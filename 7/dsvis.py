import functools
import inspect
import tempfile
import webbrowser
import json
import os
from collections import deque
from pathlib import Path

from runtime.config import get_mode, get_pointer_watchers, get_watch_vars, set_mode

__all__ = ["capture", "auto", "watch_vars", "observe", "observe_ptr", "set_mode"]

_DEFAULT_LAYOUT = {
    "type": "dagre",
    "rankdir": "LR",
    "nodesep": 120,
    "ranksep": 220,
}

_LAYOUT_PRESETS = {
    "default": dict(_DEFAULT_LAYOUT),
    "concentriclayout": {"type": "concentric"},
    "snakelayout": {"type": "snake"},
}

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


def _normalize_layout(layout):
    if layout is None:
        return dict(_DEFAULT_LAYOUT)

    if isinstance(layout, str):
        key = layout.strip().lower()
        if key in _LAYOUT_PRESETS:
            return dict(_LAYOUT_PRESETS[key])
        raise ValueError(
            "layout 必须是 default / ConcentricLayout / SnakeLayout 或布局字典"
        )

    if isinstance(layout, dict):
        merged = dict(_DEFAULT_LAYOUT)
        merged.update(layout)
        return merged

    raise ValueError("layout 参数类型无效，必须是字符串或字典")

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

        for attr, val in _iter_object_items(obj, include_private):
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
                    if _is_primitive(item_val):
                        owner["rows"].append({
                            "name": item_name,
                            "kind": "field",
                            "text": f"{item_name} = {_short(item_val)}",
                        })
                    elif _is_class_object(item_val):
                        cid = add_obj(item_val, _format_typed_label(item_name, item_val))
                        if cid:
                            owner["rows"].append({
                                "name": item_name,
                                "kind": "ref",
                                "text": item_name,
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
                            })
                    else:
                        owner["rows"].append({
                            "name": item_name,
                            "kind": "field",
                            "text": f"{item_name} = {_short(item_val)}",
                        })
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


def _render_g6(nodes, edges, title="AutoViz Snapshot", layout=None):
    import tempfile
    import webbrowser
    import json
    from pathlib import Path

    g6_data = _build_g6_data(nodes, edges)
    layout = _normalize_layout(layout)

    template_path = Path(__file__).parent / "template.html"
    html = template_path.read_text(encoding="utf-8")

    html = html.replace("__DATA__", json.dumps(g6_data))
    html = html.replace("__LAYOUT__", json.dumps(layout))
    html = html.replace("__TITLE__", title)

    fd, path = tempfile.mkstemp(suffix=".html")
    html_path = Path(path)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(html_path.as_uri())
    print(f"[dsvis] G6 HTML 输出：{html_path}")

    return html_path


def _render_debugger(steps, source_lines, title="DSVis Debugger"):
    import tempfile
    import webbrowser
    import json
    from pathlib import Path

    step_payload = []
    for idx, step in enumerate(steps, start=1):
        step_payload.append({
            "step": idx,
            "lineno": step.get("lineno"),
            "graph": _build_g6_data(step.get("nodes", []), step.get("edges", [])),
        })

    template_path = Path(__file__).parent / "debug_template.html"
    html = template_path.read_text(encoding="utf-8")
    html = html.replace("__TITLE__", title)
    html = html.replace("__STEPS__", json.dumps(step_payload, ensure_ascii=False))
    html = html.replace("__SOURCE_LINES__", json.dumps(source_lines, ensure_ascii=False))

    fd, path = tempfile.mkstemp(suffix=".html")
    html_path = Path(path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(html_path.as_uri())
    print(f"[dsvis] Debugger HTML 输出：{html_path}")
    return html_path

# ---------- 对外接口 ----------

def capture(
    title="AutoViz Snapshot",
    max_nodes=300,
    include_private=False,
    include_containers=None,
    focus_vars=None,
    pointer_watchers=None,
    layout=None,
    _caller_frame=None,
):
    frame = inspect.currentframe()
    caller = _caller_frame if _caller_frame is not None else (frame.f_back if frame else None)

    if not caller:
        print("[dsvis] 无法获取调用帧")
        return

    try:
        root_scope = {
            "__locals__": dict(caller.f_locals),
            "__globals__": dict(caller.f_globals)
        }

        mode = get_mode()
        container_flag = (mode == "fine") if include_containers is None else include_containers
        merged_focus = set(get_watch_vars()) | set(focus_vars or [])
        merged_pointers = list(get_pointer_watchers()) + list(pointer_watchers or [])
        nodes, edges = _walk(
            root_scope,
            max_nodes=max_nodes,
            include_private=include_private,
            include_containers=container_flag,
            focus_vars=merged_focus,
            pointer_watchers=merged_pointers,
        )

        return _render_g6(nodes, edges, title, layout=layout)

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


def auto():
    """
    显式启用 AST 自动插桩模式：
    用户在脚本顶部写：

        import dsvis
        dsvis.auto()
    """
    if os.environ.get("DSVIS_AST_RUNNING") == "1":
        return

    main_file = _find_main_script()
    if not main_file:
        raise RuntimeError("dsvis.auto() 只能在脚本主模块中调用")
    if Path(main_file).resolve() == Path(__file__).resolve():
        return

    from runtime.ast_hook import run_file

    run_file(main_file)
    raise SystemExit(0)


def watch_vars(*names, pointers=None):
    pointers = list(pointers or [])

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from runtime.config import pop_watch_context, push_watch_context

            push_watch_context(set(names), pointers)
            try:
                return fn(*args, **kwargs)
            finally:
                pop_watch_context()

        return wrapper

    return decorator


def observe(tag=None, vars=None, pointers=None):
    from runtime.trigger import trigger

    trigger(observed_vars=set(vars or []), pointer_watchers=list(pointers or []), tag=tag)


def observe_ptr(name, container, tag=None):
    observe(tag=tag, pointers=[(name, container)])
