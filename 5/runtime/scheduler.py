import dsvis


class Scheduler:
    def __init__(self, step_mode=True):
        self.step_mode = step_mode
        self.step = 0

    def request_update(self, caller_frame=None):
        if caller_frame is None:
            return

        self.step += 1
        root_scope = {
            "__locals__": dict(caller_frame.f_locals),
            "__globals__": dict(caller_frame.f_globals),
        }
        nodes, edges = dsvis._walk(root_scope)
        dsvis._render_g6(nodes, edges, title=f"Step {self.step}")

        if self.step_mode:
            try:
                input(f"[dsvis] Step {self.step} 完成，按 Enter 继续...")
            except EOFError:
                # 非交互环境（如 CI）下无法输入时自动继续
                pass


scheduler = Scheduler()