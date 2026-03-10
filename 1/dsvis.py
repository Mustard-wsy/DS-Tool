import inspect
import html
import tempfile
import webbrowser
from pathlib import Path
from collections import deque

__all__ = ["capture"]

# ---------- helpers ----------

def _is_primitive(x):
    return isinstance(x, (int, float, str, bool, bytes, complex))

def _is_obj(x):
    if x is None:
        return False
    t = type(x)
    if t.__module__ == "builtins":
        return False
    return hasattr(x, "__dict__")

def _short(x, n=40):
    try:
        s = repr(x)
    except:
        s = "?"
    if len(s) > n:
        s = s[:n] + "..."
    return s

# ---------- walk objects ----------

def _walk(scope, max_nodes=200):
    visited = set()
    nodes = {}
    edges = []

    tag_counter = {}

    def make_tag(obj):
        name = type(obj).__name__
        tag_counter.setdefault(name, 0)
        tag_counter[name] += 1
        addr = hex(id(obj))
        return f"{name}#{tag_counter[name]} @{addr}"

    q = deque()

    def add(obj):
        oid = id(obj)
        if oid in visited:
            return oid
        if len(nodes) >= max_nodes:
            return None
        visited.add(oid)
        node = {"id": oid, "tag": make_tag(obj), "fields": [], "obj": obj}
        nodes[oid] = node
        q.append(obj)
        return oid

    for name, val in scope.items():
        if name.startswith("_"):
            continue
        if _is_obj(val):
            add(val)

    while q:
        obj = q.popleft()
        oid = id(obj)
        node = nodes[oid]
        try:
            items = vars(obj).items()
        except:
            continue
        for attr, val in items:
            if val is None:
                node["fields"].append({"name": attr, "type": "null"})
            elif _is_primitive(val):
                node["fields"].append({"name": attr, "type": "value", "value": _short(val)})
            elif _is_obj(val):
                cid = add(val)
                node["fields"].append({"name": attr, "type": "ptr", "target": cid})
                if cid:
                    edges.append((oid, cid, attr))
            else:
                node["fields"].append({"name": attr, "type": "value", "value": type(val).__name__})

    return list(nodes.values()), edges

# ---------- layout ----------

def _layout(nodes):
    """
    布局节点：
    - 每个节点内部竖直表格
    - 节点之间水平排列
    """
    row_h = 22
    node_w = 200
    x_gap = 60
    y_gap = 60

    pos = {}
    ports = {}

    x = 20
    y = 60
    max_row_y = 0

    for n in nodes:
        nid = n["id"]
        node_h = row_h * (1 + len(n["fields"]))
        pos[nid] = (x, y)
        ports[nid] = {}

        # 记录字段中心位置
        for j, f in enumerate(n["fields"]):
            row_top = y + row_h * (j + 1)
            row_center = row_top + row_h / 2
            ports[nid][f["name"]] = row_center

        # 更新下一节点位置，水平排列
        x += node_w + x_gap
        max_row_y = max(max_row_y, y + node_h)

        # 如果超出页面宽度，则换行
        if x > 1200:
            x = 20
            y = max_row_y + y_gap
            max_row_y = y

    return pos, ports

# ---------- svg render ----------

def _render(nodes, edges, title):
    pos, ports = _layout(nodes)
    node_map = {n["id"]: n for n in nodes}

    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000">')

    lines.append("""
<defs>
<marker id="arrow" markerWidth="10" markerHeight="10"
refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
<path d="M0,0 L0,6 L9,3 z" fill="#4a6fa5"/>
</marker>
</defs>
""")

    lines.append(f'<text x="20" y="28" font-family="Consolas, monospace" font-size="18" fill="#1f2d3d">{html.escape(title)}</text>')

    # draw edges
    for s, d, name in edges:
        if s not in pos or d not in pos:
            continue
        src_x, src_y = pos[s]
        dst_x, dst_y = pos[d]
        y1 = ports[s].get(name, src_y)
        row_h = 22
        y2 = dst_y + row_h / 2  # tag 行中央
        x1 = src_x + 200
        x2 = dst_x
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4a6fa5" stroke-width="1.4" marker-end="url(#arrow)"/>')

    # draw nodes
    for n in nodes:
        x, y = pos[n["id"]]
        row_h = 22
        width = 200
        height = row_h * (1 + len(n["fields"]))

        # node background
        lines.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" ry="6" fill="#ffffff" stroke="#4a6fa5" stroke-width="1.2"/>')
        # header background
        lines.append(f'<rect x="{x}" y="{y}" width="{width}" height="{row_h}" rx="6" ry="6" fill="#dbe9ff" stroke="#4a6fa5" stroke-width="1.0"/>')
        # tag
        lines.append(f'<text x="{x+10}" y="{y+16}" font-family="Consolas, monospace" font-size="14" fill="#1f2d3d">{html.escape(n["tag"])}</text>')

        yy = y + row_h
        for f in n["fields"]:
            lines.append(f'<line x1="{x}" y1="{yy}" x2="{x+width}" y2="{yy}" stroke="#d0dbef" stroke-width="1"/>')

            if f["type"] == "value":
                val = f["value"]
            elif f["type"] == "null":
                val = "null"
            elif f["type"] == "ptr":
                target_node = node_map.get(f.get("target"))
                val = target_node["tag"] if target_node else "null"
            else:
                val = "?"

            # field name
            lines.append(f'<text x="{x+10}" y="{yy+16}" font-family="Consolas, monospace" font-size="12" fill="#243447">{html.escape(f["name"])}</text>')
            # field value
            lines.append(f'<text x="{x+120}" y="{yy+16}" font-family="Consolas, monospace" font-size="12" fill="#2f4f7f">{html.escape(val)}</text>')

            yy += row_h

    lines.append("</svg>")

    svg = "\n".join(lines)
    fd, path = tempfile.mkstemp(suffix=".svg")
    Path(path).write_text(svg, encoding="utf8")
    webbrowser.open(Path(path).as_uri())
    print("[dsvis] svg:", path)
    return path

# ---------- public api ----------

def capture(title="DSVis Snapshot"):
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        return
    caller = frame.f_back
    scope = dict(caller.f_locals)
    nodes, edges = _walk(scope)
    return _render(nodes, edges, title)