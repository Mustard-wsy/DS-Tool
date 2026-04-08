import inspect

from .scheduler import scheduler


def trigger(lineno=None, observed_vars=None, pointer_watchers=None, tag=None):
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    try:
        scheduler.request_update(
            caller_frame=caller,
            lineno=lineno,
            observed_vars=observed_vars,
            pointer_watchers=pointer_watchers,
            tag=tag,
        )
    finally:
        del frame
        if caller:
            del caller
