from dsvis import capture


class Scheduler:
    def __init__(self, step_mode=True):
        self.step_mode = step_mode
        self.step = 0

    def request_update(self, caller_frame=None):
        self.step += 1
        capture(title=f"Step {self.step}", _caller_frame=caller_frame)

        if self.step_mode:
            try:
                input(f"[dsvis] Step {self.step} 完成，按 Enter 继续...")
            except EOFError:
                # 非交互环境（如 CI）下无法输入时自动继续
                pass


scheduler = Scheduler()
