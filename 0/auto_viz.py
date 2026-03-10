import inspect
import os
from collections import deque
from pathlib import Path
import tempfile
import webbrowser
import html
import shutil
import subprocess

# 尝试导入可视化后端
_has_pyvis = False
# try:
#     from pyvis.network import Network
#     _has_pyvis = True
# except Exception:
#     pass

_has_graphviz = False
# try:
#     from graphviz import Digraph
#     _has_graphviz = True
# except Exception:
#     pass

_has_plantuml = shutil.which("plantuml") is not None

__all__ = ["capture"]


def _typename(obj):
    """返回对象类型名，尽量包含模块信息。"""
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
    """安全的短字符串表示，避免 repr 异常或过长。"""
    try:
        s = repr(obj)
    except Exception:
        s = f"<unreprable {_typename(obj)}>"
    s = s.replace("\n", "\\n")
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def _is_primitive(obj):
    return isinstance(obj, (int, float, str, bool, bytes, complex, type(None)))


def _is_class_object(obj) -> bool:
    """判断对象是否应当按 UML 对象渲染。"""
    try:
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
    except Exception:
        return False


def _is_renderable(obj):
    # 只保留：class object + 基本类型
    return _is_class_object(obj) or _is_primitive(obj)


def _is_terminal(obj):
    return (
        _is_primitive(obj)
        or inspect.ismodule(obj)
        or inspect.isroutine(obj)
        or inspect.isclass(obj)
    )


def _safe_port(name: str) -> str:
    s = "".join(ch if ch.isalnum() else "_" for ch in str(name))
    if not s:
        s = "ref"
    if s[0].isdigit():
        s = "_" + s
    return f"p_{s}"


def _gv_escape(s: str) -> str:
    return html.escape(str(s), quote=True)


def _iter_object_items(obj, include_private):
    # 尽量避免触发 property/descriptor 执行
    try:
        for k, v in vars(obj).items():
            if (not include_private) and str(k).startswith("_"):
                continue
            yield str(k), v
    except Exception:
        pass

    slots = getattr(type(obj), "__slots__", ())
    if isinstance(slots, str):
        slots = (slots,)
    for name in slots:
        if (not include_private) and str(name).startswith("_"):
            continue
        try:
            yield str(name), getattr(obj, name)
        except Exception:
            continue


def capture(direction="TB", title="AutoViz Snapshot", max_depth=4, max_nodes=300,
            include_private=False, prefer="plantuml",
            arrow_start="attribute", arrow_compass="auto",
            layout="auto", edge_routing="polyline"):
    """
    direction: "TB" top-bottom, "LR" left-right
    prefer: "plantuml" | "graphviz" | "pyvis" | "svg"
    arrow_start: "attribute" | "node"
    arrow_compass: "auto" | "center"
    layout: "auto" | "hierarchical" | "force" | "spring"
    edge_routing: "polyline" | "ortho" | "spline" | "line"
    """
    direction = str(direction).upper()
    if direction not in {"TB", "LR"}:
        direction = "TB"

    prefer = str(prefer).lower()
    if prefer not in {"plantuml", "pyvis", "graphviz", "svg"}:
        prefer = "plantuml"

    arrow_start = str(arrow_start).lower()
    if arrow_start not in {"attribute", "node"}:
        arrow_start = "attribute"

    arrow_compass = str(arrow_compass).lower()
    if arrow_compass not in {"auto", "center"}:
        arrow_compass = "auto"

    layout = str(layout).lower()
    if layout not in {"auto", "hierarchical", "force", "spring"}:
        layout = "auto"

    edge_routing = str(edge_routing).lower()
    if edge_routing not in {"polyline", "ortho", "spline", "line"}:
        edge_routing = "polyline"

    # 保留 max_depth 参数仅为兼容旧调用；当前按“直到成环/节点上限”为止展开
    max_depth = None
    try:
        max_nodes = max(1, int(max_nodes))
    except Exception:
        max_nodes = 300

    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        print("[auto_viz] 无法获取调用帧")
        return

    try:
        caller = frame.f_back
        root_scope = {
            "__locals__": dict(caller.f_locals),
            "__globals__": dict(caller.f_globals),
        }
        nodes, edges = _walk(root_scope, max_depth=max_depth, max_nodes=max_nodes,
                             include_private=include_private)
    finally:
        try:
            del caller
        except Exception:
            pass
        del frame

    if prefer == "svg":
        return _render_svg(nodes, edges, title, direction, arrow_start, arrow_compass, edge_routing)

    if prefer == "plantuml":
        if _has_plantuml:
            return _render_plantuml(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)
        if _has_graphviz:
            return _render_graphviz(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)
        if _has_pyvis:
            return _render_pyvis(nodes, edges, title)

    if prefer == "graphviz" and _has_graphviz:
        return _render_graphviz(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)
    if prefer == "pyvis" and _has_pyvis:
        return _render_pyvis(nodes, edges, title)

    if _has_plantuml:
        return _render_plantuml(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)
    if _has_graphviz:
        return _render_graphviz(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)
    if _has_pyvis:
        return _render_pyvis(nodes, edges, title)

    return _render_svg(nodes, edges, title, direction, arrow_start, arrow_compass, edge_routing)

    print("[auto_viz] 未找到渲染后端，下面是文本结构：")
    for n in nodes:
        print(n)
    for e in edges:
        print("  ", e)


def _walk(root_scope, max_depth, max_nodes, include_private):
    visited = set()
    nodes = []
    node_index = {}
    edges = []
    q = deque()

    def add_obj(obj, label, depth):
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
            "class_name": type(obj).__name__ if obj is not None else "NoneType",
            "is_class_object": _is_class_object(obj),
        }
        nodes.append(n)
        node_index[obj_id] = n
        q.append((obj, obj_id, depth))
        return obj_id

    # 直接提取作用域中的可渲染对象，不渲染 __locals__/__globals__ 节点
    for scope_name, scope_dict in root_scope.items():
        for k, v in scope_dict.items():
            if not include_private and str(k).startswith("_"):
                continue

            if scope_name == "__globals__":
                if inspect.ismodule(v) or inspect.isroutine(v) or inspect.isclass(v):
                    continue

            if not _is_renderable(v):
                continue

            child_label = f"{k} = {_short(v)}" if _is_primitive(v) else f"{k}: {_typename(v)}"
            add_obj(v, child_label, 1)

    while q:
        obj, obj_id, depth = q.popleft()
        if _is_terminal(obj):
            continue

        owner = node_index.get(obj_id)
        if owner is None or not owner.get("is_class_object"):
            continue

        try:
            for attr, val in _iter_object_items(obj, include_private):
                if _is_primitive(val):
                    owner["fields"].append(f"{attr} = {_short(val)}")
                    continue

                if not _is_class_object(val):
                    continue

                cid = add_obj(val, f"{attr}: {_typename(val)}", depth + 1)
                if cid is not None:
                    port = _safe_port(attr)
                    owner["refs"].append({"name": attr, "port": port})
                    edges.append({
                        "src": obj_id,
                        "dst": cid,
                        "label": attr,
                        "tail_port": port,
                    })
        except Exception:
            continue

    return nodes, edges


def _render_plantuml(nodes, edges, title, direction, arrow_start="attribute", arrow_compass="auto",
                     layout="auto", edge_routing="polyline"):
    uml_nodes = [n for n in nodes if n.get("is_class_object")]

    # PlantUML 对象图不支持属性端口锚点，要求从属性出发时改走 Graphviz。
    if arrow_start == "attribute" and uml_nodes and _has_graphviz:
        print("[auto_viz] PlantUML 不支持属性端口，已回退到 Graphviz(PNG)")
        return _render_graphviz(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)

    if not uml_nodes:
        if _has_graphviz:
            return _render_graphviz(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)
        if _has_pyvis:
            return _render_pyvis(nodes, edges, title)
        print("[auto_viz] 未找到可渲染的 class 对象")
        return None

    alias = {n["id"]: f"n{i+1}" for i, n in enumerate(uml_nodes)}

    lines = [
        "@startuml",
        f"title {title}",
        "skinparam shadowing false",
        "skinparam objectAttributeIconSize 0",
    ]
    if direction == "LR":
        lines.append("left to right direction")

    for n in uml_nodes:
        a = alias[n["id"]]
        cls = n.get("class_name") or "Object"

        lines.append(f'object "{cls}" as {a} {{')
        for f in n.get("fields", []):
            lines.append(f"  {f}")
        if not n.get("fields"):
            lines.append("  (no primitive fields)")
        lines.append("}")

    # 边不显示变量名，避免拥挤。
    for e in edges:
        s = alias.get(e.get("src"))
        d = alias.get(e.get("dst"))
        if s and d:
            lines.append(f"{s} --> {d}")

    lines.append("@enduml")
    puml_text = "\n".join(lines)

    fd, path = tempfile.mkstemp(suffix=".puml")
    os.close(fd)
    puml_path = Path(path)
    puml_path.write_text(puml_text, encoding="utf-8")

    if _has_plantuml:
        try:
            subprocess.run(
                ["plantuml", "-tpng", str(puml_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            png = puml_path.with_suffix(".png")
            if png.exists():
                webbrowser.open(png.as_uri())
                print(f"[auto_viz] PlantUML 输出：{png}")
                return png
        except Exception as e:
            print(f"[auto_viz] PlantUML 渲染失败：{e}")

    if _has_graphviz:
        print("[auto_viz] PlantUML 不可用，已回退到 Graphviz(PNG)")
        return _render_graphviz(nodes, edges, title, direction, arrow_start, arrow_compass, layout, edge_routing)

    webbrowser.open(puml_path.as_uri())
    print(f"[auto_viz] 无可用 PNG 后端，PlantUML 源码输出：{puml_path}")
    return puml_path


def _edge_compass(label: str, direction: str, arrow_compass: str) -> str:
    if arrow_compass == "center":
        return ""

    name = str(label).lower()
    if any(k in name for k in ("prev", "left", "last")):
        return "w"
    if any(k in name for k in ("next", "right", "succ")):
        return "e"
    if any(k in name for k in ("parent", "up", "top")):
        return "n"
    if any(k in name for k in ("child", "down", "bottom")):
        return "s"

    return "e" if direction == "LR" else "s"


def _edge_target_compass(label: str, direction: str, arrow_compass: str) -> str:
    if arrow_compass == "center":
        return ""

    name = str(label).lower()
    if any(k in name for k in ("prev", "left", "last")):
        return "e"
    if any(k in name for k in ("next", "right", "succ")):
        return "w"
    if any(k in name for k in ("parent", "up", "top")):
        return "s"
    if any(k in name for k in ("child", "down", "bottom")):
        return "n"

    return "w" if direction == "LR" else "n"


def _render_graphviz(nodes, edges, title, direction, arrow_start="attribute", arrow_compass="auto",
                     layout="auto", edge_routing="polyline"):
    engine_map = {
        "auto": "dot",
        "hierarchical": "dot",
        "force": "sfdp",
        "spring": "neato",
    }
    spline_map = {
        "polyline": "polyline",
        "ortho": "ortho",
        "spline": "spline",
        "line": "line",
    }

    dot = Digraph(comment=title, format="png", engine=engine_map.get(layout, "dot"))
    dot.attr(
        rankdir="TB" if direction == "TB" else "LR",
        bgcolor="white",
        nodesep="0.45",
        ranksep="0.75",
        splines=spline_map.get(edge_routing, "polyline"),
        dpi="220",
    )
    dot.attr(overlap="false", newrank="true", pack="true", packmode="clust", outputorder="edgesfirst")

    node_map = {n["id"]: n for n in nodes}

    for n in nodes:
        if n.get("is_class_object"):
            class_title = (n.get("class_name") or "Object").split(".")[-1]
            rows = [f'<TR><TD PORT="title" BGCOLOR="#dbe9ff"><B>{_gv_escape(class_title)}</B></TD></TR>']

            for f in n.get("fields", []):
                rows.append(f'<TR><TD ALIGN="LEFT">{_gv_escape(f)}</TD></TR>')
            for r in n.get("refs", []):
                rows.append(
                    f'<TR><TD ALIGN="LEFT" PORT="{_gv_escape(r["port"])}">'
                    f'{_gv_escape(r["name"])} &#8594;</TD></TR>'
                )

            if not n.get("fields") and not n.get("refs"):
                rows.append('<TR><TD ALIGN="LEFT"><I>(empty)</I></TD></TR>')

            label = (
                '<<TABLE BORDER="1" CELLBORDER="1" CELLPADDING="8" CELLSPACING="0" COLOR="#4a6fa5">'
                + "".join(rows)
                + "</TABLE>>"
            )
            dot.node(str(n["id"]), label=label, shape="plain")
            continue

        # 仅会命中基本类型节点
        dot.node(
            str(n["id"]),
            label=n["label"],
            shape="box",
            style="rounded,filled",
            fillcolor="#e8f0fe",
            color="#4a6fa5",
            penwidth="1.2",
            fontsize="12",
            margin="0.06,0.04",
        )

    for e in edges:
        src_node = node_map.get(e["src"])
        dst_node = node_map.get(e["dst"])
        label = e.get("label", "")
        lname = str(label).lower()

        src = str(e["src"])
        if arrow_start == "attribute" and e.get("tail_port") and src_node and src_node.get("is_class_object"):
            side = _edge_compass(label, direction, arrow_compass)
            src = f'{src}:{e["tail_port"]}{":" + side if side else ""}'

        dst = str(e["dst"])
        if dst_node and dst_node.get("is_class_object"):
            target_side = _edge_target_compass(label, direction, arrow_compass)
            dst = f"{dst}:title{':' + target_side if target_side else ''}"

        edge_kwargs = {
            "label": "",
            "color": "#4a6fa5",
            "penwidth": "1.4",
            "arrowsize": "0.8",
        }

        # 层次布局下对 next/prev 设不同约束，降低双向边互相拉扯。
        if layout in {"auto", "hierarchical"}:
            if any(k in lname for k in ("next", "right", "succ")):
                edge_kwargs["weight"] = "10"
                edge_kwargs["minlen"] = "2"
                edge_kwargs["constraint"] = "true"
            elif any(k in lname for k in ("prev", "left", "last")):
                edge_kwargs["weight"] = "2"
                edge_kwargs["constraint"] = "false"
                edge_kwargs["color"] = "#6a8bb8"
            elif e.get("tail_port"):
                edge_kwargs["constraint"] = "false"

        dot.edge(src, dst, **edge_kwargs)

    fd, path = tempfile.mkstemp(suffix=".gv")
    os.close(fd)
    source = Path(path)
    try:
        source.unlink(missing_ok=True)
    except Exception:
        pass

    out_path = Path(
        dot.render(
            filename=source.stem,
            directory=str(source.parent),
            cleanup=True,
            view=False,
        )
    )
    webbrowser.open(out_path.as_uri())
    print(f"[auto_viz] Graphviz 输出：{out_path}")
    return out_path


def _svg_text_width(text: str, px: int = 13) -> int:
    # 近似宽度，避免引入字体测量依赖
    return int(len(str(text)) * (px * 0.58))


def _svg_node_size(node):
    if node.get("is_class_object"):
        title_h = 32
        row_h = 24
        fields = node.get("fields", [])
        refs = node.get("refs", [])
        display_fields = fields if fields else ["(no primitive fields)"]
        display_refs = refs if refs else [{"name": "(no refs)", "port": "_none"}]

        w = 260
        w = max(w, _svg_text_width(node.get("class_name") or "Object", 14) + 44)
        for f in display_fields:
            w = max(w, _svg_text_width(f, 12) + 40)
        for r in display_refs:
            w = max(w, _svg_text_width(f"{r.get('name', 'ref')} ->", 12) + 40)

        h = title_h + row_h * len(display_fields) + row_h * len(display_refs)
        return {"w": w, "h": h, "title_h": title_h, "row_h": row_h,
                "display_fields": display_fields, "display_refs": display_refs}

    label = node.get("label", "")
    w = max(150, _svg_text_width(label, 12) + 30)
    return {"w": w, "h": 34}


def _layout_svg_nodes(nodes, edges, direction):
    ids = [n["id"] for n in nodes]
    by_id = {n["id"]: n for n in nodes}
    indeg = {nid: 0 for nid in ids}
    adj = {nid: [] for nid in ids}
    for e in edges:
        s, d = e.get("src"), e.get("dst")
        if s in adj and d in indeg:
            adj[s].append(d)
            indeg[d] += 1

    rank = {nid: 0 for nid in ids}
    indeg_work = dict(indeg)
    q = deque([nid for nid in ids if indeg_work[nid] == 0])
    seen = set()
    while q:
        u = q.popleft()
        seen.add(u)
        for v in adj.get(u, []):
            rank[v] = max(rank.get(v, 0), rank.get(u, 0) + 1)
            indeg_work[v] -= 1
            if indeg_work[v] == 0:
                q.append(v)

    if len(seen) < len(ids):
        max_rank = max(rank.values(), default=0)
        for nid in ids:
            if nid not in seen:
                max_rank += 1
                rank[nid] = max_rank

    layers = {}
    for nid in ids:
        layers.setdefault(rank[nid], []).append(nid)

    for r, bucket in layers.items():
        layers[r] = sorted(bucket, key=lambda x: str(by_id[x].get("label", "")))

    margin = 40
    rank_gap = 340
    item_gap = 78
    pos = {}
    geom = {}
    max_x = margin
    max_y = margin

    for r in sorted(layers.keys()):
        cursor = margin
        for nid in layers[r]:
            n = by_id[nid]
            size = _svg_node_size(n)
            if direction == "LR":
                x = margin + r * rank_gap
                y = cursor
                cursor += size["h"] + item_gap
            else:
                x = cursor
                y = margin + r * rank_gap
                cursor += size["w"] + item_gap

            pos[nid] = (x, y)
            g = {"x": x, "y": y, **size, "ports": {}}
            if n.get("is_class_object"):
                py = y + size["title_h"]
                for _f in size["display_fields"]:
                    py += size["row_h"]
                for ref in size["display_refs"]:
                    g["ports"][ref.get("port", "_none")] = py + size["row_h"] / 2
                    py += size["row_h"]
            geom[nid] = g
            max_x = max(max_x, x + size["w"])
            max_y = max(max_y, y + size["h"])

    return geom, max_x + margin, max_y + margin


def _svg_anchor(geom, side, y_hint=None):
    x, y, w, h = geom["x"], geom["y"], geom["w"], geom["h"]
    cx, cy = x + w / 2, y + h / 2
    if side == "e":
        return x + w, y_hint if y_hint is not None else cy
    if side == "w":
        return x, y_hint if y_hint is not None else cy
    if side == "n":
        return cx, y
    if side == "s":
        return cx, y + h
    return cx, cy


def _svg_edge_points(sx, sy, dx, dy, direction, edge_routing):
    if edge_routing in {"line", "spline"}:
        return [(sx, sy), (dx, dy)]

    if abs(dx - sx) < 12 and abs(dy - sy) < 12:
        return [(sx, sy), (sx + 24, sy - 24), (sx + 48, sy), (dx, dy)]

    if direction == "LR":
        mx = (sx + dx) / 2
        return [(sx, sy), (mx, sy), (mx, dy), (dx, dy)]
    my = (sy + dy) / 2
    return [(sx, sy), (sx, my), (dx, my), (dx, dy)]


def _render_svg(nodes, edges, title, direction, arrow_start="attribute", arrow_compass="auto", edge_routing="polyline"):
    node_map = {n["id"]: n for n in nodes}
    geom, canvas_w, canvas_h = _layout_svg_nodes(nodes, edges, direction)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(canvas_w)}" height="{int(canvas_h)}" viewBox="0 0 {int(canvas_w)} {int(canvas_h)}">',
        "<defs>",
        "<marker id=\"arrow\" markerWidth=\"10\" markerHeight=\"8\" refX=\"9\" refY=\"4\" orient=\"auto\" markerUnits=\"strokeWidth\">",
        "<path d=\"M0,0 L10,4 L0,8 z\" fill=\"#4a6fa5\"/>",
        "</marker>",
        "</defs>",
        "<rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"white\"/>",
        f'<text x="20" y="28" font-family="Consolas, monospace" font-size="18" fill="#1f2d3d">{_gv_escape(title)}</text>',
    ]

    # 先画边，避免压住节点内容
    for e in edges:
        src = node_map.get(e.get("src"))
        dst = node_map.get(e.get("dst"))
        if src is None or dst is None:
            continue
        gs = geom.get(e["src"])
        gd = geom.get(e["dst"])
        if gs is None or gd is None:
            continue

        source_side = ""
        y_hint = None
        if arrow_start == "attribute" and src.get("is_class_object") and e.get("tail_port"):
            source_side = _edge_compass(e.get("label", ""), direction, arrow_compass)
            y_hint = gs["ports"].get(e.get("tail_port"))
        sx, sy = _svg_anchor(gs, source_side, y_hint)

        target_side = ""
        if dst.get("is_class_object"):
            target_side = _edge_target_compass(e.get("label", ""), direction, arrow_compass)
        dx, dy = _svg_anchor(gd, target_side)

        pts = _svg_edge_points(sx, sy, dx, dy, direction, edge_routing)
        point_text = " ".join(f"{round(px, 2)},{round(py, 2)}" for px, py in pts)
        lines.append(
            f'<polyline points="{point_text}" fill="none" stroke="#4a6fa5" stroke-width="1.6" marker-end="url(#arrow)"/>'
        )

    for n in nodes:
        g = geom[n["id"]]
        x, y, w, h = g["x"], g["y"], g["w"], g["h"]
        if n.get("is_class_object"):
            lines.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" ry="6" fill="#ffffff" stroke="#4a6fa5" stroke-width="1.4"/>'
            )
            lines.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{g["title_h"]}" rx="6" ry="6" fill="#dbe9ff" stroke="#4a6fa5" stroke-width="1.0"/>'
            )
            lines.append(
                f'<text x="{x + 12}" y="{y + 21}" font-family="Consolas, monospace" font-size="14" fill="#1f2d3d">{_gv_escape((n.get("class_name") or "Object"))}</text>'
            )

            py = y + g["title_h"]
            for f in g["display_fields"]:
                lines.append(f'<line x1="{x}" y1="{py}" x2="{x + w}" y2="{py}" stroke="#d0dbef" stroke-width="1"/>')
                lines.append(
                    f'<text x="{x + 10}" y="{py + 16}" font-family="Consolas, monospace" font-size="12" fill="#243447">{_gv_escape(f)}</text>'
                )
                py += g["row_h"]

            for r in g["display_refs"]:
                lines.append(f'<line x1="{x}" y1="{py}" x2="{x + w}" y2="{py}" stroke="#d0dbef" stroke-width="1"/>')
                lines.append(
                    f'<text x="{x + 10}" y="{py + 16}" font-family="Consolas, monospace" font-size="12" fill="#2f4f7f">{_gv_escape(str(r.get("name", "ref")) + " ->")}</text>'
                )
                py += g["row_h"]
        else:
            lines.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" ry="6" fill="#e8f0fe" stroke="#4a6fa5" stroke-width="1.2"/>'
            )
            lines.append(
                f'<text x="{x + 10}" y="{y + 22}" font-family="Consolas, monospace" font-size="12" fill="#243447">{_gv_escape(n.get("label", ""))}</text>'
            )

    lines.append("</svg>")
    svg_text = "\n".join(lines)

    fd, path = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    out_path = Path(path)
    out_path.write_text(svg_text, encoding="utf-8")
    webbrowser.open(out_path.as_uri())
    print(f"[auto_viz] SVG 输出：{out_path}")
    return out_path


def _render_pyvis(nodes, edges, title):
    net = Network(height="880px", width="100%", directed=True, notebook=False)
    net.set_options("""
    {
      "nodes": {
        "font": {"size": 18, "face": "Consolas"},
        "margin": 12
      },
      "edges": {
        "font": {"size": 14},
        "width": 2,
        "smooth": {"enabled": true, "type": "bezier"}
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -5000,
          "springLength": 95,
          "springConstant": 0.02,
          "damping": 0.28,
          "avoidOverlap": 1
        }
      }
    }
    """)

    for n in nodes:
        lines = [n["label"]]
        lines.extend(n.get("fields", []))
        lines.extend([f'{r["name"]} ->' for r in n.get("refs", [])])
        label = "\n".join(lines)

        net.add_node(
            n["id"],
            label=label,
            title=n["type"],
            shape="box",
            color="#e8f0fe",
            borderWidth=2,
            widthConstraint={"minimum": 220},
        )

    # PyVis 保留不显示边标签，和 Graphviz 保持一致。
    for e in edges:
        net.add_edge(e["src"], e["dst"], label="", color="#4a6fa5", width=2)

    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    html_path = Path(path)

    net.write_html(str(html_path), open_browser=False, notebook=False)
    webbrowser.open(html_path.as_uri())
    print(f"[auto_viz] PyVis 交互式 HTML 输出：{html_path}")
    return html_path
