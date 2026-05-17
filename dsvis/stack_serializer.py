"""Stack frame serialization for the DSVis debugger.

Converts Python call-stack frames into the JSON structure consumed by the
frontend stack panel.
"""

from pathlib import Path

from .introspection import (
    is_primitive,
    short,
    stack_display_text,
    stack_tree_item_text,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_internal_frame(frame):
    """True when *frame* belongs to the dsvis package itself."""
    try:
        Path(frame.f_code.co_filename).resolve().relative_to(_PACKAGE_ROOT)
        return True
    except Exception:
        return False


def _frame_parameter_names(frame):
    """Return the ordered parameter names of *frame*."""
    code = frame.f_code
    names = []
    idx = 0
    idx_end = code.co_argcount + code.co_posonlyargcount + code.co_kwonlyargcount
    while idx < idx_end and idx < len(code.co_varnames):
        names.append(code.co_varnames[idx])
        idx += 1
    if code.co_flags & 4 and idx < len(code.co_varnames):   # CO_VARARGS
        names.append(code.co_varnames[idx])
        idx += 1
    if code.co_flags & 8 and idx < len(code.co_varnames):   # CO_VARKEYWORDS
        names.append(code.co_varnames[idx])
    return names


def _strip_name_prefix(name, text):
    """Remove ``name = `` prefix from *text* if present."""
    prefix = f"{name} = "
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def _serialize_stack_tree(value, depth=0, max_depth=2, max_items=120):
    """Return a recursive tree node dict for *value*, or None."""
    if depth >= max_depth:
        return None

    if isinstance(value, dict):
        items = list(value.items())
        children = []
        for i, (k, v) in enumerate(items):
            if i >= max_items:
                break
            children.append({
                "name": f"[{short(k, 40)}]",
                "text": stack_tree_item_text(v),
                "tree": _serialize_stack_tree(v, depth + 1, max_depth, max_items),
            })
        return {
            "text": f"{{dict}} len={len(items)}",
            "children": children,
            "truncated": len(items) > max_items,
        }

    if isinstance(value, (list, tuple)):
        from collections import deque as _deque
        containers = (list, tuple, _deque)
    else:
        containers = ()
    if isinstance(value, containers):
        items = list(value)
        children = []
        for i, item in enumerate(items):
            if i >= max_items:
                break
            children.append({
                "name": f"[{i}]",
                "text": stack_tree_item_text(item),
                "tree": _serialize_stack_tree(item, depth + 1, max_depth, max_items),
            })
        return {
            "text": f"{{{type(value).__name__}}} len={len(items)}",
            "children": children,
            "truncated": len(items) > max_items,
        }

    if isinstance(value, (set, frozenset)):
        items = list(sorted(value, key=lambda x: short(x, 60)))
        children = []
        for i, item in enumerate(items):
            if i >= max_items:
                break
            children.append({
                "name": f"[{i}]",
                "text": stack_tree_item_text(item),
                "tree": _serialize_stack_tree(item, depth + 1, max_depth, max_items),
            })
        return {
            "text": f"{{{type(value).__name__}}} len={len(items)}",
            "children": children,
            "truncated": len(items) > max_items,
        }

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def serialize_scope_rows(scope_dict, include_private=False, preferred_order=None):
    """Return a list of stack row dicts for a single scope (locals/globals)."""
    rows = []
    seen = set()
    preferred_set = set(str(name) for name in (preferred_order or []))
    ordered_keys: list[str] = []
    if preferred_order:
        ordered_keys.extend(str(name) for name in preferred_order)
    ordered_keys.extend(str(name) for name in scope_dict.keys())

    for name in ordered_keys:
        if name in seen or name not in scope_dict:
            continue
        seen.add(name)
        if not include_private and name.startswith("_"):
            continue
        value = scope_dict.get(name)
        value_short, hidden_reason = stack_display_text(value)
        full_text = f"{name} = {value_short}"
        raw_text = f"{name} = {short(value)}"
        row: dict = {
            "name": name,
            "kind": "param" if name in preferred_set else "field",
            "text": full_text,
        }

        if hidden_reason:
            row["hidden_reason"] = hidden_reason
            row["compact_text"] = full_text
            row["full_text"] = raw_text
        elif is_primitive(value):
            row["full_text"] = raw_text

        tree = _serialize_stack_tree(value)
        if tree and tree.get("children"):
            row["tree"] = tree
            row["tree_default_limit"] = 5
            row["full_text"] = _strip_name_prefix(name, full_text)

        rows.append(row)
    return rows


def serialize_runtime_stack(caller_frame, include_private=False):
    """Build stack payload for the given *caller_frame*."""
    import inspect as _inspect

    frames = []
    current = caller_frame
    while current:
        if not _is_internal_frame(current):
            frames.append(current)
        current = current.f_back

    if not frames:
        return {"globals": [], "frames": []}

    globals_source = frames[-1].f_globals
    stack_frames = []
    for frame in reversed(frames):
        is_module = frame.f_code.co_name == "<module>"
        params = None if is_module else _frame_parameter_names(frame)
        stack_frames.append({
            "name": "(main)" if is_module else frame.f_code.co_name,
            "lineno": frame.f_lineno,
            "filename": Path(frame.f_code.co_filename).name,
            "locals": serialize_scope_rows(
                frame.f_locals,
                include_private=include_private,
                preferred_order=params,
            ),
            "kind": "module" if is_module else "function",
        })

    return {
        "globals": serialize_scope_rows(globals_source, include_private=include_private),
        "frames": stack_frames,
    }
