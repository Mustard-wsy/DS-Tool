"""Card renderer — converts DSVis graph data to G6-compatible format.

Also handles HTML generation (``render_debugger()``).
"""

import json
import tempfile
import webbrowser
from pathlib import Path


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

def build_g6_data(nodes, edges, layout=None):
    """Convert internal graph representation to G6 card format.

    Returns ``{"nodes": [...], "edges": [...]}``.
    """
    g6_data: dict = {"nodes": [], "edges": []}

    rankdir = "LR"
    if layout and isinstance(layout, dict):
        rankdir = layout.get("rankdir", "LR")

    is_vertical = rankdir == "TB"

    id_to_name: dict[str, str] = {}
    class_count: dict[str, int] = {}

    padding_x = 10
    padding_y = 8
    row_h = 18
    default_header_h = 22
    section_gap = 6
    min_card_w = 100
    max_card_w = 280
    char_px = 6.0

    for n in nodes:
        cls = n.get("class_name") or "Obj"
        class_count[cls] = class_count.get(cls, 0) + 1
        name = n.get("label") or f"{cls}#{class_count[cls]}"
        id_to_name[str(n["id"])] = name

        rows = n.get("rows", [])
        raw_header_lines = str(name).splitlines() or [str(name)]
        candidate_lengths = [len(line) for line in raw_header_lines]
        candidate_lengths.extend(len(str(r.get("text", ""))) for r in rows)
        max_len = max(candidate_lengths) if candidate_lengths else 0

        target_w = int(padding_x * 2 + max_len * char_px + 12)
        card_w = max(min_card_w, min(max_card_w, target_w))
        max_chars = max(10, int((card_w - padding_x * 2 - 6) / char_px))

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
        header_h = max(default_header_h, header_line_count * 16)

        height = padding_y * 2 + header_h + max(len(display_rows), 1) * row_h

        # ---------- ports ----------
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
        else:
            header_center_y = (padding_y + header_h / 2) / height
            ports = [
                {"key": "inL", "placement": [0, header_center_y], "r": 0, "fill": "transparent", "stroke": "transparent"},
                {"key": "inR", "placement": [1, header_center_y], "r": 0, "fill": "transparent", "stroke": "transparent"},
            ]
            for row_idx in ref_row_indices:
                y = (padding_y + header_h + row_idx * row_h + row_h / 2) / height
                ports.append({"key": f"pl{row_idx}", "placement": [0, y], "r": 0, "fill": "transparent", "stroke": "transparent"})
                ports.append({"key": f"pr{row_idx}", "placement": [1, y], "r": 0, "fill": "transparent", "stroke": "transparent"})

        g6_data["nodes"].append({
            "id": str(n["id"]),
            "type": "card",
            "style": {
                "size": [card_w, height],
                "name": display_name,
                "headerHeight": header_h,
                "rows": display_rows,
                "rowBindGroups": bind_groups,
                "rowBindBlocks": bind_blocks,
                "refRowIndices": ref_row_indices,
                "refLabelMap": ref_label_map,
                "sectionGap": section_gap,
                "ports": ports,
            },
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

        g6_data["edges"].append({
            "id": f"e{edge_counter}",
            "source": src_id,
            "target": dst_id,
            "data": {"refIndex": ref_idx},
            "style": {},
        })
        edge_counter += 1

    return g6_data


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def render_debugger(steps, source_lines, title="DSVis Debugger", layout=None, display_indices=None):
    """Generate a self-contained HTML debugger page and open it in a browser.

    *display_indices* is an optional list of indices into *steps* that
    should be visible in the UI (step counter, Prev/Next).  All steps are
    still available for breakpoint / line navigation.
    """
    from .dsvis import _normalize_layout  # deferred — avoids circular import
    from .runtime.config import breakpoints_enabled

    if display_indices is None:
        display_indices = list(range(len(steps)))

    normalized_layout = _normalize_layout(layout)
    step_payload = []
    for idx, step in enumerate(steps, start=1):
        step_payload.append({
            "step": idx,
            "lineno": step.get("lineno"),
            "stack": step.get("stack", {"globals": [], "frames": []}),
            "graph": build_g6_data(step.get("nodes", []), step.get("edges", []), normalized_layout),
        })

    template_path = Path(__file__).parent / "template.html"
    styles_path = Path(__file__).parent / "styles.css"
    html = template_path.read_text(encoding="utf-8")
    styles = styles_path.read_text(encoding="utf-8")
    html = html.replace("__TITLE__", title)
    html = html.replace("__STYLES__", styles)
    html = html.replace("__STEPS__", json.dumps(step_payload, ensure_ascii=False))
    html = html.replace("__SOURCE_LINES__", json.dumps(source_lines, ensure_ascii=False))
    html = html.replace("__LAYOUT__", json.dumps(normalized_layout))
    html = html.replace("__BREAKPOINTS_ENABLED__", json.dumps(breakpoints_enabled()))
    html = html.replace("__DISPLAY_INDICES__", json.dumps(display_indices))

    fd, path = tempfile.mkstemp(suffix=".html")
    html_path = Path(path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(html_path.as_uri())
    print(f"[dsvis] HTML 输出：{html_path}")
    return html_path
