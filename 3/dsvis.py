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
    # 转换数据格式
    g6_data = {
        "nodes": [],
        "edges": []
    }

    id_to_name = {}
    class_count = {}

    # 卡片布局参数（与前端一致）
    padding_x = 10
    padding_y = 8
    row_h = 18
    header_h = 22
    section_gap = 6
    card_w = 300

    for n in nodes:
        cls = n.get("class_name") or "Obj"
        class_count[cls] = class_count.get(cls, 0) + 1
        name = f"{cls}{class_count[cls]}"
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

        # 端口：左右入点 + 每个指针行左右各一个出点
        ports = [
            {"key": "inL", "placement": [0, 0.5], "r": 2.5, "fill": "#5b8ff9", "stroke": "#2b6cd4"},
            {"key": "inR", "placement": [1, 0.5], "r": 2.5, "fill": "#5b8ff9", "stroke": "#2b6cd4"},
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

    # 预计算每个节点的指针名称 -> 索引
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
            "style": {
            }
        }
        edge_counter += 1
        g6_data["edges"].append(edge_item)

    # 🔥 使用稳定布局（关键）
    layout = {
        "type": "dagre",
        "rankdir": "LR",   # 左→右（链表非常清晰）
        "nodesep": 30,
        "ranksep": 100
    }

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
  html, body, #container {{
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
  }}
  #fallback {{
    position: absolute;
    top: 12px;
    left: 12px;
    padding: 8px 10px;
    background: #fff3cd;
    border: 1px solid #ffeeba;
    color: #856404;
    font-family: Consolas, monospace;
    font-size: 12px;
    display: none;
    z-index: 10;
  }}
</style>
<script src="https://unpkg.com/@antv/g6@5.0.51/dist/g6.min.js"></script>
</head>

<body style="margin:0">
<div id="fallback">G6 加载失败或渲染出错（请检查控制台错误）。</div>
<div id="container"></div>

<script>
const data = {json.dumps(g6_data)};
const fallback = document.getElementById('fallback');

function showFallback(err) {{
  fallback.style.display = 'block';
  if (err && err.message) {{
    fallback.textContent = 'G6 渲染错误: ' + err.message;
  }}
}}

try {{
  if (!window.G6) {{
    showFallback(new Error('G6 未加载'));
  }} else {{
    // 自定义“分栏卡片”节点（G6 v5）
    const {{ register, BaseNode }} = G6;
    class CardNode extends BaseNode {{
      drawKeyShape(attributes, container) {{
        const name = attributes.name || '';
        const fields = Array.isArray(attributes.fields) ? attributes.fields : [];
        const refs = Array.isArray(attributes.refs) ? attributes.refs : [];
        const size = attributes.size || [300, 80];
        const width = size[0];
        const height = size[1];

        const paddingX = 10;
        const paddingY = 8;
        const rowH = 18;
        const headerH = 22;
        const sectionGap = attributes.sectionGap || 6;
        const labelW = width - paddingX * 2;

        const keyShape = this.upsert('key', 'rect', {{
          x: -width / 2,
          y: -height / 2,
          width,
          height,
          radius: 4,
          fill: '#e8f0fe',
          stroke: '#5b8ff9',
        }}, container);

        this.upsert('header-bg', 'rect', {{
          x: -width / 2,
          y: -height / 2,
          width,
          height: headerH + paddingY,
          fill: '#dbe7ff',
          stroke: 'transparent',
          radius: 4,
        }}, container);

        this.upsert('header-text', 'text', {{
          x: -width / 2 + paddingX,
          y: -height / 2 + paddingY + 2,
          text: name,
          fill: '#000',
          fontSize: 12,
          fontFamily: 'Consolas, monospace',
          textBaseline: 'top',
        }}, container);

        const fieldRows = Math.max(fields.length, 1);
        const refRows = refs.length;

        // fields (top section)
        for (let i = 0; i < fieldRows; i++) {{
          const y = -height / 2 + headerH + paddingY + i * rowH + 2;
          const text = fields[i] || '';
          if (text) {{
            this.upsert(`field-${{i}}`, 'text', {{
              x: -width / 2 + paddingX,
              y,
              text,
              fill: '#1a1a1a',
              fontSize: 11,
              fontFamily: 'Consolas, monospace',
              textBaseline: 'top',
            }}, container);
          }}
        }}

        // divider between fields and refs
        if (refRows > 0) {{
          const divY = -height / 2 + headerH + paddingY + fieldRows * rowH + sectionGap / 2;
          this.upsert('divider', 'line', {{
            x1: -width / 2 + paddingX,
            y1: divY,
            x2: width / 2 - paddingX,
            y2: divY,
            stroke: '#c3d4ff',
          }}, container);
        }}

        // refs (bottom section)
        for (let i = 0; i < refRows; i++) {{
          const y = -height / 2 + headerH + paddingY + fieldRows * rowH + sectionGap + i * rowH + 2;
          const text = refs[i] || '';
          if (text) {{
            this.upsert(`ref-${{i}}`, 'text', {{
              x: -width / 2 + paddingX,
              y,
              text,
              fill: '#1a1a1a',
              fontSize: 11,
              fontFamily: 'Consolas, monospace',
              textBaseline: 'top',
            }}, container);
          }}

          // port hints on both sides for pointer rows
          const portY = y + 6;
        }}

        return keyShape;
      }}
    }}
    register('node', 'card', CardNode);

    const graph = new G6.Graph({{
      container: 'container',
      width: window.innerWidth,
      height: window.innerHeight,
      autoResize: true,
      data,

      layout: {json.dumps(layout)},

      node: {{
        type: 'card',
        style: {{
          fill: '#e8f0fe',
          stroke: '#5b8ff9',
          radius: 4,
          label: false,
          port: true
        }}
      }},

      edge: {{
        style: {{
          stroke: '#999',
          endArrow: true,
          router: {{
            type: 'polyline'
          }}
        }}
      }},

      behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element'],

      transforms: ['process-parallel-edges']
    }});

    graph.render();

    // 根据相对位置切换指针端口左右
    function updateEdgePorts() {{
        const updates = [];
        const edges = graph.getEdgeData();

        for (const e of edges) {{
            const src = graph.getNodeData(e.source);
            const tgt = graph.getNodeData(e.target);
            if (!src || !tgt) continue;

            const refIndex = e.data ? e.data.refIndex : null;
            if (refIndex === null || refIndex === undefined) continue;

            // 获取节点位置
            const sx = src.style?.x ?? 0;
            const tx = tgt.style?.x ?? 0;

            // 👇 关键：只在当前 refIndex 的左右 port 之间切换
            const useLeft = tx < sx;

            const sourcePort = useLeft
            ? `pl${{refIndex}}`   // 该字段的左端口
            : `pr${{refIndex}}`;  // 该字段的右端口

            const targetPort = useLeft ? 'inR' : 'inL';

            updates.push({{
            id: e.id,
            style: {{
                sourcePort,
                targetPort
            }}
            }});
        }}

        graph.updateEdgeData(updates);
        }}

    graph.on('afterlayout', updateEdgePorts);
    graph.on('node:dragend', updateEdgePorts);
  }}
}} catch (err) {{
  console.error(err);
  showFallback(err);
}}
</script>
</body>
</html>
"""

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


