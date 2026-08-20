"""Field binding for DSVis step-by-step animation groups.

Users call ``bind_fields(obj, keys=("A", 3), children=("A", 1))`` to
declare that certain container fields should be animated together.

This module is a compatibility layer consumed exclusively by
``graph_builder._resolve_object_fields()``.
"""

import weakref

# ---------------------------------------------------------------------------
# Global registry (weak-keyed — objects can be garbage collected)
# ---------------------------------------------------------------------------

_OBJECT_FIELD_BINDINGS = weakref.WeakKeyDictionary()


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_bind_token(token):
    """Parse ``keys@A:3`` → (field, group, ratio) or None."""
    if not isinstance(token, str):
        return None
    text = token.strip()
    if "@" not in text:
        return None
    left, right = text.split("@", 1)
    field = left.strip()
    if not field or not right.strip():
        return None
    if ":" in right:
        group, ratio_text = right.split(":", 1)
        group = group.strip() or "default"
        try:
            ratio = int(ratio_text.strip())
        except Exception:
            return None
    else:
        group = right.strip() or "default"
        ratio = 1
    if ratio <= 0:
        return None
    return field, group, ratio


def _parse_inline_bind_spec(spec):
    """Parse ``A:3`` or ``@A:3`` → (group, ratio) or None."""
    if not isinstance(spec, str):
        return None
    text = spec.strip()
    if not text:
        return None
    if text.startswith("@"):
        text = text[1:].strip()
    if not text:
        return None
    if ":" in text:
        group, ratio_text = text.split(":", 1)
        group = group.strip() or "default"
        try:
            ratio = int(ratio_text.strip())
        except Exception:
            return None
    else:
        group = text
        ratio = 1
    if ratio <= 0:
        return None
    return group, ratio


# ---------------------------------------------------------------------------
# Internal registration
# ---------------------------------------------------------------------------

def _bind_field_internal(obj, field, group, ratio=1):
    if obj is None:
        return
    field_name = str(field).strip()
    group_name = str(group).strip()
    try:
        r = int(ratio)
    except Exception:
        raise ValueError("ratio 必须是正整数")
    if not field_name or not group_name or r <= 0:
        raise ValueError("字段绑定参数无效")
    mapping = _OBJECT_FIELD_BINDINGS.setdefault(obj, {})
    mapping[field_name] = (group_name, r)


# ---------------------------------------------------------------------------
# Public API — bind_fields
# ---------------------------------------------------------------------------

def bind_fields(obj, **field_specs):
    """Batch bind container fields to animation groups.

    Usage::

        dsvis.bind_fields(self, keys=("A", 3), children=("A", 1))
        dsvis.bind_fields(self, keys="A:3", vals="B:2")
    """
    for field, spec in field_specs.items():
        if isinstance(spec, tuple) and len(spec) == 2:
            _bind_field_internal(obj, field, spec[0], spec[1])
            continue
        if isinstance(spec, str):
            parsed = _parse_inline_bind_spec(spec)
            if not parsed:
                raise ValueError(f"字段 {field} 的绑定规格无效")
            _bind_field_internal(obj, field, parsed[0], parsed[1])
            continue
        raise ValueError(f"字段 {field} 的绑定规格无效，需为 ('A', 3) 或 'A:3'")


# ---------------------------------------------------------------------------
# Query helpers (used by graph_builder)
# ---------------------------------------------------------------------------

def get_instance_bound_specs(obj):
    """Return {group: {field: ratio}} for bind_fields() calls on *obj*."""
    raw = _OBJECT_FIELD_BINDINGS.get(obj, {})
    out: dict[str, dict[str, int]] = {}
    for field, pair in raw.items():
        if not isinstance(pair, tuple) or len(pair) != 2:
            continue
        group, ratio = pair
        try:
            r = int(ratio)
        except Exception:
            continue
        if r <= 0:
            continue
        out.setdefault(str(group), {})[str(field)] = r
    return out


def get_bound_specs(obj):
    """Return {group: {field: ratio}} from class-level __dsvis_bindings__.

    Supports two declaration formats:
    1) ``__dsvis_bindings__ = ["keys@A:3", "children@A:1"]``
    2) ``__dsvis_bindings__ = {"A": {"keys": 3, "children": 1}}``
    """
    raw = getattr(obj, "__dsvis_bindings__", None)
    groups: dict[str, dict[str, int]] = {}

    if isinstance(raw, (list, tuple)):
        for token in raw:
            parsed = _parse_bind_token(token)
            if not parsed:
                continue
            field, group, ratio = parsed
            groups.setdefault(group, {})[field] = ratio
        return groups

    if isinstance(raw, dict):
        for group_name, mapping in raw.items():
            if not isinstance(mapping, dict):
                continue
            clean: dict[str, int] = {}
            for field, ratio in mapping.items():
                try:
                    r = int(ratio)
                except Exception:
                    continue
                if r > 0:
                    clean[str(field)] = r
            if clean:
                groups[str(group_name)] = clean
    return groups
