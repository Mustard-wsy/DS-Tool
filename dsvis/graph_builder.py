"""Graph builder — BFS traversal of runtime objects.

Responsibilities
---------------
- Row-append helpers: construct field rows and ref rows with canonical
  ``TypeName::fieldName`` keys (``_make_field_key``).
- Bind-group resolution: ``_resolve_object_fields()`` owns the animation
  policy that interleaves bound container fields.
- Traversal: ``walk_graph()`` scans the root scope, processes pointer
  watchers, and runs a BFS loop that delegates field resolution per object.

The main entry point is ``walk_graph()`` which takes a root scope dict and
returns ``(nodes, edges)`` ready for the card renderer.
"""

from collections import deque

from .introspection import (
    format_typed_label,
    is_class_object,
    is_container,
    is_graph_root_value,
    is_primitive,
    is_renderable,
    iter_container_items,
    iter_object_items,
    short,
    typename,
)
from .field_binding import get_bound_specs, get_instance_bound_specs


# ---------------------------------------------------------------------------
# Row-append helpers (used during field resolution)
# ---------------------------------------------------------------------------

def _owner_field_prefix(owner):
    """Stable field-key prefix used by UI presets and user settings.

    Prefer the bare class name over the fully qualified runtime type because
    scripts may run as ``__main__`` during visualization but as an imported
    module during tests.
    """
    return owner.get('class_name') or owner.get('type', '')


def _make_field_key(owner, item_name):
    """Canonical ``TypeName::fieldName`` key shared across backend and frontend.

    This is the single backend path for constructing field keys.  Both
    ``card_renderer.py`` and ``template.html`` consume this format without
    re-normalising the prefix.
    """
    return f"{_owner_field_prefix(owner)}::{item_name}"


def _append_field(owner, item_name, item_val, *, bind_group=None, bind_block=None):
    """Append a plain (non-ref) row."""
    field_key = _make_field_key(owner, item_name)
    row = {"name": item_name, "kind": "field",
           "text": f"{item_name} = {short(item_val)}",
           "field_key": field_key}
    if bind_group is not None:
        row["bind_group"] = bind_group
    if bind_block is not None:
        row["bind_block"] = bind_block
    owner["rows"].append(row)


def _append_ref_or_field(item_name, item_val, owner, obj_id, nodes, edges,
                         visited, max_nodes, include_containers, _add_obj,
                         *, bind_group=None, bind_block=None):
    """Ref (→ child node) or plain field, depending on type."""
    if is_class_object(item_val):
        cid = _add_obj(item_val, format_typed_label(item_name, item_val))
        if cid:
            field_key = _make_field_key(owner, item_name)
            row = {"name": item_name, "kind": "ref", "text": item_name, "field_key": field_key}
            if bind_group is not None:
                row["bind_group"] = bind_group
            if bind_block is not None:
                row["bind_block"] = bind_block
            owner["rows"].append(row)
            owner["refs"].append({"name": item_name, "field_key": field_key})
            edges.append({"src": obj_id, "dst": cid, "label": item_name, "field_key": field_key})
        else:
            _append_field(owner, item_name, item_val,
                          bind_group=bind_group, bind_block=bind_block)
    else:
        _append_field(owner, item_name, item_val,
                      bind_group=bind_group, bind_block=bind_block)


# ---------------------------------------------------------------------------
# Bind-group field resolution (post-processing step)
# ---------------------------------------------------------------------------

def _resolve_object_fields(owner, obj, item_map, obj_id,
                           nodes, edges, visited, max_nodes,
                           include_containers, _add_obj):
    """Post-processing: bind-group animation + unbound fields for *obj*."""
    bind_groups = get_bound_specs(obj)
    instance_specs = get_instance_bound_specs(obj)
    for group_name, mapping in instance_specs.items():
        bind_groups.setdefault(group_name, {}).update(mapping)
    bound_fields = set()
    for mapping in bind_groups.values():
        bound_fields.update(mapping.keys())

    # Track which bound fields were actually handled by a bind-group block.
    # Non-container bound fields (e.g. tree node references) can't be animated
    # and must fall through to unbound processing instead of being silently
    # dropped.
    actually_bound: set[str] = set()

    # ---------- bind-group animation blocks ----------
    for group_name, mapping in bind_groups.items():
        ordered_fields = [attr for attr in mapping.keys() if attr in item_map]
        if len(ordered_fields) < 2:
            continue
        bound_streams = {}
        for attr in ordered_fields:
            val = item_map.get(attr)
            if not isinstance(val, (list, tuple, set, frozenset, dict, deque)):
                continue
            bound_streams[attr] = {
                "ratio": mapping.get(attr, 1),
                "items": list(iter_container_items(attr, val)),
                "cursor": 0,
            }
        if len(bound_streams) < 2:
            continue
        for attr in ordered_fields:
            if attr in bound_streams:
                actually_bound.add(attr)
        block_index = 0
        progressed = True
        while progressed:
            progressed = False
            for attr in ordered_fields:
                stream = bound_streams.get(attr)
                if not stream:
                    continue
                take = stream["ratio"]
                while take > 0 and stream["cursor"] < len(stream["items"]):
                    item_name, item_val = stream["items"][stream["cursor"]]
                    _append_ref_or_field(
                        item_name, item_val, owner, obj_id, nodes, edges,
                        visited, max_nodes, include_containers, _add_obj,
                        bind_group=group_name,
                        bind_block=f"{group_name}#{block_index}",
                    )
                    stream["cursor"] += 1
                    take -= 1
                    progressed = True
            if progressed:
                block_index += 1

    # ---------- unbound fields ----------
    for attr, val in item_map.items():
        if attr in actually_bound:
            continue
        if is_primitive(val):
            _append_field(owner, attr, val)
        elif isinstance(val, (list, tuple, set, frozenset, dict, deque)):
            items = list(iter_container_items(attr, val))
            # Non-empty containers are expanded into `X[i]` rows only — no
            # aggregate row (the expanded items fully represent the content).
            # Empty containers keep an aggregate row (e.g. ``keys = []``) so
            # the field stays visible/identifiable in the graph and panel.
            if not items:
                _append_field(owner, attr, val)
                continue
            for item_name, item_val in items:
                _append_ref_or_field(item_name, item_val, owner, obj_id,
                                     nodes, edges, visited, max_nodes,
                                     include_containers, _add_obj)
        elif is_class_object(val):
            _append_ref_or_field(attr, val, owner, obj_id,
                                 nodes, edges, visited, max_nodes,
                                 include_containers, _add_obj)


def walk_graph(
    root_scope,
    max_nodes=300,
    include_private=False,
    include_containers=False,
    focus_vars=None,
    pointer_watchers=None,
):
    """BFS traversal of live objects reachable from *root_scope*.

    Returns ``(nodes, edges)``.
    """
    visited: set[int] = set()
    nodes: list[dict] = []
    edges: list[dict] = []
    node_index: dict[int, dict] = {}
    q = deque()
    focus_vars = set(focus_vars or [])
    pointer_watchers = list(pointer_watchers or [])

    # ------------------------------------------------------------------
    # nested helpers
    # ------------------------------------------------------------------

    def _add_pointer_node(pointer_name, container_name, pointer_value, text):
        node_id = f"ptr:{pointer_name}->{container_name}:{len(nodes)}"
        n = {
            "id": node_id,
            "label": f"{pointer_name} -> {container_name}",
            "type": "Pointer",
            "rows": [{"name": "value", "kind": "field", "text": text, "field_key": f"Pointer::value"}],
            "refs": [],
            "class_name": "Pointer",
            "is_class_object": False,
        }
        if pointer_value is not None:
            n["rows"].append({
                "name": "index",
                "kind": "field",
                "text": f"index = {short(pointer_value)}",
                "field_key": f"Pointer::index",
            })
        nodes.append(n)

    def _add_obj(obj, label, value_text=None, force_render=False):
        if not force_render and not is_renderable(obj, include_containers=include_containers):
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
            "type": typename(obj),
            "rows": [],
            "refs": [],
            # Avoid truthiness checks here: bool(obj) may call user __len__
            # while objects are still being initialized.
            "class_name": type(obj).__name__ if obj is not None else "NoneType",
            "is_class_object": is_class_object(obj),
        }
        if value_text is not None:
            n["rows"].append({"name": "value", "kind": "field", "text": value_text, "field_key": f"{n.get('class_name') or n.get('type', '')}::value"})
        nodes.append(n)
        node_index[obj_id] = n

        if is_container(obj):
            items = list(iter_container_items("item", obj))
            n["rows"].append({
                "name": "summary",
                "kind": "field",
                "text": f"size = {len(items)}",
                "field_key": f"{n.get('class_name') or n.get('type', '')}::summary",
            })
            for item_name, item_val in items[:12]:
                if is_primitive(item_val):
                    n["rows"].append({
                        "name": item_name,
                        "kind": "field",
                        "text": f"{item_name} = {short(item_val)}",
                        "field_key": f"{n.get('class_name') or n.get('type', '')}::{item_name}",
                    })
                elif is_class_object(item_val):
                    cid = _add_obj(item_val, format_typed_label(item_name, item_val))
                    if cid:
                        field_key = f"{n.get('class_name') or n.get('type', '')}::{item_name}"
                        n["rows"].append({
                            "name": item_name,
                            "kind": "ref",
                            "text": item_name,
                            "field_key": field_key,
                        })
                        n["refs"].append({"name": item_name, "field_key": field_key})
                        edges.append({"src": obj_id, "dst": cid, "label": item_name, "field_key": field_key})
        q.append(obj)
        return obj_id

    # ---------- scan root scope ----------
    for scope_dict in [root_scope["__locals__"], root_scope["__globals__"]]:
        for k, v in scope_dict.items():
            if not include_private and k.startswith("_"):
                continue
            label = format_typed_label(k, v)
            value_text = f"value = {short(v)}" if is_primitive(v) else None
            should_force = k in focus_vars
            if should_force and is_container(v):
                _add_obj(v, label, value_text=f"value = {short(v)}", force_render=True)
                continue
            if should_force and not is_renderable(v, include_containers=include_containers):
                _add_obj(short(v), label, value_text=f"value = {short(v)}", force_render=True)
                continue
            _add_obj(v, label, value_text=value_text)

    # ---------- pointer watchers ----------
    merged_scope = {}
    merged_scope.update(root_scope.get("__globals__", {}))
    merged_scope.update(root_scope.get("__locals__", {}))
    for pointer_name, container_name in pointer_watchers:
        pointer_value = merged_scope.get(pointer_name)
        container_value = merged_scope.get(container_name)
        if not isinstance(pointer_value, int):
            _add_pointer_node(pointer_name, container_name, pointer_value, "status = non_int_index")
            continue
        if not is_container(container_value):
            _add_pointer_node(pointer_name, container_name, pointer_value, "status = missing_container")
            continue
        try:
            pointed = container_value[pointer_value]
            _add_pointer_node(pointer_name, container_name, pointer_value, f"value = {short(pointed)}")
        except Exception:
            _add_pointer_node(pointer_name, container_name, pointer_value, "status = out_of_range_or_invalid")

    # ---------- BFS (field resolution delegated to _resolve_object_fields) ----------
    while q:
        obj = q.popleft()
        obj_id = id(obj)
        owner = node_index.get(obj_id)

        if owner is None or not owner.get("is_class_object"):
            continue

        item_map = dict(iter_object_items(obj, include_private))

        _resolve_object_fields(owner, obj, item_map, obj_id,
                               nodes, edges, visited, max_nodes,
                               include_containers, _add_obj)

    return nodes, edges
