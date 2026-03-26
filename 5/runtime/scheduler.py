import dsvis
import json


class Scheduler:
    def __init__(self, step_mode=True):
        self.step_mode = step_mode
        self.step = 0
        self.last_signature = None

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

    def request_update(self, caller_frame=None):
        if caller_frame is None:
            return

        root_scope = {
            "__locals__": dict(caller_frame.f_locals),
            "__globals__": dict(caller_frame.f_globals),
        }
        nodes, edges = dsvis._walk(root_scope)
        signature = self._make_signature(nodes, edges)
        if signature == self.last_signature:
            return

        self.step += 1
        self.last_signature = signature
        dsvis._render_g6(nodes, edges, title=f"Step {self.step}")

        if self.step_mode:
            try:
                input(f"[dsvis] Step {self.step} 完成，按 Enter 继续...")
            except EOFError:
                # 非交互环境（如 CI）下无法输入时自动继续
                pass


scheduler = Scheduler()
