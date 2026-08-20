import os

# ---------------------------------------------------------------------------
# Mode — capture granularity
# ---------------------------------------------------------------------------

_MODE = os.environ.get("DSVIS_MODE", "coarse").strip().lower()
if _MODE not in {"coarse", "fine", "line"}:
    _MODE = "coarse"


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


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

_LAYOUT = os.environ.get("DSVIS_LAYOUT", "default")


def set_layout(layout):
    global _LAYOUT
    _LAYOUT = layout


def get_layout():
    return _LAYOUT


# ---------------------------------------------------------------------------
# Text flow
# ---------------------------------------------------------------------------

_TEXT_FLOW = os.environ.get("DSVIS_TEXT_FLOW", "vertical").strip().lower()
if _TEXT_FLOW not in {"horizontal", "vertical"}:
    _TEXT_FLOW = "vertical"
if _TEXT_FLOW == "horizontal":
    _TEXT_FLOW = "vertical"  # horizontal text flow no longer supported


def get_text_flow() -> str:
    return _TEXT_FLOW


def set_text_flow(flow: str):
    global _TEXT_FLOW
    normalized = (flow or "").strip().lower()
    if normalized not in {"horizontal", "vertical"}:
        raise ValueError("text_flow must be 'horizontal' or 'vertical'")
    # Horizontal text flow is no longer supported — silently use vertical.
    _TEXT_FLOW = "vertical"


# ---------------------------------------------------------------------------
# Breakpoints — frontend step-navigation toggle
# ---------------------------------------------------------------------------
# When ON, the scheduler records every trigger so the replay UI can
# stop on any source line.  Visibility metadata is still driven by
# the capture mode (coarse / fine / line).
# When OFF, the scheduler only records graph-changing steps.

_BREAKPOINTS_ENABLED = True


def enable_breakpoints():
    global _BREAKPOINTS_ENABLED
    _BREAKPOINTS_ENABLED = True


def disable_breakpoints():
    global _BREAKPOINTS_ENABLED
    _BREAKPOINTS_ENABLED = False


def breakpoints_enabled() -> bool:
    return _BREAKPOINTS_ENABLED


# ---------------------------------------------------------------------------
# Watch variables — global set + context stack
# ---------------------------------------------------------------------------

_WATCH_STACK: list[tuple[set[str], list]] = []
_GLOBAL_WATCH_VARS: set[str] = set()


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


# ---------------------------------------------------------------------------
# Field visibility — initial visibility state for generated HTML
# ---------------------------------------------------------------------------
# Key format: "ClassName.fieldName", value: "visible" | "self" | "cascade"
_FIELD_VISIBILITY: dict[str, str] = {}


def set_field_visible(field_key: str, state: str):
    """Set initial visibility for a field in generated HTML.

    field_key: "ClassName.fieldName" (e.g. "AVLNode.left")
    state: "visible" | "self" | "cascade"
    """
    if state not in {"visible", "self", "cascade"}:
        raise ValueError("state must be 'visible', 'self', or 'cascade'")
    _FIELD_VISIBILITY[field_key] = state


def get_field_visibility() -> dict[str, str]:
    return dict(_FIELD_VISIBILITY)
