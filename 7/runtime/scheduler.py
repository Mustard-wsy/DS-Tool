import dsvis
import json
import atexit
from pathlib import Path
from .config import get_mode, get_pointer_watchers, get_watch_vars


class Scheduler:
    def __init__(self):
        self.last_signature = None
        self.steps = []
        self.source_lines = []
        self.source_file = None
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
        if not file_path:
            return
        p = Path(file_path)
        if not p.exists():
            return
        self.source_file = str(p)
        self.source_lines = p.read_text(encoding="utf-8").splitlines()

    def request_update(self, caller_frame=None, lineno=None, observed_vars=None, pointer_watchers=None, tag=None):
        if caller_frame is None:
            return

        self._ensure_source_loaded(caller_frame)
        root_scope = {
            "__locals__": dict(caller_frame.f_locals),
            "__globals__": dict(caller_frame.f_globals),
        }
        mode = get_mode()
        merged_focus = set(get_watch_vars()) | set(observed_vars or [])
        merged_pointers = list(get_pointer_watchers()) + list(pointer_watchers or [])
        nodes, edges = dsvis._walk(
            root_scope,
            include_containers=(mode == "fine"),
            focus_vars=merged_focus,
            pointer_watchers=merged_pointers,
        )
        signature = self._make_signature(nodes, edges)
        if signature == self.last_signature:
            return

        self.last_signature = signature
        self.steps.append(
            {
                "lineno": lineno or caller_frame.f_lineno,
                "nodes": nodes,
                "edges": edges,
                "tag": tag,
            }
        )

    def flush(self):
        if not self.steps:
            return
        dsvis._render_debugger(
            self.steps,
            self.source_lines,
            title=f"DSVis Debugger ({Path(self.source_file).name if self.source_file else 'script'})",
        )
        self.steps = []


scheduler = Scheduler()
