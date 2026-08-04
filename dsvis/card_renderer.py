"""Card renderer — converts DSVis graph data to G6-compatible format.

Also handles HTML generation (``render_debugger()``).
"""

import base64
import json
import tempfile
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
def _load_codicon_styles() -> str:
    """Return codicon CSS with the font embedded as a data URI.

    The generated HTML is opened from a temporary directory, so we cannot
    rely on relative ``url(...)`` references inside the upstream CSS.
    """
    root = Path(__file__).resolve().parents[1]
    css_path = root / "node_modules" / "@vscode" / "codicons" / "dist" / "codicon.css"
    ttf_path = root / "node_modules" / "@vscode" / "codicons" / "dist" / "codicon.ttf"
    if not css_path.is_file() or not ttf_path.is_file():
        return ""
    css = css_path.read_text(encoding="utf-8")
    font_data = base64.b64encode(ttf_path.read_bytes()).decode("ascii")
    font_url = f"data:font/ttf;base64,{font_data}"
    css = css.replace("url(\"./codicon.ttf?721d4c0a96379d0c13d3d5596893c348\")", f"url('{font_url}')")
    css += "\n.icon-btn .codicon, .edge-toggle .codicon, .pane-toggle .codicon { font-size: 18px; line-height: 1; }\n"
    return css



# ---------------------------------------------------------------------------
# Node style system
# ---------------------------------------------------------------------------

@dataclass
class TextLayoutConfig:
    """Pixel-level text layout constants for card rendering.

    These are the *source of truth* for all card dimension calculations.
    The frontend currently also hardcodes its own copies; future work
    should make it consume these from the node style payload.
    """
    padding_x: int = 10
    padding_y: int = 8
    row_h: int = 18
    default_header_h: int = 22
    section_gap: int = 6
    min_card_w: int = 100
    max_card_w: int = 280
    char_px: float = 6.0


@dataclass
class PortLayoutDescriptor:
    """Data-driven port naming so ``resolvePortsForEdge`` in JS doesn't branch on rankdir.

    ``entry``:  [port_when_target_is_right_or_below,  port_when_target_is_left_or_above]
    ``ref``:    per-ref-row  [port_when_source_is_right_or_below,  port_when_source_is_left_or_above]
    """
    direction: str            # "LR" | "TB"
    entry: list[str]          # len=2, ordered [positive, negative]
    ref: list[dict] = field(default_factory=list)  # [{"idx": 3, "ports": ["pr3","pl3"]}, ...]


@dataclass
class NodeStyle:
    """All visual metadata for a single G6 card node.

    Serialized via ``to_dict()`` into the ``style`` block that
    ``CardNode.drawKeyShape`` and ``resolvePortsForEdge`` consume.
    """
    size: tuple[int, int]
    name: str
    header_height: int
    rows: list[str]
    row_bind_groups: list
    row_bind_blocks: list
    ref_row_indices: list[int]
    ref_label_map: dict
    section_gap: int
    ports: list[dict]
    port_layout: PortLayoutDescriptor | None = None
    show_subtitle: bool = False
    subtitle: str | None = None
    text_flow: str = "horizontal"  # "horizontal" | "vertical" (future)
    row_names: list = field(default_factory=list)
    row_kinds: list = field(default_factory=list)
    row_field_keys: list = field(default_factory=list)
    # Vertical grid layout fields
    title_col_w: int = 0
    field_col_w: int = 0
    grid_names: list = field(default_factory=list)
    grid_values: list = field(default_factory=list)
    grid_refs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "size": list(self.size),
            "name": self.name,
            "headerHeight": self.header_height,
            "rows": self.rows,
            "rowNames": self.row_names,
            "rowKinds": self.row_kinds,
            "rowFieldKeys": self.row_field_keys,
            "rowBindGroups": self.row_bind_groups,
            "rowBindBlocks": self.row_bind_blocks,
            "refRowIndices": self.ref_row_indices,
            "refLabelMap": self.ref_label_map,
            "sectionGap": self.section_gap,
            "ports": self.ports,
            "className": self.subtitle if self.show_subtitle and self.subtitle else "",
        }
        # Only emit textFlow when it differs from the default (horizontal).
        # This lets the frontend's VIS_CONFIG switch between layouts.
        if self.text_flow != "horizontal":
            d["textFlow"] = self.text_flow
        if self.port_layout is not None:
            d["portLayout"] = {
                "direction": self.port_layout.direction,
                "entry": self.port_layout.entry,
                "ref": self.port_layout.ref,
            }
        if self.show_subtitle and self.subtitle:
            d["showSubtitle"] = True
            d["subtitle"] = self.subtitle
        if self.title_col_w:
            d["titleColW"] = self.title_col_w
            d["fieldColW"] = self.field_col_w
            d["gridNames"] = self.grid_names
            d["gridValues"] = self.grid_values
            d["gridRefs"] = self.grid_refs
        return d


# ---------------------------------------------------------------------------
# Text-wrapping helpers
# ---------------------------------------------------------------------------

def _wrap_line(text, max_chars):
    """Split a single line into chunks of at most *max_chars*."""
    if max_chars <= 0:
        return [text]
    if len(text) <= max_chars:
        return [text]
    out = []
    cursor = 0
    while cursor < len(text):
        out.append(text[cursor : cursor + max_chars])
        cursor += max_chars
    return out


def _wrap_multiline(text, max_chars):
    """Wrap each line of *text* to *max_chars* columns."""
    lines = str(text).splitlines() or [str(text)]
    wrapped = []
    for line in lines:
        wrapped.extend(_wrap_line(line, max_chars))
    return wrapped or [""]


# ---------------------------------------------------------------------------
# G6 card builder
# ---------------------------------------------------------------------------

def _build_ports(*, is_vertical, ref_row_indices, header_h, height, text_cfg):
    """Return (ports_list, port_layout_descriptor)."""
    ports = []
    ref_entries = []
    direction = "TB" if is_vertical else "LR"

    if is_vertical:
        num_ref_rows = len(ref_row_indices)
        header_center_x = 0.5
        ports = [
            {"key": "inT", "placement": [header_center_x, 0], "r": 0, "fill": "transparent", "stroke": "transparent"},
            {"key": "inB", "placement": [header_center_x, 1], "r": 0, "fill": "transparent", "stroke": "transparent"},
        ]
        for i, row_idx in enumerate(ref_row_indices):
            if num_ref_rows > 1:
                x = 0.1 + (0.8 * i / (num_ref_rows - 1))
            else:
                x = 0.5
            ports.append({"key": f"pt{row_idx}", "placement": [x, 0], "r": 0, "fill": "transparent", "stroke": "transparent"})
            ports.append({"key": f"pb{row_idx}", "placement": [x, 1], "r": 0, "fill": "transparent", "stroke": "transparent"})
            ref_entries.append({"idx": row_idx, "ports": [f"pb{row_idx}", f"pt{row_idx}"]})
        port_layout = PortLayoutDescriptor(
            direction="TB",
            entry=["inT", "inB"],
            ref=ref_entries,
        )
    else:
        header_center_y = (text_cfg.padding_y + header_h / 2) / height
        ports = [
            {"key": "inL", "placement": [0, header_center_y], "r": 0, "fill": "transparent", "stroke": "transparent"},
            {"key": "inR", "placement": [1, header_center_y], "r": 0, "fill": "transparent", "stroke": "transparent"},
        ]
        for row_idx in ref_row_indices:
            y = (text_cfg.padding_y + header_h + row_idx * text_cfg.row_h + text_cfg.row_h / 2) / height
            ports.append({"key": f"pl{row_idx}", "placement": [0, y], "r": 0, "fill": "transparent", "stroke": "transparent"})
            ports.append({"key": f"pr{row_idx}", "placement": [1, y], "r": 0, "fill": "transparent", "stroke": "transparent"})
            ref_entries.append({"idx": row_idx, "ports": [f"pr{row_idx}", f"pl{row_idx}"]})
        port_layout = PortLayoutDescriptor(
            direction="LR",
            entry=["inL", "inR"],
            ref=ref_entries,
        )

    return ports, port_layout


def _layout_horizontal_node(name, rows, subtitle_text, text_cfg):
    """Horizontal text flow: compute card dimensions and row layout.

    Returns ``(card_w, height, header_h, display_name, display_rows,
    bind_groups, bind_blocks, ref_row_indices, ref_label_map)``.
    """
    raw_header_lines = str(name).splitlines() or [str(name)]
    candidate_lengths = [len(line) for line in raw_header_lines]

    if subtitle_text:
        subtitle_lines = _wrap_multiline(subtitle_text, 999)
        candidate_lengths.extend(len(line) for line in subtitle_lines)
    else:
        subtitle_lines = []

    candidate_lengths.extend(len(str(r.get("text", ""))) for r in rows)
    max_len = max(candidate_lengths) if candidate_lengths else 0

    target_w = int(text_cfg.padding_x * 2 + max_len * text_cfg.char_px + 12)
    card_w = max(text_cfg.min_card_w, min(text_cfg.max_card_w, target_w))
    max_chars = max(10, int((card_w - text_cfg.padding_x * 2 - 6) / text_cfg.char_px))

    header_lines = _wrap_multiline(name, max_chars)
    display_name = "\n".join(header_lines)

    display_rows = []
    bind_groups = []
    bind_blocks = []
    ref_row_indices = []
    ref_label_map = {}

    for row in rows:
        text = str(row.get("text", ""))
        wrapped_lines = _wrap_multiline(text, max_chars)
        visual_start = len(display_rows)
        for line in wrapped_lines:
            display_rows.append(line)
            bind_groups.append(row.get("bind_group"))
            bind_blocks.append(row.get("bind_block"))
        if row.get("kind") == "ref":
            ref_row_indices.append(visual_start)
            if text not in ref_label_map:
                ref_label_map[text] = visual_start

    header_line_count = max(1, len(header_lines))
    header_h = max(text_cfg.default_header_h, header_line_count * 16)
    if subtitle_text:
        header_h += 14
    height = text_cfg.padding_y * 2 + header_h + max(len(display_rows), 1) * text_cfg.row_h

    return card_w, height, header_h, display_name, display_rows, bind_groups, bind_blocks, ref_row_indices, ref_label_map




def _parse_vertical_field(text, is_ref):
    """Parse row text into (field_name, field_value) for vertical table view."""
    raw = str(text or '').strip()
    if not raw:
        return '', ''

    if ' = ' in raw and not is_ref:
        k, v = raw.split(' = ', 1)
        return k.strip(), v.strip()

    for sep in (' -> ', ': ', '=>', '→'):
        if sep in raw:
            k, v = raw.split(sep, 1)
            return k.strip(), ('' if is_ref else v.strip())

    if is_ref and ' ' in raw:
        return raw.split(' ', 1)[0].strip(), ''

    return raw, '' if is_ref else raw

def _layout_vertical_node(name, rows, subtitle_text, text_cfg):
    """Vertical grid layout: title column + field-name/value grid rows.

    Card structure:
        ┌──────────┬────────┬────────┬──────────┐
        │  Title   │ name_0 │ name_1 │ name_2   │  ← header row
        │          │ val_0  │ val_1  │ val_2    │  ← data row
        └──────────┴────────┴────────┴──────────┘
    Title spans both rows vertically. Ref rows show name only (data cell empty).
    """
    raw_header_lines = str(name).splitlines() or [str(name)]
    display_name = "\n".join(raw_header_lines)

    # Split each row into (name, value, is_ref)
    field_defs = []
    for row in rows:
        text = str(row.get("text", ""))
        is_ref = row.get("kind") == "ref"
        fname, fval = _parse_vertical_field(text, is_ref)
        field_defs.append((fname, fval, is_ref, text))

    # column widths
    title_col_w = int(max(len(line) for line in raw_header_lines) * text_cfg.char_px + 12)
    title_col_w = max(60, min(160, title_col_w))

    field_col_w = 16
    if field_defs:
        for fname, fval, _, _raw_text in field_defs:
            w = max(len(fname), len(fval)) * text_cfg.char_px + 12
            field_col_w = max(field_col_w, int(w))
    field_col_w = max(50, min(120, field_col_w))

    num_fields = max(len(field_defs), 1)
    card_w = max(text_cfg.min_card_w,
                 text_cfg.padding_x * 2 + title_col_w + num_fields * field_col_w)

    # card height: 2 grid rows
    grid_row_h = 20
    card_h = text_cfg.padding_y * 2 + 2 * grid_row_h

    # grid data for frontend
    grid_names = [f[0] for f in field_defs]
    grid_values = [f[1] for f in field_defs]
    grid_refs = [i for i, f in enumerate(field_defs) if f[2]]

    # build display_rows for backward compat
    display_rows = [str(r.get("text", "")) for r in rows]
    bind_groups = [r.get("bind_group") for r in rows]
    bind_blocks = [r.get("bind_block") for r in rows]
    ref_row_indices = grid_refs[:]
    ref_label_map = {}
    for i in grid_refs:
        t = str(rows[i].get("text", ""))
        if t not in ref_label_map:
            ref_label_map[t] = i

    header_h = 0  # unused in grid mode

    return (card_w, card_h, header_h, display_name,
            display_rows, bind_groups, bind_blocks,
            ref_row_indices, ref_label_map,
            title_col_w, field_col_w, grid_names, grid_values, grid_refs)



def _layout_node(name, rows, subtitle_text, text_flow, text_cfg):
    """Dispatch card layout by text flow direction."""
    if text_flow == "vertical":
        return _layout_vertical_node(name, rows, subtitle_text, text_cfg)
    return _layout_horizontal_node(name, rows, subtitle_text, text_cfg)


def build_g6_data(nodes, edges, layout=None, text_flow="horizontal"):
    """Convert internal graph representation to G6 card format.

    *text_flow* sets the default text flow for all cards ("horizontal" | "vertical").
    """
    g6_data: dict = {"nodes": [], "edges": []}

    rankdir = "LR"
    if layout and isinstance(layout, dict):
        rankdir = layout.get("rankdir", "LR")

    is_vertical = rankdir == "TB"
    text_cfg = TextLayoutConfig()

    id_to_name: dict[str, str] = {}
    class_count: dict[str, int] = {}

    for n in nodes:
        cls = n.get("class_name") or "Obj"
        class_count[cls] = class_count.get(cls, 0) + 1
        name = n.get("label") or f"{cls}#{class_count[cls]}"
        id_to_name[str(n["id"])] = name

        rows = n.get("rows", [])
        subtitle_text = cls if n.get("is_class_object") else None

        # ── text-flow dispatch: layout card dimensions + rows ──
        layout_result = _layout_node(
            name=name, rows=rows, subtitle_text=subtitle_text,
            text_flow=text_flow, text_cfg=text_cfg,
        )
        (card_w, height, header_h, display_name,
         display_rows, bind_groups, bind_blocks,
         ref_row_indices, ref_label_map) = layout_result[:9]
        # Vertical grid extras (unpacked only when present)
        grid_extras = layout_result[9:] if len(layout_result) > 9 else ()

        # ── ports + port layout descriptor ──
        use_vertical_ports = is_vertical or (text_flow == "vertical")
        ports, port_layout = _build_ports(
            is_vertical=use_vertical_ports,
            ref_row_indices=ref_row_indices,
            header_h=header_h,
            height=height,
            text_cfg=text_cfg,
        )

        # Field keys follow the backend contract (graph_builder._make_field_key).
        # The renderer passes them through without re-normalising the prefix.
        node_style = NodeStyle(
            size=(card_w, height),
            name=display_name,
            header_height=header_h,
            rows=display_rows,
            row_names=[str(r.get("name", "")) for r in rows],
            row_kinds=[str(r.get("kind", "field")) for r in rows],
            row_field_keys=[str(r.get("field_key", "")) for r in rows],
            row_bind_groups=bind_groups,
            row_bind_blocks=bind_blocks,
            ref_row_indices=ref_row_indices,
            ref_label_map=ref_label_map,
            section_gap=text_cfg.section_gap,
            ports=ports,
            port_layout=port_layout,
            show_subtitle=bool(subtitle_text),
            subtitle=subtitle_text,
            text_flow=text_flow,
            title_col_w=grid_extras[0] if len(grid_extras) > 0 else 0,
            field_col_w=grid_extras[1] if len(grid_extras) > 1 else 0,
            grid_names=grid_extras[2] if len(grid_extras) > 2 else [],
            grid_values=grid_extras[3] if len(grid_extras) > 3 else [],
            grid_refs=grid_extras[4] if len(grid_extras) > 4 else [],
        )

        g6_data["nodes"].append({
            "id": str(n["id"]),
            "type": "card",
            "style": node_style.to_dict(),
        })

    # ---------- edges ----------
    ref_index = {}
    for n in g6_data["nodes"]:
        style = n.get("style") or {}
        ref_rows = style.get("refRowIndices", [])
        rows = style.get("rows", [])
        mapping = style.get("refLabelMap") if isinstance(style.get("refLabelMap"), dict) else {}
        if not mapping:
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

        edge_data = {"refIndex": ref_idx, "label": label}
        fk = e.get("field_key")
        if fk is not None:
            edge_data["field_key"] = fk
        g6_data["edges"].append({
            "id": f"e{edge_counter}",
            "source": src_id,
            "target": dst_id,
            "data": edge_data,
            "style": {},
        })
        edge_counter += 1

    return g6_data


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def _derive_algorithm_name(source_lines, title):
    """Derive a human-readable algorithm name from source code heuristics."""
    source = "\n".join(source_lines) if source_lines else ""
    source_lower = source.lower()

    # Class-name heuristics: look for tree / heap / graph classes
    import re
    class_match = re.search(r'class\s+(\w*(?:Tree|Heap|Graph|Hash|Sort|List|Queue|Stack|Union|Find|DSU|Huffman|Prim|Kruskal|DFS|BFS|SCC|Topo)\w*)', source)
    if class_match:
        return class_match.group(1)

    # Keyword heuristics
    if 'avl' in source_lower and ('rotate' in source_lower or 'balance_factor' in source_lower):
        return 'AVL'
    if 'red_black' in source_lower or 'rb_tree' in source_lower or ('color' in source_lower and 'rotate' in source_lower and 'black' in source_lower):
        return 'RBTree'
    if 'b_plus_tree' in source_lower or 'bptree' in source_lower or 'BPlusTree' in source:
        return 'BPlusTree'
    if 'btree' in source_lower or 'b_tree' in source_lower or 'BTree' in source:
        return 'BTree'
    if 'binary_heap' in source_lower or 'binheap' in source_lower or ('heap' in source_lower and 'sift' in source_lower):
        return 'BinaryHeap'
    if 'huffman' in source_lower or 'huff' in source_lower:
        return 'Huffman'
    if 'prim' in source_lower and ('mst' in source_lower or 'minimum_spanning' in source_lower):
        return 'Prim'
    if 'dfs' in source_lower and 'bfs' in source_lower:
        return 'DFS/BFS'
    if 'dfs' in source_lower:
        return 'DFS'
    if 'bfs' in source_lower:
        return 'BFS'
    if 'scc' in source_lower or 'strongly_connected' in source_lower or 'tarjan' in source_lower or 'kosaraju' in source_lower:
        return 'SCC'
    if 'topo' in source_lower or 'topological' in source_lower:
        return 'TopologicalSort'
    if 'dsu' in source_lower or 'disjoint' in source_lower or 'union_find' in source_lower:
        return 'DSU'
    if 'bubble_sort' in source_lower or 'bubblesort' in source_lower:
        return 'BubbleSort'
    if 'merge_sort' in source_lower or 'mergesort' in source_lower:
        return 'MergeSort'
    if 'hash_open' in source_lower or 'open_addressing' in source_lower:
        return 'HashOpenAddressing'
    if 'hash_closed' in source_lower or 'closed_addressing' in source_lower or 'separate_chaining' in source_lower:
        return 'HashClosedAddressing'
    if 'hanoi' in source_lower or 'tower_of_hanoi' in source_lower:
        return 'HanoiTower'
    if 'gcd' in source_lower and ('euclid' in source_lower or 'gcd' in source_lower):
        return 'GCD'
    if 'priority_queue' in source_lower or 'priorityqueue' in source_lower:
        return 'PriorityQueue'
    if 'stack' in source_lower and ('push' in source_lower or 'pop' in source_lower):
        return 'Stack'
    if 'queue' in source_lower and 'enq' in source_lower:
        return 'Queue'
    if 'palindrome' in source_lower:
        return 'Palindrome'

    # Fallback: extract from title (strips "DSVis Debugger" prefix)
    if title and title != 'DSVis Debugger':
        clean = title.replace('DSVis Debugger', '').replace('(', '').replace(')', '').strip()
        if clean:
            return clean

    return 'Algorithm'

def render_debugger(steps, source_lines, title="DSVis Debugger", layout=None, display_indices=None):
    """Generate a self-contained HTML debugger page and open it in a browser.

    Layout contract
    ---------------
    *layout* is normalised once via :func:`dsvis._normalize_layout` and
    embedded as ``__LAYOUT__``.  The frontend consumes this value as-is;
    there is no second normalisation pass.

    Step payload contract
    ---------------------
    Each raw *step* dict (``lineno``, ``nodes``, ``edges``, ``stack``,
    ``_visible``) is transformed here into a display-step payload
    (``step``, ``lineno``, ``stack``, ``graph``).  *display_indices*
    (computed by the scheduler) selects which display steps are visible
    in the UI — all steps remain available for breakpoint / line
    navigation.
    """
    from .dsvis import _normalize_layout  # deferred — avoids circular import
    from .runtime.config import breakpoints_enabled, get_text_flow, get_field_visibility

    # breakpoints state is a pure presentation hint for the frontend —
    # the scheduler already decided recording policy before reaching here.
    if display_indices is None:
        display_indices = list(range(len(steps)))

    text_flow = get_text_flow()
    normalized_layout = _normalize_layout(layout)
    step_payload = []
    for idx, step in enumerate(steps, start=1):
        step_payload.append({
            "step": idx,
            "lineno": step.get("lineno"),
            "stack": step.get("stack", {"globals": [], "frames": []}),
            "graph": build_g6_data(step.get("nodes", []), step.get("edges", []), normalized_layout, text_flow),
        })

    template_path = Path(__file__).parent / "template.html"
    styles_path = Path(__file__).parent / "styles.css"
    g6_path = Path(__file__).parent / "g6.min.js"
    html = template_path.read_text(encoding="utf-8")
    styles = styles_path.read_text(encoding="utf-8")
    g6_js = g6_path.read_text(encoding="utf-8") if g6_path.exists() else ""
    codicon_styles = _load_codicon_styles()
    if codicon_styles:
        styles = f"{codicon_styles}\n{styles}"
    html = html.replace("__TITLE__", title)
    html = html.replace("__STYLES__", styles)
    html = html.replace("__G6_JS__", g6_js)
    html = html.replace("__DSVIS_ALGO__", json.dumps(_derive_algorithm_name(source_lines, title)))
    html = html.replace("__STEPS__", json.dumps(step_payload, ensure_ascii=False))
    html = html.replace("__SOURCE_LINES__", json.dumps(source_lines, ensure_ascii=False))
    html = html.replace("__LAYOUT__", json.dumps(normalized_layout))
    html = html.replace("__BREAKPOINTS_ENABLED__", json.dumps(breakpoints_enabled()))
    html = html.replace("__DISPLAY_INDICES__", json.dumps(display_indices))
    html = html.replace("__INITIAL_VISIBILITY__", json.dumps(get_field_visibility(), ensure_ascii=False))

    fd, path = tempfile.mkstemp(suffix=".html")
    html_path = Path(path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(html_path.as_uri())
    print(f"[dsvis] HTML 输出：{html_path}")
    return html_path
