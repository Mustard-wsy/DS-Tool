import inspect
import tempfile
import webbrowser
from collections import deque
from pathlib import Path
from pyvis.network import Network
import html

__all__ = ["capture"]

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

    # 遍历局部和全局作用域
    for scope_dict in [root_scope["__locals__"], root_scope["__globals__"]]:
        for k, v in scope_dict.items():
            if not include_private and k.startswith("_"):
                continue
            label = f"{k} = {_short(v)}" if _is_primitive(v) else f"{k}: {_typename(v)}"
            add_obj(v, label)

    # BFS 遍历对象字段
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
                    edges.append({"src": obj_id, "dst": cid, "label": attr})
    return nodes, edges
def _render_pyvis(nodes, edges, title="AutoViz Snapshot"):
    net = Network(height="880px", width="100%", directed=True)

    net.set_options("""
    {
      "nodes": {
        "font": {"size":14,"face":"Consolas"},
        "shape": "box"
      },
      "edges": {
        "arrows": {"to": {"enabled": true}},
        "smooth": {"enabled": true, "type": "cubicBezier"}
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.2,
          "springLength": 150,
          "springConstant": 0.05,
          "damping": 0.28,
          "avoidOverlap": 1
        }
      }
    }
    """)

    # 指针颜色表（可扩展）
    _POINTER_COLORS = [
        "#4a90e2",  # 蓝色 → next
        "#e94e77",  # 粉红 → prev
        "#f5a623",  # 橙色 → left
        "#7ed321",  # 绿色 → right
        "#9013fe",  # 紫色 → parent
        "#50e3c2",  # 青色 → child
        "#b8e986",  # 浅绿 → succ
        "#d0021b",  # 红色 → last
        "#f8e71c",  # 黄 → top
        "#417505",  # 深绿 → bottom
    ]

    id_to_name = {}
    class_count = {}
    for i, n in enumerate(nodes):
        cls_name = n.get("class_name") or "Object"
        class_count[cls_name] = class_count.get(cls_name, 0) + 1
        display_name = f"{cls_name}{class_count[cls_name]}"
        id_to_name[n["id"]] = display_name
        n["_display_name"] = display_name  # 保存备用

    # 构建指针类型到颜色的映射
    pointer_types = set(e.get("label", "") for e in edges)
    color_map = {p: _POINTER_COLORS[i % len(_POINTER_COLORS)]
                 for i, p in enumerate(sorted(pointer_types))}

    # 添加节点
    for n in nodes:
        lines = [id_to_name[n["id"]]]  # 第一行显示节点名

        # 输出基本字段
        for f in n.get("fields", []):
            lines.append(f)

        # 输出引用字段
        for r in n.get("refs", []):
            dst_id = None
            for e in edges:
                if e.get("src") == n["id"] and e.get("label") == r["name"]:
                    dst_id = e.get("dst")
                    break
            if dst_id is not None and dst_id in id_to_name:
                lines.append(f"{r['name']} -> {id_to_name[dst_id]}")
            else:
                lines.append(f"{r['name']} -> None")

        label_text = "\n".join(lines)

        net.add_node(
            n["id"],
            label=label_text,
            title=n["type"],
            shape="box",
            color="#e8f0fe",
            widthConstraint={"minimum": 220}
        )

    # 添加边，按指针类型使用不同颜色
    for e in edges:
        ptr_name = e.get("label", "")
        color = color_map.get(ptr_name, "#4a6fa5")  # 默认蓝色
        net.add_edge(
            e["src"],
            e["dst"],
            label=ptr_name,  # 可以显示指针名
            color=color,
            width=2
        )

    fd, path = tempfile.mkstemp(suffix=".html")
    html_path = Path(path)
    net.write_html(str(html_path))
    webbrowser.open(html_path.as_uri())
    print(f"[auto_viz] PyVis HTML 输出：{html_path}")

    return html_path
# def _render_pyvis(nodes, edges, title="AutoViz Snapshot"):
#     net = Network(height="880px", width="100%", directed=True)
#     net.set_options("""
#     {
#       "nodes": {"font":{"size":14,"face":"Consolas"},"shape":"box"},
#       "edges": {"arrows":{"to":{"enabled":true}},"color":{"color":"#4a6fa5"}}
#     }
#     """)
#
#     for n in nodes:
#         label_lines = [n["label"]] + n.get("fields", []) + [f'{r["name"]} ->' for r in n.get("refs", [])]
#         label = "\n".join(label_lines)
#         net.add_node(n["id"], label=label, title=n["type"], color="#e8f0fe")
#
#     for e in edges:
#         net.add_edge(e["src"], e["dst"], label="")
#
#     fd, path = tempfile.mkstemp(suffix=".html")
#     html_path = Path(path)
#     net.write_html(str(html_path))
#     webbrowser.open(html_path.as_uri())
#     print(f"[auto_viz] PyVis HTML 输出：{html_path}")
#     return html_path

def capture(title="AutoViz Snapshot", max_nodes=300, include_private=False):
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    if not caller:
        print("[auto_viz] 无法获取调用帧")
        return
    try:
        root_scope = {
            "__locals__": dict(caller.f_locals),
            "__globals__": dict(caller.f_globals)
        }
        nodes, edges = _walk(root_scope, max_nodes=max_nodes, include_private=include_private)
        return _render_pyvis(nodes, edges, title)
    finally:
        del frame
        if caller:
            del caller

