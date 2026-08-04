import json
import atexit
from pathlib import Path
from .config import get_layout, get_mode, get_pointer_watchers, get_watch_vars, breakpoints_enabled
from ..stack_serializer import serialize_runtime_stack
from ..graph_builder import walk_graph
from ..introspection import is_graph_root_value
from ..card_renderer import render_debugger


class Scheduler:
    def __init__(self):
        self.last_signature = None
        self.steps = []
        self.source_lines = []
        self.source_file = None
        self.max_nodes = 300  # 默认值，可被 capture 覆盖
        self.include_private = False  # 默认值，可被 capture 覆盖
        self.effective_layout = None  # 由 capture 设置
        atexit.register(self.flush)

    @staticmethod
    def _make_signature(nodes, edges):
        normalized_nodes = sorted(
            [
                {
                    "id": str(n.get("id")),
                    "label": n.get("label"),
                    "class_name": n.get("class_name"),
                    "is_class_object": n.get("is_class_object"),
                    "rows": [row.get("text", "") for row in n.get("rows", [])],
                    "refs": [ref.get("name", "") for ref in n.get("refs", [])],
                }
                for n in nodes
            ],
            key=lambda x: (x["id"], x["label"] or ""),
        )
        normalized_edges = sorted(
            [
                {
                    "src": str(e.get("src")),
                    "dst": str(e.get("dst")),
                    "label": e.get("label", ""),
                }
                for e in edges
            ],
            key=lambda x: (x["src"], x["dst"], x["label"]),
        )
        payload = {
            "nodes": normalized_nodes,
            "edges": normalized_edges,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _ensure_source_loaded(self, caller_frame):
        if self.source_lines:
            return
        file_path = caller_frame.f_globals.get("__file__")
        # Fallback: try sys.argv[0] when __file__ is not available
        # (e.g. interactive sessions or capture()-only mode)
        if not file_path:
            import sys
            if sys.argv and sys.argv[0]:
                file_path = sys.argv[0]
        if not file_path:
            return
        p = Path(file_path)
        if not p.exists():
            return
        self.source_file = str(p)
        self.source_lines = p.read_text(encoding="utf-8").splitlines()

    def request_update(self, caller_frame=None, lineno=None, observed_vars=None, pointer_watchers=None, max_nodes=None, include_private=None, include_containers=None, _source="mode"):
        if caller_frame is None:
            return

        self._ensure_source_loaded(caller_frame)
        mode = get_mode()
        merged_focus = set(get_watch_vars()) | set(observed_vars or [])
        merged_pointers = list(get_pointer_watchers()) + list(pointer_watchers or [])
        
        # 使用提供的参数，或者使用 scheduler 的默认值
        effective_max_nodes = max_nodes if max_nodes is not None else self.max_nodes
        effective_include_private = include_private if include_private is not None else self.include_private
        effective_include_containers = include_containers if include_containers is not None else (mode == "fine")

        stack_data = serialize_runtime_stack(
            caller_frame,
            include_private=effective_include_private,
        )

        pointer_related_names = set()
        for pointer_name, container_name in merged_pointers:
            if pointer_name:
                pointer_related_names.add(pointer_name)
            if container_name:
                pointer_related_names.add(container_name)

        def _keep_graph_root(name, value):
            # Focus/pointer vars should stay visible even in coarse mode.
            if name in merged_focus or name in pointer_related_names:
                return True
            return is_graph_root_value(value, include_containers=effective_include_containers)

        root_scope = {
            "__locals__": {k: v for k, v in caller_frame.f_locals.items() if _keep_graph_root(k, v)},
            "__globals__": {k: v for k, v in caller_frame.f_globals.items() if _keep_graph_root(k, v)},
        }
        
        nodes, edges = walk_graph(
            root_scope,
            max_nodes=effective_max_nodes,
            include_private=effective_include_private,
            include_containers=effective_include_containers,
            focus_vars=merged_focus,
            pointer_watchers=merged_pointers,
        )
        signature = self._make_signature(nodes, edges)
        has_changed = signature != self.last_signature

        # ---------------------------------------------------------------
        # Single decision point: breakpoint semantics
        # ---------------------------------------------------------------
        # ON  → record every trigger so the frontend can navigate
        #        line by line.  _visible is set per the capture mode.
        # OFF → record only when the object graph actually changes;
        #        every recorded step is visible.
        # ---------------------------------------------------------------
        use_breakpoints = breakpoints_enabled()

        if use_breakpoints:
            # --- breakpoint-aware recording ---
            if has_changed:
                self.last_signature = signature
                self.last_nodes = nodes
                self.last_edges = edges
            else:
                nodes = self.last_nodes if hasattr(self, "last_nodes") else nodes
                edges = self.last_edges if hasattr(self, "last_edges") else edges

            # Visible only when:
            # - mode is "line" (show everything), or
            # - this is a mode trigger (not line-only) with a real graph change
            #   that differs from the last visible state
            changed_from_last_visible = (
                not hasattr(self, "last_visible_signature")
                or signature != self.last_visible_signature
            )
            is_line_mode = (get_mode() == "line")
            is_mode_trigger = (_source == "mode")
            if is_line_mode:
                visible = True
            elif is_mode_trigger and has_changed and changed_from_last_visible:
                visible = True
            else:
                visible = False

            if visible and not hasattr(self, "last_visible_signature"):
                self.last_visible_signature = signature
                self.last_visible_nodes = nodes
                self.last_visible_edges = edges
            elif visible and has_changed:
                self.last_visible_signature = signature
                self.last_visible_nodes = nodes
                self.last_visible_edges = edges

            self.steps.append(
                {
                    "lineno": lineno or caller_frame.f_lineno,
                    "nodes": nodes,
                    "edges": edges,
                    "stack": stack_data,
                    "_visible": visible,
                }
            )
            return

        # --- mode-driven recording (breakpoints OFF) ---
        if not has_changed:
            return

        self.last_signature = signature
        self.steps.append(
            {
                "lineno": lineno or caller_frame.f_lineno,
                "nodes": nodes,
                "edges": edges,
                "stack": stack_data,
                "_visible": True,
            }
        )

    def flush(self):
        """Flush recorded steps to a self-contained HTML replay page.

        display_indices is the single source of truth for which steps
        are visible in the frontend.  The renderer receives the full
        *self.steps* list so that raw-step navigation (breakpoints,
        step-into) still works.
        """
        if not self.steps:
            return
        
        try:
            title = f"DSVis Debugger ({Path(self.source_file).name if self.source_file else 'script'})"

            # Build display index map — which steps are visible in the UI
            display_indices = [i for i, s in enumerate(self.steps) if s.get("_visible", True)]

            render_debugger(
                self.steps,
                self.source_lines,
                title=title,
                layout=get_layout(),
                display_indices=display_indices,
            )
        except Exception as e:
            print(f"[dsvis] Scheduler flush 出错：{e}")
        finally:
            # 清空状态，为下一轮做准备
            self.steps = []
            self.last_signature = None
            self.last_visible_signature = None
            self.source_lines = []
            self.source_file = None
            self.effective_layout = None


scheduler = Scheduler()
