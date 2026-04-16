import json
import atexit
from pathlib import Path
import inspect
from .config import get_mode, get_pointer_watchers, get_watch_vars


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
        if not file_path:
            return
        p = Path(file_path)
        if not p.exists():
            return
        self.source_file = str(p)
        self.source_lines = p.read_text(encoding="utf-8").splitlines()

    def _is_user_frame(self, frame):
        if frame is None:
            return False
        if not self.source_file:
            return True
        try:
            return str(Path(frame.f_code.co_filename).resolve()) == str(Path(self.source_file).resolve())
        except Exception:
            return False

    @staticmethod
    def _is_internal_binding(name, value):
        key = str(name)
        if key in {"trigger", "dsvis"}:
            return True
        if key.startswith("__"):
            return True
        if inspect.ismodule(value):
            mod_name = getattr(value, "__name__", "")
            if mod_name == "dsvis" or mod_name.startswith("dsvis."):
                return True
        if inspect.isfunction(value) or inspect.ismethod(value):
            mod_name = getattr(value, "__module__", "")
            if mod_name == "dsvis" or mod_name.startswith("dsvis."):
                return True
        return False

    def request_update(self, caller_frame=None, lineno=None, observed_vars=None, pointer_watchers=None, max_nodes=None, include_private=None):
        if caller_frame is None:
            return

        # 延迟导入以避免循环导入
        from .. import dsvis

        self._ensure_source_loaded(caller_frame)
        root_scope = {
            "__locals__": dict(caller_frame.f_locals),
            "__globals__": dict(caller_frame.f_globals),
        }
        stack_frames = []
        walk = caller_frame
        depth = 0
        while walk and depth < 64:
            if not self._is_user_frame(walk):
                walk = walk.f_back
                depth += 1
                continue
            local_snapshot = dict(walk.f_locals)
            code = walk.f_code
            arg_count = int(getattr(code, "co_argcount", 0) or 0)
            kw_only_count = int(getattr(code, "co_kwonlyargcount", 0) or 0)
            pos_only_count = int(getattr(code, "co_posonlyargcount", 0) or 0)
            arg_names = list(code.co_varnames[: arg_count + kw_only_count + pos_only_count])
            clean_locals = {
                k: v for k, v in local_snapshot.items()
                if not self._is_internal_binding(k, v)
            }
            stack_frames.append(
                {
                    "function": code.co_name,
                    "lineno": walk.f_lineno,
                    "locals": clean_locals,
                    "params": arg_names,
                }
            )
            walk = walk.f_back
            depth += 1
        stack_frames.reverse()

        globals_snapshot = {
            k: v for k, v in dict(caller_frame.f_globals).items()
            if not self._is_internal_binding(k, v)
        }
        mode = get_mode()
        merged_focus = set(get_watch_vars()) | set(observed_vars or [])
        merged_pointers = list(get_pointer_watchers()) + list(pointer_watchers or [])
        
        # 使用提供的参数，或者使用 scheduler 的默认值
        effective_max_nodes = max_nodes if max_nodes is not None else self.max_nodes
        effective_include_private = include_private if include_private is not None else self.include_private
        
        nodes, edges = dsvis._walk(
            root_scope,
            max_nodes=effective_max_nodes,
            include_private=effective_include_private,
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
                "scope": {
                    "globals": globals_snapshot,
                    "frames": stack_frames,
                },
            }
        )

    def flush(self):
        if not self.steps:
            return
        
        try:
            # 延迟导入以避免循环导入
            from .. import dsvis
            
            # 生成默认标题
            title = f"DSVis Debugger ({Path(self.source_file).name if self.source_file else 'script'})"
            
            # 调用渲染函数
            dsvis._render_debugger(
                self.steps,
                self.source_lines,
                title=title,
            )
        except Exception as e:
            print(f"[dsvis] Scheduler flush 出错：{e}")
        finally:
            # 清空状态，为下一轮做准备
            self.steps = []
            self.last_signature = None
            self.source_lines = []
            self.source_file = None
            self.effective_layout = None


scheduler = Scheduler()
