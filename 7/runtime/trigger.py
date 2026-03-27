import inspect

from .scheduler import scheduler


def trigger(lineno=None):
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    try:
        scheduler.request_update(caller_frame=caller, lineno=lineno)
    finally:
        del frame
        if caller:
            del caller
