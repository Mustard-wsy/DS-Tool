import os

_MODE = os.environ.get("DSVIS_MODE", "line").strip().lower()
if _MODE not in {"coarse", "fine", "line"}:
    _MODE = "line"

_WATCH_STACK = []
_GLOBAL_WATCH_VARS = set()
_LAYOUT = os.environ.get("DSVIS_LAYOUT", "default")

# Breakpoints toggle — when ON, the scheduler/injector use line-mode
# collection regardless of _MODE.  When OFF, collection follows _MODE.
_BREAKPOINTS_ENABLED = True


def set_mode(mode: str | None = None):
    global _MODE
    if mode is None:
        _MODE = "fine"
        return
    normalized = (mode or "").strip().lower()
    if normalized not in {"coarse", "fine", "line"}:
        raise ValueError("mode must be 'coarse', 'fine' or 'line'")
    _MODE = normalized


def get_mode() -> str:
    return _MODE


def enable_breakpoints():
    global _BREAKPOINTS_ENABLED
    _BREAKPOINTS_ENABLED = True


def disable_breakpoints():
    global _BREAKPOINTS_ENABLED
    _BREAKPOINTS_ENABLED = False


def breakpoints_enabled() -> bool:
    return _BREAKPOINTS_ENABLED


def set_layout(layout):
    global _LAYOUT
    _LAYOUT = layout


def get_layout():
    return _LAYOUT


def push_watch_context(var_names, pointers):
    _WATCH_STACK.append((set(var_names or []), list(pointers or [])))


def pop_watch_context():
    if _WATCH_STACK:
        _WATCH_STACK.pop()


def get_watch_vars():
    merged = set(_GLOBAL_WATCH_VARS)
    for names, _ in _WATCH_STACK:
        merged |= set(names)
    return merged


def add_global_watch_vars(var_names):
    for name in var_names or []:
        text = str(name).strip()
        if text:
            _GLOBAL_WATCH_VARS.add(text)


def remove_global_watch_vars(var_names):
    for name in var_names or []:
        text = str(name).strip()
        if text:
            _GLOBAL_WATCH_VARS.discard(text)


def clear_global_watch_vars():
    _GLOBAL_WATCH_VARS.clear()


def get_pointer_watchers():
    merged = []
    for _, pointers in _WATCH_STACK:
        merged.extend(pointers)
    return merged
