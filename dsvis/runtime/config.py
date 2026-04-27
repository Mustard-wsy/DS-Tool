import os

_MODE = os.environ.get("DSVIS_MODE", "coarse").strip().lower()
if _MODE not in {"coarse", "fine"}:
    _MODE = "coarse"

_WATCH_STACK = []
_GLOBAL_WATCH_VARS = set()
_LAYOUT = os.environ.get("DSVIS_LAYOUT", "default")


def set_mode(mode: str | None = None):
    global _MODE
    if mode is None:
        _MODE = "fine"
        return
    normalized = (mode or "").strip().lower()
    if normalized not in {"coarse", "fine"}:
        raise ValueError("mode must be 'coarse' or 'fine'")
    _MODE = normalized


def get_mode() -> str:
    return _MODE


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
