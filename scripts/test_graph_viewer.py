"""Test the independent graph-viewer transformer against real BFS output.

Runs graph_builder.walk_graph on live graph objects (mirroring the repo's
Prim / scc / DFS-BFS shapes) and checks the graph-view payload.

Run:  e:/Study/DataStructure/DSVis/.venv/bin/python.exe scripts/test_graph_viewer.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dsvis.graph_builder import walk_graph
from dsvis.graph_viewer import build_graph_viewer_data


def _scope(root_name, obj):
    return {"__locals__": {root_name: obj}, "__globals__": {}}


# ── 1. Directed unweighted (scc-like) ──
class SNode:
    def __init__(self, nid):
        self.id = nid
        self.neighbors = []


class SGraph:
    def __init__(self, n):
        self.nodes = [SNode(i) for i in range(n)]

    def add_edge(self, u, v):
        self.nodes[u].neighbors.append(self.nodes[v])


def make_scc():
    g = SGraph(4)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 0)  # cycle
    g.add_edge(2, 3)
    return g


# ── 2. Undirected weighted (Prim-like) ──
class PEdge:
    def __init__(self, to, weight):
        self.to = to
        self.weight = weight


class PNode:
    def __init__(self, value):
        self.value = value
        self.edges = []


class PGraph:
    def __init__(self):
        self.nodes = {}

    def add_node(self, value):
        if value not in self.nodes:
            self.nodes[value] = PNode(value)

    def add_edge(self, u, v, w):
        self.add_node(u)
        self.add_node(v)
        self.nodes[u].edges.append(PEdge(self.nodes[v], w))
        self.nodes[v].edges.append(PEdge(self.nodes[u], w))


def make_prim():
    g = PGraph()
    g.add_edge('A', 'B', 3)
    g.add_edge('B', 'C', 1)
    g.add_edge('A', 'C', 2)
    return g


# ── 3. Undirected unweighted (DFS/BFS-like) ──
class BNode:
    def __init__(self, value):
        self.value = value
        self.neighbors = []


class BGraph:
    def __init__(self):
        self.nodes = {}

    def add_node(self, value):
        if value not in self.nodes:
            self.nodes[value] = BNode(value)

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        self.nodes[u].neighbors.append(self.nodes[v])
        self.nodes[v].neighbors.append(self.nodes[u])


def make_bfs():
    g = BGraph()
    g.add_edge('X', 'Y')
    g.add_edge('Y', 'Z')
    return g


def run(name, g, root_name='g'):
    nodes, edges = walk_graph(_scope(root_name, g))
    view = build_graph_viewer_data(nodes, edges)
    val_of = {n['id']: n['value'] for n in view['nodes']}
    print(f"\n=== {name} ===")
    print("vertices:", [(n['value'], n['index']) for n in view['nodes']])
    print("edges:", [(val_of.get(e['source']), val_of.get(e['target']), e['value']) for e in view['edges']])
    print("undirected:", view['undirected'])
    return view


def main():
    ok = True

    scc = run("scc (directed unweighted)", make_scc())
    assert scc['undirected'] is False, "scc should be directed"
    assert len(scc['nodes']) == 4, f"expected 4 vertices, got {len(scc['nodes'])}"
    vals = sorted(str(n['value']) for n in scc['nodes'])
    assert vals == ['0', '1', '2', '3'], f"vertex values should be ids, got {vals}"
    assert len(scc['edges']) == 4, f"expected 4 directed edges, got {len(scc['edges'])}"

    prim = run("prim (undirected weighted)", make_prim())
    assert prim['undirected'] is True, "prim should be undirected"
    assert len(prim['nodes']) == 3, f"expected 3 vertices, got {len(prim['nodes'])}"
    vals = sorted(str(n['value']) for n in prim['nodes'])
    assert vals == ['A', 'B', 'C'], f"vertex values should be A/B/C, got {vals}"
    # undirected collapsed → 3 distinct pairs
    assert len(prim['edges']) == 3, f"expected 3 collapsed edges, got {len(prim['edges'])}"
    weights = sorted(int(e['value']) for e in prim['edges'])
    assert weights == [1, 2, 3], f"edge weights should be 1,2,3, got {weights}"
    # no Edge objects leaked as nodes
    for n in prim['nodes']:
        assert n['value'] in ('A', 'B', 'C'), f"edge object leaked: {n['value']}"

    bfs = run("bfs (undirected unweighted)", make_bfs())
    assert bfs['undirected'] is True, "bfs should be undirected"
    assert len(bfs['nodes']) == 3, f"expected 3 vertices, got {len(bfs['nodes'])}"
    assert len(bfs['edges']) == 2, f"expected 2 collapsed edges, got {len(bfs['edges'])}"

    print("\nAll graph-viewer tests passed.")
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
