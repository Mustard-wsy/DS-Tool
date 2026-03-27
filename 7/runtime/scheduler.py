import dsvis
import json
import atexit
from pathlib import Path


class Scheduler:
    def __init__(self):
        self.last_signature = None
        self.steps = []
        self.source_lines = []
        self.source_file = None
        atexit.register(self.flush)

    @staticmethod
    def _make_signature(nodes, edges):
        normalized_nodes = []
        for n in nodes:
            normalized_nodes.append(
                {
                    "class_name": n.get("class_name"),
                    "is_class_object": n.get("is_class_object"),
                    "rows": sorted((row.get("text", "") for row in n.get("rows", []))),
                    "refs": sorted((ref.get("name", "") for ref in n.get("refs", []))),
                }
            )
        normalized_edges = sorted((e.get("label", "") for e in edges))
        payload = {
            "nodes": sorted(
                normalized_nodes,
                key=lambda x: (
                    x["class_name"] or "",
                    str(x["is_class_object"]),
                    "|".join(x["rows"]),
                    "|".join(x["refs"]),
                ),
            ),
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

    def request_update(self, caller_frame=None, lineno=None):
        if caller_frame is None:
            return

        self._ensure_source_loaded(caller_frame)
        root_scope = {
            "__locals__": dict(caller_frame.f_locals),
            "__globals__": dict(caller_frame.f_globals),
        }
        nodes, edges = dsvis._walk(root_scope)
        signature = self._make_signature(nodes, edges)
        if signature == self.last_signature:
            return

        self.last_signature = signature
        self.steps.append(
            {
                "lineno": lineno or caller_frame.f_lineno,
                "nodes": nodes,
                "edges": edges,
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
