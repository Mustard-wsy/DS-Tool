import os

_MODE = os.environ.get("DSVIS_MODE", "coarse").strip().lower()
if _MODE not in {"coarse", "fine"}:
    _MODE = "coarse"

_WATCH_STACK = []


def set_mode(mode: str):
    global _MODE
    normalized = (mode or "").strip().lower()
    if normalized not in {"coarse", "fine"}:
        raise ValueError("mode must be 'coarse' or 'fine'")
    _MODE = normalized


def get_mode() -> str:
    return _MODE


def push_watch_context(var_names, pointers):
    _WATCH_STACK.append((set(var_names or []), list(pointers or [])))


def pop_watch_context():
    if _WATCH_STACK:
        _WATCH_STACK.pop()


def get_watch_vars():
    merged = set()
    for names, _ in _WATCH_STACK:
        merged |= set(names)
    return merged


def get_pointer_watchers():
    merged = []
    for _, pointers in _WATCH_STACK:
        merged.extend(pointers)
    return merged
