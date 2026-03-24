import threading

from dsvis import capture


class Scheduler:
    def __init__(self, delay=0.1):
        self.delay = delay
        self.pending = False

    def request_update(self):
        if not self.pending:
            self.pending = True
            threading.Timer(self.delay, self.flush).start()

    def flush(self):
        self.pending = False
        capture()


scheduler = Scheduler()
