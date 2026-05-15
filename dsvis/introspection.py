"""Object introspection and type predicates.

Pure helpers used by the graph builder, stack serializer, and card renderer.
"""

import inspect
import re
from collections import deque
from pathlib import Path
from typing import Any


def typename(obj):
    """Human-readable type name, stripping __main__ and builtins prefixes."""
    try:
        t = type(obj)
        mod = getattr(t, "__module__", "")
        name = getattr(t, "__qualname__", getattr(t, "__name__", str(t)))
        if mod in ("__main__", "main"):
            return name
        if mod and mod != "builtins":
            return f"{mod}.{name}"
        return name
    except Exception:
        return "unknown"


def short(obj, max_len=80):
    """Safe repr truncated to *max_len* characters."""
    try:
        s = repr(obj)
    except Exception:
        s = f"<unreprable {typename(obj)}>"
    s = s.replace("\n", "\\n")
    if len(s) > max_len:
        s = s[: max_len - 1] + "\u2026"
    return s


def stack_display_text(value):
    """Return (text, reason) for the stack panel row text.

    *reason* is non-None when the value is hidden (module, routine, class,
    or an opaque address string).
    """
    if inspect.ismodule(value):
        return "<module hidden>", "module"

    if inspect.isroutine(value):
        kind = type(value).__name__ or "callable"
        name = getattr(value, "__qualname__", getattr(value, "__name__", ""))
        if name:
            return f"<{kind} {name}>", "callable"
        return f"<{kind}>", "callable"

    if inspect.isclass(value):
        name = getattr(value, "__qualname__", getattr(value, "__name__", typename(value)))
        return f"<class {name}>", "class"

    value_short = short(value)
    if re.match(r"^<.*\sobject\sat\s0x[0-9A-Fa-f]+>$", value_short):
        return f"<{type(value).__name__} instance>", "address"

    return value_short, None


def stack_tree_item_text(value):
    """One-line summary for a tree node in the stack panel."""
    if is_primitive(value):
        return f"{{{typename(value)}}} {short(value, 120)}"

    if isinstance(value, dict):
        return f"{{dict}} len={len(value)}"

    if isinstance(value, (list, tuple, deque, set, frozenset)):
        return f"{{{type(value).__name__}}} len={len(value)}"

    text, _ = stack_display_text(value)
    return f"{{{typename(value)}}} {text}"


def is_primitive(obj):
    return isinstance(obj, (int, float, str, bool, bytes, complex, type(None)))


def is_class_object(obj):
    """True for user-defined objects (has __dict__ or __slots__)."""
    if obj is None or is_primitive(obj):
        return False
    if inspect.ismodule(obj) or inspect.isroutine(obj) or inspect.isclass(obj):
        return False
    if isinstance(obj, (list, tuple, set, frozenset, dict, deque)):
        return False
    t = type(obj)
    if t.__module__ == "builtins":
        return False
    return hasattr(obj, "__dict__") or hasattr(t, "__slots__")


def is_container(obj):
    return isinstance(obj, (list, tuple, set, frozenset, dict, deque))


def is_renderable(obj, include_containers=False):
    return is_class_object(obj) or is_primitive(obj) or (include_containers and is_container(obj))


def is_graph_root_value(obj, include_containers=False):
    return is_class_object(obj) or (include_containers and is_container(obj))


def format_typed_label(name, value):
    return f"{name}\n({typename(value)})"


def iter_container_items(name, container):
    """Yield (display_name, value) for every item in a container."""
    if isinstance(container, dict):
        for k, v in container.items():
            yield f"{name}[{short(k, 30)}]", v
        return

    if isinstance(container, (list, tuple, deque)):
        for i, v in enumerate(container):
            yield f"{name}[{i}]", v
        return

    if isinstance(container, (set, frozenset)):
        for i, v in enumerate(sorted(container, key=lambda x: short(x))):
            yield f"{name}[{i}]", v
        return


def iter_object_items(obj, include_private=False):
    """Yield (attr_name, value) for a user-defined object."""
    try:
        for k, v in vars(obj).items():
            if not include_private and str(k).startswith("_"):
                continue
            yield str(k), v
    except Exception:
        pass
    slots = getattr(type(obj), "__slots__", ())
    if isinstance(slots, str):
        slots = (slots,)
    for s_name in slots:
        if not include_private and str(s_name).startswith("_"):
            continue
        try:
            yield str(s_name), getattr(obj, s_name)
        except Exception:
            continue
