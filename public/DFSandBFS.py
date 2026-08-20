import dsvis
dsvis.auto()

from collections import deque


class GraphNode:
    def __init__(self, value):
        self.value = value
        self.neighbors = []


class Graph:
    def __init__(self):
        self.nodes = {}

    # =========================
    # 添加节点
    # =========================

    def add_node(self, value):

        if value not in self.nodes:
            self.nodes[value] = GraphNode(value)

    # =========================
    # 添加无向边
    # =========================

    def add_edge(self, u, v):

        self.add_node(u)
        self.add_node(v)

        self.nodes[u].neighbors.append(self.nodes[v])
        self.nodes[v].neighbors.append(self.nodes[u])

    # =========================
    # BFS
    # =========================

    def bfs(self, start):

        visited = set()
        order = []

        q = deque()

        q.append(self.nodes[start])
        visited.add(start)

        while q:

            node = q.popleft()

            order.append(node.value)

            for neighbor in node.neighbors:

                if neighbor.value not in visited:

                    visited.add(neighbor.value)
                    q.append(neighbor)

        return order

    # =========================
    # DFS
    # =========================

    def dfs(self, start):

        visited = set()
        order = []

        def _dfs(node):

            visited.add(node.value)

            order.append(node.value)

            for neighbor in node.neighbors:

                if neighbor.value not in visited:
                    _dfs(neighbor)

        _dfs(self.nodes[start])

        return order

    # =========================
    # 校验连通性
    # =========================

    def is_connected(self):

        if not self.nodes:
            return True

        start = next(iter(self.nodes))

        visited = set()

        def dfs(node):

            visited.add(node.value)

            for neighbor in node.neighbors:

                if neighbor.value not in visited:
                    dfs(neighbor)

        dfs(self.nodes[start])

        return len(visited) == len(self.nodes)


# =====================================
# 教学演示
# =====================================

def graph_demo():

    g = Graph()

    # 精心设计的图：
    #
    #         A
    #       /   \
    #      B     C
    #     / \   / \
    #    D   E F   G
    #         \   /
    #           H
    #
    # BFS:
    # A B C D E F G H
    #
    # DFS:
    # A B D E H G C F
    #

    edges = [
        ("A", "B"),
        ("A", "C"),

        ("B", "D"),
        ("B", "E"),

        ("C", "F"),
        ("C", "G"),

        ("E", "H"),
        ("G", "H"),
    ]

    for u, v in edges:
        g.add_edge(u, v)

    bfs_order = g.bfs("A")
    dfs_order = g.dfs("A")

    assert g.is_connected()

    return g, bfs_order, dfs_order


if __name__ == "__main__":

    graph, bfs_result, dfs_result = graph_demo()

    print("BFS:")
    print(bfs_result)

    print()

    print("DFS:")
    print(dfs_result)