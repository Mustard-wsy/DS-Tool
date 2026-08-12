import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dsvis

dsvis.set_mode("coarse")
dsvis.auto()


class GraphNode:
    def __init__(self, value):
        self.value = value
        self.edges = []


class Edge:
    def __init__(self, to, weight):
        self.to = to
        self.weight = weight


class Graph:
    def __init__(self):
        self.nodes = {}

    def add_node(self, value):
        if value not in self.nodes:
            self.nodes[value] = GraphNode(value)

    def add_edge(self, u, v, w):
        self.add_node(u)
        self.add_node(v)
        self.nodes[u].edges.append(Edge(self.nodes[v], w))
        self.nodes[v].edges.append(Edge(self.nodes[u], w))


def main():
    g = Graph()
    g.add_edge('A', 'B', 3)
    g.add_edge('B', 'C', 1)
    g.add_edge('C', 'D', 4)
    g.add_edge('D', 'A', 2)
    g.add_edge('A', 'C', 5)
    return g


g = main()
