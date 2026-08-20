"""Graph viewer data — a self-contained "graph displayer" transformer.

This module is deliberately independent from the card renderer.  It turns the
generic ``(nodes, edges)`` produced by :mod:`dsvis.graph_builder` into a
minimal, self-describing graph-view payload that a plain graph viewer can draw
directly::

    {
      "nodes":   [{"id": "…", "value": "…", "index": 0}, …],
      "edges":   [{"source": "…", "target": "…", "value": "…"}, …],
      "undirected": true|false,
    }

Node semantics
--------------
- **Edge objects** (e.g. an ``Edge(to, weight)``) are not rendered as nodes;
  they become directed graph edges with an optional value (weight).
- **Vertices** are the class objects that form the graph (referenced by a
  vertex collection or by another vertex/edge).  A vertex's displayed value is
  its primary scalar field, falling back to its traversal-order index.
- **Everything else** (the root graph container, helper objects, isolated
  objects) is ignored.

Direction
---------
An edge set is treated as **undirected** only when every directed edge has a
symmetric mirror carrying the *same* value; otherwise it is directed.  For
undirected graphs the symmetric pair is collapsed into a single edge.
"""

import re

# A plain (non-container-indexed) ref attribute whose name marks an "edge
# object" — the bridge object that connects two vertices (e.g. Edge.to).
_EDGE_REF_NAMES = {"to", "v", "target", "end", "dest", "node"}

# Priority order used to extract a scalar value from field rows.
_VERTEX_VALUE_FIELDS = ("value", "val", "data", "key", "id", "name", "label")
_EDGE_VALUE_FIELDS = ("weight", "w", "cost", "dist", "value", "len")

_INDEXED = re.compile(r".*\[\d+\]$")
_FIELD_TEXT = re.compile(r"^([^=]+)=\s*(.*)$")


def _plain_ref_names(node):
    """Ref names that are not container-indexed (e.g. ``edges[0]``)."""
    out = []
    for r in node.get("refs", []):
        name = str(r.get("name", ""))
        if not _INDEXED.match(name):
            out.append(name)
    return out


def _is_edge_object(node):
    """A class object with a single plain ref in EDGE_REF_NAMES is a bridge."""
    if not node.get("refs"):
        return False
    return any(name in _EDGE_REF_NAMES for name in _plain_ref_names(node))


def _clean_scalar(text):
    """Strip repr quoting from a scalar value string (``'A'`` → ``A``)."""
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        text = text[1:-1]
    return text


def _scalar_fields(node):
    """Return an ordered ``{field_name: scalar_value}`` map of a node's rows."""
    scalar = {}
    for r in node.get("rows", []):
        if r.get("kind") != "field":
            continue
        text = str(r.get("text", "")).strip()
        name = str(r.get("name", "")).strip()
        m = _FIELD_TEXT.match(text)
        if m:
            name = m.group(1).strip()
            scalar[name] = _clean_scalar(m.group(2))
        elif name:
            scalar[name] = _clean_scalar(text)
    return scalar


def _scalar_field_value(node, prefer=None):
    """Extract a scalar value string from a node's field rows.

    Returns ``None`` when no scalar field exists.  ``prefer`` is an ordered
    tuple of field names tried first (used for edge objects' weight).
    """
    scalar = _scalar_fields(node)
    if prefer:
        for f in prefer:
            if f in scalar:
                return scalar[f]
    for f in _VERTEX_VALUE_FIELDS:
        if f in scalar:
            return scalar[f]
    if scalar:
        return next(iter(scalar.values()))
    return None


def _is_undirected(edges):
    """Undirected iff every directed edge has a same-value symmetric mirror."""
    seen = {(e["source"], e["target"], e["value"]) for e in edges}
    for a, b, v in seen:
        if (b, a, v) not in seen:
            return False
    return True


def build_graph_viewer_data(nodes, edges):
    """Transform generic BFS ``(nodes, edges)`` into the graph-view payload."""
    nodes = list(nodes or [])
    edges = list(edges or [])
    by_id = {str(n["id"]): n for n in nodes}
    incoming: dict[str, list[str]] = {}
    for e in edges:
        incoming.setdefault(str(e.get("dst")), []).append(str(e.get("src")))

    # ── classify ──
    edge_object_ids = {str(n["id"]) for n in nodes if _is_edge_object(n)}
    vertex_ids = [
        str(n["id"]) for n in nodes
        if str(n["id"]) not in edge_object_ids and incoming.get(str(n["id"]))
    ]
    index_of = {nid: i for i, nid in enumerate(vertex_ids)}

    out_nodes = []
    for i, nid in enumerate(vertex_ids):
        node = by_id[nid]
        value = _scalar_field_value(node)
        out_nodes.append({
            "id": nid,
            "value": value if value is not None else i,
            "index": i,
            # Scalar field names on the vertex — lets the UI offer a
            # "value field" override without re-classifying in the frontend.
            "fields": list(_scalar_fields(node).keys()),
        })

    # ── resolve each edge object to (source vertex → target vertex, value) ──
    # Find, for every edge object, the single vertex it points to.
    edge_obj_target: dict[str, str | None] = {}
    edge_obj_value: dict[str, str | None] = {}
    for nid in edge_object_ids:
        node = by_id.get(nid)
        if not node:
            continue
        target = None
        for ref in node.get("refs", []):
            if str(ref.get("name", "")) in _EDGE_REF_NAMES:
                # match the BFS edge leaving this object under that ref name
                for e in edges:
                    if str(e.get("src")) == nid and str(e.get("label", "")) == str(ref.get("name", "")):
                        target = str(e.get("dst"))
                        break
                if target:
                    break
        edge_obj_target[nid] = target
        edge_obj_value[nid] = _scalar_field_value(node, prefer=_EDGE_VALUE_FIELDS) if target else None

    # ── build graph edges ──
    g_edges = []
    for e in edges:
        src, dst = str(e.get("src")), str(e.get("dst"))
        if dst in edge_object_ids:
            # vertex → edge object → target vertex (edge value = object's weight)
            tgt = edge_obj_target.get(dst)
            if tgt and src in index_of and tgt in index_of:
                edge_obj = by_id.get(dst) or {}
                g_edges.append({
                    "source": src, "target": tgt, "value": edge_obj_value.get(dst),
                    "edgeId": dst,
                    "fields": list(_scalar_fields(edge_obj).keys()),
                })
        else:
            if src in index_of and dst in index_of:
                g_edges.append({"source": src, "target": dst, "value": None, "edgeId": None, "fields": []})

    # ── direction + undirected collapse ──
    undirected = _is_undirected(g_edges)
    if undirected:
        collapsed: dict[tuple, dict] = {}
        for e in g_edges:
            key = tuple(sorted((e["source"], e["target"])))
            collapsed[key] = e  # keep the last representative
        g_edges = list(collapsed.values())

    return {"nodes": out_nodes, "edges": g_edges, "undirected": undirected}
