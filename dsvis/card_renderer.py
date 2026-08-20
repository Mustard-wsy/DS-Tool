"""Card renderer — converts DSVis graph data to G6-compatible format.

Also handles HTML generation (``render_debugger()``).
"""

import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

# Local style server (see runtime/style_server.py). Fixed port so a running
# server is reused across script runs; the frontend persists styles to
# <cwd>/.dsvis/<script>.json instead of the browser's localStorage on C:.
STYLE_SERVER_PORT = 8765


def _read_style_config(source_file):
    """Load the persisted per-script style from <cwd>/.dsvis/<stem>.json."""
    if not source_file:
        return None
    style_file = Path.cwd() / ".dsvis" / f"{Path(source_file).stem}.json"
    if not style_file.exists():
        return None
    try:
        return json.loads(style_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _port_open(port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_http(port: int, path: str = "/ping", timeout: float = 1.5) -> bool:
    """True if a DSVis-style HTTP server responds 204 on GET <path>.

    Verifying with an actual request (not just a TCP connect) prevents a
    non-DSVis process squatting on the port from being mistaken for ours.
    """
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
            s.sendall(f"GET {path} HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n".encode("ascii"))
            s.settimeout(timeout)
            first = s.recv(64).decode("latin-1", "replace")
            return " 204" in first.split("\r\n", 1)[0]
    except Exception:
        return False


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_server_on_port(port: int) -> bool:
    """Launch a detached style server on *port* and wait for /ping to answer."""
    try:
        server_script = Path(__file__).resolve().parent / "runtime" / "style_server.py"
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.Popen(
            [sys.executable, str(server_script), "--port", str(port)],
            cwd=str(Path.cwd()),
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            if _probe_http(port):
                return True
            time.sleep(0.1)
    except Exception:
        pass
    return False


def _ensure_style_server():
    """Return a reachable DSVis style-server port (reusing a live one or
    starting a detached server), else None.

    - Reuses the default port only if a live DSVis server answers /ping.
    - If the default port is squatted by a non-DSVis process, starts the server
      on a random free high port instead.
    - Any failure degrades gracefully to None (the frontend falls back to
      localStorage for style persistence).
    """
    if _probe_http(STYLE_SERVER_PORT):
        return STYLE_SERVER_PORT
    if _port_open(STYLE_SERVER_PORT):
        # Squatted by something else — use a random free port.
        port = _find_free_port()
        return port if _start_server_on_port(port) else None
    return STYLE_SERVER_PORT if _start_server_on_port(STYLE_SERVER_PORT) else None
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
    # Average rendered width per char for the card fonts (11-12px). 6.0 was
    # too small — G6 renders ~6.8-7.5px/char, so wrapped lines still overflowed
    # the card. 7.0 is a safe upper bound.
    char_px: float = 7.0


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
        if self.title_col_w is not None:
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
            # Side ports for "sidePort" pointer edges (e.g. B+Tree next sibling
            # links): left/right midpoints so such edges can leave from the sides.
            {"key": "sL", "placement": [0, 0.5], "r": 0, "fill": "transparent", "stroke": "transparent"},
            {"key": "sR", "placement": [1, 0.5], "r": 0, "fill": "transparent", "stroke": "transparent"},
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
    candidate_lengths.extend(len(str(r.get("text", ""))) for r in rows)
    max_len = max(candidate_lengths) if candidate_lengths else 0

    target_w = int(text_cfg.padding_x * 2 + max_len * text_cfg.char_px + 12)
    card_w = max(text_cfg.min_card_w, min(text_cfg.max_card_w, target_w))
    max_chars = max(10, int((card_w - text_cfg.padding_x * 2 - 6) / text_cfg.char_px))

    header_lines = _wrap_multiline(name, max_chars)
    display_name = "\n".join(header_lines)

    # The type-name subtitle is wrapped to the card width too, so a long class
    # / structure-type name wraps instead of overflowing the card ("跑出格子").
    subtitle_lines = _wrap_multiline(subtitle_text, max_chars) if subtitle_text else []

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
    if subtitle_lines:
        header_h += len(subtitle_lines) * 14
    height = text_cfg.padding_y * 2 + header_h + max(len(display_rows), 1) * text_cfg.row_h

    return (card_w, height, header_h, display_name,
            display_rows, bind_groups, bind_blocks,
            ref_row_indices, ref_label_map, subtitle_lines)




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
    # Wrap the title to a capped column width so a long line (e.g. a class name
    # rendered as "field\n(SomeVeryLongType)", parens already in the label)
    # never overflows the title cell. char_px is the average rendered char
    # width, so the wrapped longest line fits inside the column.
    title_cap = 160
    init_max_chars = max(4, int((title_cap - 12) / text_cfg.char_px))
    wrapped_title = _wrap_multiline(name, init_max_chars)
    longest_wrapped = max(len(l) for l in wrapped_title)
    title_col_w = max(60, min(160, int(longest_wrapped * text_cfg.char_px + 12)))
    display_name = "\n".join(wrapped_title)

    # Split each row into (name, value, is_ref)
    field_defs = []
    for row in rows:
        text = str(row.get("text", ""))
        is_ref = row.get("kind") == "ref"
        fname, fval = _parse_vertical_field(text, is_ref)
        field_defs.append((fname, fval, is_ref, text))

    # column widths
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
            [],  # subtitle_lines (vertical grid does not render a subtitle)
            title_col_w, field_col_w, grid_names, grid_values, grid_refs)



def _layout_node(name, rows, subtitle_text, text_flow, text_cfg):
    """Dispatch card layout by text flow direction."""
    if text_flow == "vertical":
        return _layout_vertical_node(name, rows, subtitle_text, text_cfg)
    return _layout_horizontal_node(name, rows, subtitle_text, text_cfg)


def build_g6_data(nodes, edges, layout=None, text_flow="horizontal", field_visibility=None):
    """Convert internal graph representation to G6 card format.

    *text_flow* sets the default text flow for all cards ("horizontal" | "vertical").

    *field_visibility* is the ``get_field_visibility()`` dict
    (``"ClassName.fieldName" -> "visible"|"self"|"cascade"``).  When a node's
    ``__title__`` pseudo-field is hidden, the vertical layout collapses the
    title column by serializing ``titleColW: 0`` instead of the natural
    header width — so the generated payload is self-consistent with the
    initial visibility (the frontend also recomputes it defensively).
    """
    g6_data: dict = {"nodes": [], "edges": []}

    rankdir = "LR"
    if layout and isinstance(layout, dict):
        rankdir = layout.get("rankdir", "LR")

    is_vertical = rankdir == "TB"
    text_cfg = TextLayoutConfig()
    field_visibility = field_visibility or {}

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
        subtitle_lines = layout_result[9] if len(layout_result) > 9 else []
        # Vertical grid extras (unpacked only when present)
        grid_extras = layout_result[10:] if len(layout_result) > 10 else ()

        # Collapse the title column when the backend knows the title is hidden.
        # This only affects vertical-grid nodes (horizontal cards carry no grid extras).
        title_col_w = grid_extras[0] if len(grid_extras) > 0 else 0
        title_hidden = field_visibility.get(f"{cls}.__title__") in ("self", "cascade")
        if title_hidden and len(grid_extras) > 0:
            title_col_w = 0
            # Keep the card width self-consistent: drop the title column width.
            field_col_w = grid_extras[1] if len(grid_extras) > 1 else 0
            num_fields = max(len(grid_extras[2]) if len(grid_extras) > 2 else 0, 1)
            card_w = max(text_cfg.min_card_w,
                         text_cfg.padding_x * 2 + title_col_w + num_fields * field_col_w)

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
            # Store the wrapped (multi-line) subtitle so the frontend renders a
            # long class / structure-type name on multiple lines instead of
            # letting a single G6 text run past the card edge.
            subtitle="\n".join(subtitle_lines) if subtitle_lines else subtitle_text,
            text_flow=text_flow,
            title_col_w=title_col_w,
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

def render_debugger(steps, source_lines, title="DSVis Debugger", layout=None, display_indices=None, source_file=None):
    """Generate a self-contained HTML debugger page and open it in a browser.

    Layout contract
    ---------------
    *layout* is normalised once via :func:`dsvis._normalize_layout` and
    embedded as ``__LAYOUT__``.  The frontend consumes this value as-is;
    there is no second normalisation pass.

    Style persistence
    -----------------
    *source_file* (the user script being visualised) selects the per-script
    style file ``<cwd>/.dsvis/<stem>.json``.  When present it is embedded as
    ``__STYLE_CONFIG__`` so the page opens with the previously saved style;
    ``__STYLE_SERVER__`` carries the localhost port the frontend uses to save
    styles back to that file (never the browser's localStorage on C:).

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
    from .graph_viewer import build_graph_viewer_data
    from .runtime.config import breakpoints_enabled, get_text_flow, get_field_visibility

    # breakpoints state is a pure presentation hint for the frontend —
    # the scheduler already decided recording policy before reaching here.
    if display_indices is None:
        display_indices = list(range(len(steps)))

    text_flow = get_text_flow()
    normalized_layout = _normalize_layout(layout)
    step_payload = []
    for idx, step in enumerate(steps, start=1):
        step_nodes = step.get("nodes", [])
        step_edges = step.get("edges", [])
        step_payload.append({
            "step": idx,
            "lineno": step.get("lineno"),
            "stack": step.get("stack", {"globals": [], "frames": []}),
            "graph": build_g6_data(
                step_nodes,
                step_edges,
                normalized_layout,
                text_flow,
                field_visibility=get_field_visibility(),
            ),
            # Independent graph-displayer payload (structureType='graph').
            "graphView": build_graph_viewer_data(step_nodes, step_edges),
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

    # Style persistence: embed the saved style (if any) and the local style
    # server port so the page can load + persist per-script styles to disk.
    style_config = _read_style_config(source_file)
    style_port = _ensure_style_server()
    style_server = None
    if style_port is not None:
        style_server = {"port": style_port}
        if source_file:
            style_server["script"] = Path(source_file).name
    html = html.replace("__STYLE_CONFIG__", json.dumps(style_config, ensure_ascii=False))
    html = html.replace("__STYLE_SERVER__", json.dumps(style_server, ensure_ascii=False))

    # ── Output location ──
    # Default: write a stable, shareable self-contained page to
    # <cwd>/.dsvis/out/<script-stem>.html, overwriting on each run, so the user
    # can double-click / share / refresh the same file. Falls back to a temp
    # file when the project directory is not writable.
    html_path = None
    try:
        out_dir = Path.cwd() / ".dsvis" / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(source_file).stem if source_file else "dsvis"
        html_path = out_dir / f"{stem}.html"
        html_path.write_text(html, encoding="utf-8")
    except Exception:
        html_path = None
    if html_path is None:
        fd, path = tempfile.mkstemp(suffix=".html")
        html_path = Path(path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    # ── Open the page ──
    # Server mode (default): serve via the local style server so the browser
    # loads it over http:// (no file:// restrictions, PageAgent works, style
    # persistence is same-origin). Falls back to file:// when no server is up
    # or the server does not support /view (e.g. an older process on the port).
    http_url = None
    if style_port:
        stem = Path(source_file).stem if source_file else "dsvis"
        candidate = f"http://127.0.0.1:{style_port}/view/{stem}.html"
        try:
            import urllib.request
            with urllib.request.urlopen(candidate, timeout=2) as _resp:
                if _resp.status == 200:
                    http_url = candidate
        except Exception:
            http_url = None
    if http_url:
        webbrowser.open(http_url)
        print(f"[dsvis] HTML 输出：{http_url}")
    else:
        webbrowser.open(html_path.as_uri())
        print(f"[dsvis] HTML 输出：{html_path}")
    return html_path
