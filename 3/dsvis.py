import inspect
import tempfile
import webbrowser
import json
from collections import deque
from pathlib import Path

__all__ = ["capture"]

# ---------- helpers ----------

def _typename(obj):
    try:
        t = type(obj)
        mod = getattr(t, "__module__", "")
        name = getattr(t, "__qualname__", getattr(t, "__name__", str(t)))
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

def _is_renderable(obj):
    return _is_class_object(obj) or _is_primitive(obj)

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

# ---------- 核心遍历 ----------

def _walk(root_scope, max_nodes=300, include_private=False):
    visited = set()
    nodes = []
    edges = []
    node_index = {}
    q = deque()

    def add_obj(obj, label):
        if not _is_renderable(obj):
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
            "fields": [],
            "refs": [],
            "class_name": type(obj).__name__ if obj else "NoneType",
            "is_class_object": _is_class_object(obj),
        }
        nodes.append(n)
        node_index[obj_id] = n
        q.append(obj)
        return obj_id

    # 扫描作用域
    for scope_dict in [root_scope["__locals__"], root_scope["__globals__"]]:
        for k, v in scope_dict.items():
            if not include_private and k.startswith("_"):
                continue
            label = f"{k} = {_short(v)}" if _is_primitive(v) else f"{k}: {_typename(v)}"
            add_obj(v, label)

    # BFS
    while q:
        obj = q.popleft()
        obj_id = id(obj)
        owner = node_index.get(obj_id)

        if owner is None or not owner.get("is_class_object"):
            continue

        for attr, val in _iter_object_items(obj, include_private):
            if _is_primitive(val):
                owner["fields"].append(f"{attr} = {_short(val)}")
            elif _is_class_object(val):
                cid = add_obj(val, f"{attr}: {_typename(val)}")
                if cid:
                    owner["refs"].append({"name": attr})
                    edges.append({
                        "src": obj_id,
                        "dst": cid,
                        "label": attr
                    })

    return nodes, edges

# ---------- G6 渲染 ----------

def _render_g6(nodes, edges, title="AutoViz Snapshot"):
    import tempfile
    import webbrowser
    import json
    from pathlib import Path

    # 转换数据格式
    g6_data = {
        "nodes": [],
        "edges": []
    }

    id_to_name = {}
    class_count = {}

    padding_x = 10
    padding_y = 8
    row_h = 18
    header_h = 22
    section_gap = 6
    card_w = 100

    for n in nodes:
        cls = n.get("class_name") or "Obj"
        class_count[cls] = class_count.get(cls, 0) + 1
        name = f"{cls}#{class_count[cls]}"
        id_to_name[n["id"]] = name

        refs = [r.get("name", "") for r in n.get("refs", [])]
        fields = n.get("fields", [])
        field_rows = max(len(fields), 1)
        ref_rows = max(len(refs), 1) if refs else 0

        height = (
            padding_y * 2
            + header_h
            + field_rows * row_h
            + (section_gap if refs else 0)
            + ref_rows * row_h
        )

        header_center_y = (padding_y + header_h / 2) / height

        ports = [
            {"key": "inL", "placement": [0, header_center_y], "r": 2.5, "fill": "#5b8ff9", "stroke": "#2b6cd4"},
            {"key": "inR", "placement": [1, header_center_y], "r": 2.5, "fill": "#5b8ff9", "stroke": "#2b6cd4"},
        ]
        for i in range(len(refs)):
            y = (
                padding_y
                + header_h
                + field_rows * row_h
                + section_gap
                + i * row_h
                + row_h / 2
            ) / height
            ports.append({"key": f"pl{i}", "placement": [0, y], "r": 2.5, "fill": "#5b8ff9", "stroke": "#2b6cd4"})
            ports.append({"key": f"pr{i}", "placement": [1, y], "r": 2.5, "fill": "#5b8ff9", "stroke": "#2b6cd4"})

        g6_data["nodes"].append({
            "id": str(n["id"]),
            "type": "card",
            "style": {
                "size": [card_w, height],
                "name": name,
                "fields": fields,
                "refs": refs,
                "sectionGap": section_gap,
                "ports": ports
            }
        })

    ref_index = {}
    for n in g6_data["nodes"]:
        refs = (n.get("style") or {}).get("refs", [])
        ref_index[n["id"]] = {r: i for i, r in enumerate(refs)}

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

    layout = {
        "type": "dagre",
        "rankdir": "LR",
        "nodesep": 120,
        "ranksep": 220
    }

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

# ---------- 对外接口 ----------

def capture(title="AutoViz Snapshot", max_nodes=300, include_private=False):
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None

    if not caller:
        print("[dsvis] 无法获取调用帧")
        return

    try:
        root_scope = {
            "__locals__": dict(caller.f_locals),
            "__globals__": dict(caller.f_globals)
        }

        nodes, edges = _walk(
            root_scope,
            max_nodes=max_nodes,
            include_private=include_private
        )

        return _render_g6(nodes, edges, title)

    finally:
        del frame
        if caller:
            del caller


