import functools
import inspect
import tempfile
import webbrowser
import json
import os
import weakref
from collections import deque
from pathlib import Path

from .runtime.config import (
    get_mode,
    get_pointer_watchers,
    get_watch_vars,
    set_mode,
)
from .runtime.scheduler import scheduler

__all__ = [
    "capture",
    "auto",
    "bind_fields",
    "set_mode",
]

_DEFAULT_LAYOUT = {
    "type": "dagre",
    "rankdir": "LR",
    "nodesep": 120,
    "ranksep": 220,
}

_OBJECT_FIELD_BINDINGS = weakref.WeakKeyDictionary()

# ---------- helpers ----------

def _typename(obj):
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

def _short(obj, max_len=80):
    try:
        s = repr(obj)
    except Exception:
        s = f"<unreprable {_typename(obj)}>"
    s = s.replace("\n", "\\n")
    if len(s) > max_len:
        s = s[:max_len-1] + "…"
    return s

def _is_primitive(obj):
    return isinstance(obj, (int, float, str, bool, bytes, complex, type(None)))

def _is_class_object(obj):
    if obj is None or _is_primitive(obj):
        return False
    if inspect.ismodule(obj) or inspect.isroutine(obj) or inspect.isclass(obj):
        return False
    if isinstance(obj, (list, tuple, set, frozenset, dict, deque)):
        return False
    t = type(obj)
    if t.__module__ == "builtins":
        return False
    return hasattr(obj, "__dict__") or hasattr(t, "__slots__")

def _is_container(obj):
    return isinstance(obj, (list, tuple, set, frozenset, dict, deque))


def _is_renderable(obj, include_containers=False):
    return _is_class_object(obj) or _is_primitive(obj) or (include_containers and _is_container(obj))

def _format_typed_label(name, value):
    return f"{name}\n({_typename(value)})"

def _iter_container_items(name, container):
    """把容器拆成 (显示名, 值) 二元组，支持继续判断引用关系。"""
    if isinstance(container, dict):
        for k, v in container.items():
            yield f"{name}[{_short(k, 30)}]", v
        return

    if isinstance(container, (list, tuple, deque)):
        for i, v in enumerate(container):
            yield f"{name}[{i}]", v
        return

    if isinstance(container, (set, frozenset)):
        for i, v in enumerate(sorted(container, key=lambda x: _short(x))):
            yield f"{name}[{i}]", v
        return

def _iter_object_items(obj, include_private=False):
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
    for name in slots:
        if not include_private and str(name).startswith("_"):
            continue
        try:
            yield str(name), getattr(obj, name)
        except Exception:
            continue

def _parse_bind_token(token):
    """
    解析类似 `keys@A:3` 的声明：
    - keys: 字段名
    - A: 分组名
    - 3: 比例（每轮取 3 个）
    """
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


def _bind_field_internal(obj, field, group, ratio=1):
    """
    内部函数，用于绑定单个字段。
    """
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


def _parse_inline_bind_spec(spec):
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





def bind_fields(obj, **field_specs):
    """
    批量绑定（推荐）：
        self.keys = []
        self.children = []
        dsvis.bind_fields(self, keys=("A", 3), children=("A", 1))
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





def _get_instance_bound_specs(obj):
    raw = _OBJECT_FIELD_BINDINGS.get(obj, {})
    out = {}
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


def _get_bound_specs(obj):
    """
    支持两种定义方式：
    1) __dsvis_bindings__ = ["keys@A:3", "children@A:1", "vals@B:2", ...]
    2) __dsvis_bindings__ = {"A": {"keys": 3, "children": 1}, "B": {...}}
    """
    raw = getattr(obj, "__dsvis_bindings__", None)
    groups = {}

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
            clean = {}
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


def _normalize_layout(layout):
    if layout is None:
        return dict(_DEFAULT_LAYOUT)

    if isinstance(layout, dict):
        merged = dict(_DEFAULT_LAYOUT)
        merged.update(layout)
        layout_type = str(merged.get("type", "")).strip().lower()
        if layout_type in {"snake", "concentric", "snakelayout", "concentriclayout"}:
            raise ValueError("snake / concentric 布局已移除，仅支持 dagre 类布局参数")
        return merged

    raise ValueError("layout 参数类型无效，必须是布局字典或 None")

# ---------- 核心遍历 ----------

def _walk(
    root_scope,
    max_nodes=300,
    include_private=False,
    include_containers=False,
    focus_vars=None,
    pointer_watchers=None,
):
    visited = set()
    nodes = []
    edges = []
    node_index = {}
    q = deque()
    focus_vars = set(focus_vars or [])
    pointer_watchers = list(pointer_watchers or [])

    def _add_pointer_node(pointer_name, container_name, pointer_value, text):
        node_id = f"ptr:{pointer_name}->{container_name}:{len(nodes)}"
        n = {
            "id": node_id,
            "label": f"{pointer_name} -> {container_name}",
            "type": "Pointer",
            "rows": [{"name": "value", "kind": "field", "text": text}],
            "refs": [],
            "class_name": "Pointer",
            "is_class_object": False,
        }
        if pointer_value is not None:
            n["rows"].append({
                "name": "index",
                "kind": "field",
                "text": f"index = {_short(pointer_value)}",
            })
        nodes.append(n)

    def add_obj(obj, label, value_text=None):
        if not _is_renderable(obj, include_containers=include_containers):
            return None
        obj_id = id(obj)
        if obj_id in visited:
            return obj_id
        if len(nodes) >= max_nodes:
            return None
        visited.add(obj_id)

        n = {
            "id": obj_id,
            "label": label,
            "type": _typename(obj),
            "rows": [],
            "refs": [],
            "class_name": type(obj).__name__ if obj else "NoneType",
            "is_class_object": _is_class_object(obj),
        }
        if value_text is not None:
            n["rows"].append({
                "name": "value",
                "kind": "field",
                "text": value_text,
            })
        nodes.append(n)
        node_index[obj_id] = n
        if _is_container(obj):
            items = list(_iter_container_items("item", obj))
            n["rows"].append({
                "name": "summary",
                "kind": "field",
                "text": f"size = {len(items)}",
            })
            for item_name, item_val in items[:12]:
                if _is_primitive(item_val):
                    n["rows"].append({
                        "name": item_name,
                        "kind": "field",
                        "text": f"{item_name} = {_short(item_val)}",
                    })
                elif _is_class_object(item_val):
                    cid = add_obj(item_val, _format_typed_label(item_name, item_val))
                    if cid:
                        n["rows"].append({
                            "name": item_name,
                            "kind": "ref",
                            "text": item_name,
                        })
                        n["refs"].append({"name": item_name})
                        edges.append({"src": obj_id, "dst": cid, "label": item_name})
        q.append(obj)
        return obj_id

    # 扫描作用域
    for scope_dict in [root_scope["__locals__"], root_scope["__globals__"]]:
        for k, v in scope_dict.items():
            if not include_private and k.startswith("_"):
                continue
            label = _format_typed_label(k, v)
            value_text = f"value = {_short(v)}" if _is_primitive(v) else None
            should_force = k in focus_vars
            if should_force and _is_container(v):
                add_obj(v, label, value_text=f"value = {_short(v)}")
                continue
            if should_force and not _is_renderable(v, include_containers=include_containers):
                add_obj(_short(v), label, value_text=f"value = {_short(v)}")
                continue
            add_obj(v, label, value_text=value_text)

    merged_scope = {}
    merged_scope.update(root_scope.get("__globals__", {}))
    merged_scope.update(root_scope.get("__locals__", {}))
    for pointer_name, container_name in pointer_watchers:
        pointer_value = merged_scope.get(pointer_name)
        container_value = merged_scope.get(container_name)
        if not isinstance(pointer_value, int):
            _add_pointer_node(pointer_name, container_name, pointer_value, "status = non_int_index")
            continue
        if not _is_container(container_value):
            _add_pointer_node(pointer_name, container_name, pointer_value, "status = missing_container")
            continue
        try:
            pointed = container_value[pointer_value]
            _add_pointer_node(
                pointer_name,
                container_name,
                pointer_value,
                f"value = {_short(pointed)}",
            )
        except Exception:
            _add_pointer_node(pointer_name, container_name, pointer_value, "status = out_of_range_or_invalid")

    # BFS
    while q:
        obj = q.popleft()
        obj_id = id(obj)
        owner = node_index.get(obj_id)

        if owner is None or not owner.get("is_class_object"):
            continue

        object_items = list(_iter_object_items(obj, include_private))
        item_map = dict(object_items)
        bind_groups = _get_bound_specs(obj)
        instance_specs = _get_instance_bound_specs(obj)
        for group_name, mapping in instance_specs.items():
            bind_groups.setdefault(group_name, {}).update(mapping)
        bound_fields = set()
        for mapping in bind_groups.values():
            bound_fields.update(mapping.keys())

        def _append_container_item(item_name, item_val, bind_group=None, bind_block=None):
            if _is_primitive(item_val):
                owner["rows"].append({
                    "name": item_name,
                    "kind": "field",
                    "text": f"{item_name} = {_short(item_val)}",
                    "bind_group": bind_group,
                    "bind_block": bind_block,
                })
            elif _is_class_object(item_val):
                cid = add_obj(item_val, _format_typed_label(item_name, item_val))
                if cid:
                    owner["rows"].append({
                        "name": item_name,
                        "kind": "ref",
                        "text": item_name,
                        "bind_group": bind_group,
                        "bind_block": bind_block,
                    })
                    owner["refs"].append({"name": item_name})
                    edges.append({
                        "src": obj_id,
                        "dst": cid,
                        "label": item_name
                    })
                else:
                    owner["rows"].append({
                        "name": item_name,
                        "kind": "field",
                        "text": f"{item_name} = {_short(item_val)}",
                        "bind_group": bind_group,
                        "bind_block": bind_block,
                    })
            else:
                owner["rows"].append({
                    "name": item_name,
                    "kind": "field",
                    "text": f"{item_name} = {_short(item_val)}",
                    "bind_group": bind_group,
                    "bind_block": bind_block,
                })

        for group_name, mapping in bind_groups.items():
            ordered_fields = [attr for attr in mapping.keys() if attr in item_map]
            if len(ordered_fields) < 2:
                continue
            bound_streams = {}
            for attr in ordered_fields:
                val = item_map.get(attr)
                if not isinstance(val, (list, tuple, set, frozenset, dict, deque)):
                    continue
                bound_streams[attr] = {
                    "ratio": mapping.get(attr, 1),
                    "items": list(_iter_container_items(attr, val)),
                    "cursor": 0,
                }
            if len(bound_streams) < 2:
                continue
            block_index = 0
            progressed = True
            while progressed:
                progressed = False
                for attr in ordered_fields:
                    stream = bound_streams.get(attr)
                    if not stream:
                        continue
                    take = stream["ratio"]
                    while take > 0 and stream["cursor"] < len(stream["items"]):
                        item_name, item_val = stream["items"][stream["cursor"]]
                        _append_container_item(
                            item_name,
                            item_val,
                            bind_group=group_name,
                            bind_block=f"{group_name}#{block_index}",
                        )
                        stream["cursor"] += 1
                        take -= 1
                        progressed = True
                if progressed:
                    block_index += 1

        for attr, val in object_items:
            if attr in bound_fields:
                continue
            if _is_primitive(val):
                owner["rows"].append({
                    "name": attr,
                    "kind": "field",
                    "text": f"{attr} = {_short(val)}",
                })
            elif isinstance(val, (list, tuple, set, frozenset, dict, deque)):
                items = list(_iter_container_items(attr, val))
                if not items:
                    owner["rows"].append({
                        "name": attr,
                        "kind": "field",
                        "text": f"{attr} = {type(val).__name__}()",
                    })
                    continue

                for item_name, item_val in items:
                    _append_container_item(item_name, item_val)
            elif _is_class_object(val):
                cid = add_obj(val, _format_typed_label(attr, val))
                if cid:
                    owner["rows"].append({
                        "name": attr,
                        "kind": "ref",
                        "text": attr,
                    })
                    owner["refs"].append({"name": attr})
                    edges.append({
                        "src": obj_id,
                        "dst": cid,
                        "label": attr
                    })

    return nodes, edges

# ---------- G6 渲染 ----------

def _build_g6_data(nodes, edges):
    g6_data = {
        "nodes": [],
        "edges": []
    }

    id_to_name = {}
    class_count = {}

    padding_x = 10
    padding_y = 8
    row_h = 18
    default_header_h = 22
    section_gap = 6
    card_w = 100

    for n in nodes:
        cls = n.get("class_name") or "Obj"
        class_count[cls] = class_count.get(cls, 0) + 1
        name = n.get("label") or f"{cls}#{class_count[cls]}"
        id_to_name[n["id"]] = name

        rows = n.get("rows", [])
        display_rows = [r.get("text", "") for r in rows]
        bind_groups = [r.get("bind_group") for r in rows]
        bind_blocks = [r.get("bind_block") for r in rows]
        bind_groups = [r.get("bind_group") for r in rows]
        bind_blocks = [r.get("bind_block") for r in rows]
        header_line_count = max(1, len(str(name).splitlines()))
        header_h = max(default_header_h, header_line_count * 16)

        height = (
            padding_y * 2
            + header_h
            + max(len(display_rows), 1) * row_h
        )

        header_center_y = (padding_y + header_h / 2) / height

        ports = [
            {"key": "inL", "placement": [0, header_center_y], "r": 0, "fill": "transparent", "stroke": "transparent"},
            {"key": "inR", "placement": [1, header_center_y], "r": 0, "fill": "transparent", "stroke": "transparent"},
        ]

        ref_row_indices = []
        for row_idx, row in enumerate(rows):
            if row.get("kind") != "ref":
                continue
            ref_row_indices.append(row_idx)
            y = (
                padding_y
                + header_h
                + row_idx * row_h
                + row_h / 2
            ) / height
            ports.append({"key": f"pl{row_idx}", "placement": [0, y], "r": 0, "fill": "transparent", "stroke": "transparent"})
            ports.append({"key": f"pr{row_idx}", "placement": [1, y], "r": 0, "fill": "transparent", "stroke": "transparent"})

        g6_data["nodes"].append({
            "id": str(n["id"]),
            "type": "card",
            "style": {
                "size": [card_w, height],
                "name": name,
                "headerHeight": header_h,
                "rows": display_rows,
                "rowBindGroups": bind_groups,
                "rowBindBlocks": bind_blocks,
                "refRowIndices": ref_row_indices,
                "sectionGap": section_gap,
                "ports": ports
            }
        })

    ref_index = {}
    for n in g6_data["nodes"]:
        ref_rows = (n.get("style") or {}).get("refRowIndices", [])
        rows = (n.get("style") or {}).get("rows", [])
        mapping = {}
        for row_idx in ref_rows:
            if 0 <= row_idx < len(rows):
                mapping[rows[row_idx]] = row_idx
        ref_index[n["id"]] = mapping

    edge_counter = 0
    for e in edges:
        src_id = str(e["src"])
        dst_id = str(e["dst"])
        label = e.get("label", "")
        ref_idx = None
        if label and src_id in ref_index and label in ref_index[src_id]:
            ref_idx = ref_index[src_id][label]

        edge_item = {
            "id": f"e{edge_counter}",
            "source": src_id,
            "target": dst_id,
            "data": {"refIndex": ref_idx},
            "style": {}
        }
        edge_counter += 1
        g6_data["edges"].append(edge_item)

    return g6_data


def _build_stack_view(step):
    scope = step.get("scope") or {}
    raw_globals = scope.get("globals") or {}
    raw_frames = scope.get("frames") or []
    internal_names = {"trigger", "dsvis", "filepath", "code", "compiled", "f", "global_env", "new_tree", "previous_flag", "transformer", "tree"}

    def _safe_short(value):
        return _short(value, max_len=120)

    def _describe_value(value):
        if _is_primitive(value):
            return _safe_short(value)

        if isinstance(value, dict):
            pairs = []
            for idx, (k, v) in enumerate(value.items()):
                if idx >= 4:
                    pairs.append("...")
                    break
                pairs.append(f"{_safe_short(k)}: {_safe_short(v)}")
            return "{" + ", ".join(pairs) + "}"

        if isinstance(value, (list, tuple, deque, set, frozenset)):
            try:
                seq = list(value)
            except Exception:
                return _safe_short(value)
            parts = []
            for idx, item in enumerate(seq):
                if idx >= 4:
                    parts.append("...")
                    break
                parts.append(_safe_short(item))
            left, right = ("[", "]")
            if isinstance(value, tuple):
                left, right = ("(", ")")
            elif isinstance(value, (set, frozenset)):
                left, right = ("{", "}")
            return f"{left}{', '.join(parts)}{right}"

        if _is_class_object(value):
            fields = []
            try:
                for idx, (k, v) in enumerate(_iter_object_items(value, include_private=False)):
                    if idx >= 4:
                        fields.append("...")
                        break
                    fields.append(f"{k}={_safe_short(v)}")
            except Exception:
                return _safe_short(value)
            type_name = type(value).__name__
            return f"{type_name}{{{', '.join(fields)}}}"

        return _safe_short(value)

    def _build_value_tree(value, depth=0, max_depth=4, max_items=20):
        if depth >= max_depth:
            return {
                "text": _safe_short(value),
                "children": [],
                "truncated": True,
            }

        if _is_primitive(value):
            return {
                "text": _safe_short(value),
                "children": [],
                "truncated": False,
            }

        children = []
        truncated = False

        if isinstance(value, dict):
            for idx, (k, v) in enumerate(value.items()):
                if idx >= max_items:
                    truncated = True
                    break
                children.append({
                    "name": _safe_short(k),
                    "tree": _build_value_tree(v, depth=depth + 1, max_depth=max_depth, max_items=max_items),
                })
            return {
                "text": f"dict ({len(value)})",
                "children": children,
                "truncated": truncated,
            }

        if isinstance(value, (list, tuple, deque)):
            seq = list(value)
            for idx, item in enumerate(seq):
                if idx >= max_items:
                    truncated = True
                    break
                children.append({
                    "name": f"[{idx}]",
                    "tree": _build_value_tree(item, depth=depth + 1, max_depth=max_depth, max_items=max_items),
                })
            kind = type(value).__name__
            return {
                "text": f"{kind} ({len(seq)})",
                "children": children,
                "truncated": truncated,
            }

        if isinstance(value, (set, frozenset)):
            seq = sorted(list(value), key=lambda x: _safe_short(x))
            for idx, item in enumerate(seq):
                if idx >= max_items:
                    truncated = True
                    break
                children.append({
                    "name": f"[{idx}]",
                    "tree": _build_value_tree(item, depth=depth + 1, max_depth=max_depth, max_items=max_items),
                })
            kind = type(value).__name__
            return {
                "text": f"{kind} ({len(seq)})",
                "children": children,
                "truncated": truncated,
            }

        if _is_class_object(value):
            try:
                items = list(_iter_object_items(value, include_private=False))
            except Exception:
                return {
                    "text": _safe_short(value),
                    "children": [],
                    "truncated": False,
                }
            for idx, (k, v) in enumerate(items):
                if idx >= max_items:
                    truncated = True
                    break
                children.append({
                    "name": str(k),
                    "tree": _build_value_tree(v, depth=depth + 1, max_depth=max_depth, max_items=max_items),
                })
            return {
                "text": f"{type(value).__name__}",
                "children": children,
                "truncated": truncated,
            }

        return {
            "text": _safe_short(value),
            "children": [],
            "truncated": False,
        }

    globals_items = []
    for name in sorted(raw_globals.keys()):
        if str(name).startswith("_") or str(name) in internal_names:
            continue
        globals_items.append({
            "name": str(name),
            "text": _describe_value(raw_globals[name]),
            "tree": _build_value_tree(raw_globals[name]),
            "is_param": False,
        })

    frame_name_count = {}
    locals_frames = []
    for frame in raw_frames:
        func_name = str(frame.get("function") or "<module>")
        frame_name_count[func_name] = frame_name_count.get(func_name, 0) + 1
        frame_title = f"{func_name}#{frame_name_count[func_name]}"

        params = list(frame.get("params") or [])
        param_set = set(str(p) for p in params)
        local_dict = frame.get("locals") or {}
        ordered_names = []
        for p in params:
            if p in local_dict and not str(p).startswith("_") and str(p) not in internal_names:
                ordered_names.append(str(p))
        for k in sorted(local_dict.keys()):
            ks = str(k)
            if ks.startswith("_") or ks in param_set or ks in internal_names:
                continue
            ordered_names.append(ks)

        rows = []
        for n in ordered_names:
            v = local_dict.get(n)
            rows.append({
                "name": n,
                "text": _describe_value(v),
                "tree": _build_value_tree(v),
                "is_param": n in param_set,
            })
        locals_frames.append({
            "title": frame_title,
            "function": func_name,
            "rows": rows,
        })

    return {
        "globals": globals_items,
        "frames": locals_frames,
    }


def _render_debugger(steps, source_lines, title="DSVis Debugger", layout=None):
    import tempfile
    import webbrowser
    import json
    from pathlib import Path

    step_payload = []
    for idx, step in enumerate(steps, start=1):
        step_payload.append({
            "step": idx,
            "lineno": step.get("lineno"),
            "stack_view": _build_stack_view(step),
        })

    template_path = Path(__file__).parent / "template.html"
    html = template_path.read_text(encoding="utf-8")
    html = html.replace("__TITLE__", title)
    html = html.replace("__STEPS__", json.dumps(step_payload, ensure_ascii=False))
    html = html.replace("__SOURCE_LINES__", json.dumps(source_lines, ensure_ascii=False))
    html = html.replace("__LAYOUT__", json.dumps(_normalize_layout(layout)))

    fd, path = tempfile.mkstemp(suffix=".html")
    html_path = Path(path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(html_path.as_uri())
    print(f"[dsvis] HTML 输出：{html_path}")
    return html_path

# ---------- 对外接口 ----------

def capture(
    max_nodes=300,
    include_private=False,
    include_containers=None,
    focus_vars=None,
    pointer_watchers=None,
    _caller_frame=None,
):
    frame = inspect.currentframe()
    caller = _caller_frame if _caller_frame is not None else (frame.f_back if frame else None)

    if not caller:
        print("[dsvis] 无法获取调用帧")
        return

    try:
        # 统一模式：capture 现在使用 scheduler，就像 trigger 一样
        # 这样 capture 就和 auto 模式统一了，都通过 scheduler 收集 steps，最后一起渲染
        mode = get_mode()
        container_flag = (mode == "fine") if include_containers is None else include_containers
        merged_focus = set(get_watch_vars()) | set(focus_vars or [])
        merged_pointers = list(get_pointer_watchers()) + list(pointer_watchers or [])
        
        # 调用 scheduler 的 request_update，就像 trigger 一样
        # 这会检查数据是否变化，如果变化就添加到 steps 中
        scheduler.request_update(
            caller_frame=caller,
            lineno=caller.f_lineno,
            observed_vars=merged_focus,
            pointer_watchers=merged_pointers,
            max_nodes=max_nodes,
            include_private=include_private,
        )

    finally:
        del frame
        if _caller_frame is None and caller:
            del caller


def _find_main_script():
    frame = inspect.currentframe()
    try:
        current = frame.f_back if frame else None
        while current:
            g = current.f_globals
            if g.get("__name__") == "__main__" and g.get("__file__"):
                return str(Path(g["__file__"]).resolve())
            current = current.f_back
    finally:
        if frame:
            del frame
    return None


def auto(fn=None):
    """
    自动追踪模式，支持两种用法：
    
    1) 装饰器用法（顶层使用）：
        @dsvis.auto()
        def main():
            pass
    
    2) 脚本顶部调用（启用 AST 自动插桩）：
        import dsvis
        dsvis.auto()  # 如果没有被用作装饰器
    """
    
    def make_decorator():
        """返回实际的装饰器"""
        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                # 装饰器模式：在函数执行期间收集所有变化
                result = fn(*args, **kwargs)
                
                # 函数执行完后刷新调度器以生成可视化
                scheduler.flush()
                
                return result
            
            return wrapper
        return decorator
    
    # 如果 fn 是可调用的，说明被用作 @auto 不带括号
    if callable(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            scheduler.flush()
            return result
        return wrapper
    
    # fn 为 None，说明是 @auto() 带括号的装饰器用法或脚本顶部调用
    # 先尝试检查调用栈，看是否在装饰器上下文中
    frame = inspect.currentframe()
    try:
        # 查看调用栈，是否下一帧就是被装饰的函数定义
        caller = frame.f_back if frame else None
        if caller and caller.f_code.co_name == '<module>':
            # 在模块级别被调用，可能是装饰器或脚本顶部调用
            # 检查环境变量看是否已经在 AST 运行中
            if os.environ.get("DSVIS_AST_RUNNING") != "1":
                # 第一次调用且在主模块，执行 AST 模式
                main_file = _find_main_script()
                if main_file and Path(main_file).resolve() != Path(__file__).resolve():
                    from .runtime.ast_hook import run_file
                    run_file(main_file)
                    raise SystemExit(0)
    finally:
        del frame
    
    # 返回装饰器
    return make_decorator()

