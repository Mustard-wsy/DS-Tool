import dsvis
dsvis.auto()
from collections import deque


class GraphNode:
    def __init__(self, value):
        self.value = value
        self.next = []


class DirectedGraph:
    def __init__(self):
        self.nodes = {}

    # =========================
    # 添加节点
    # =========================

    def add_node(self, value):

        if value not in self.nodes:
            self.nodes[value] = GraphNode(value)

    # =========================
    # 添加有向边
    # =========================

    def add_edge(self, u, v):

        self.add_node(u)
        self.add_node(v)

        self.nodes[u].next.append(
            self.nodes[v]
        )

    # =========================
    # 计算入度
    # =========================

    def compute_indegree(self):

        indegree = {
            value: 0
            for value in self.nodes
        }

        for node in self.nodes.values():

            for neighbor in node.next:
                indegree[neighbor.value] += 1

        return indegree

    # =========================
    # Kahn 拓扑排序
    # =========================

    def topological_sort(self):

        indegree = self.compute_indegree()

        q = deque()

        # 所有入度为 0 的点入队
        for node in self.nodes:

            if indegree[node] == 0:
                q.append(node)

        order = []

        while q:

            cur = q.popleft()

            order.append(cur)

            for neighbor in self.nodes[cur].next:

                indegree[neighbor.value] -= 1

                if indegree[neighbor.value] == 0:
                    q.append(neighbor.value)

        # 有环
        if len(order) != len(self.nodes):
            return None

        return order

    # =========================
    # 检查是否为 DAG
    # =========================

    def is_dag(self):

        return self.topological_sort() is not None


# =====================================
# 教学演示
# =====================================

def topo_demo():

    g = DirectedGraph()

    # 精心设计的 DAG：
    #
    #     A
    #    / \
    #   B   C
    #   |\ /|
    #   | D |
    #   |/ \|
    #   E   F
    #    \ /
    #     G
    #
    # 一个可能的拓扑序：
    # A B C D E F G

    edges = [
        ("A", "B"),
        ("A", "C"),

        ("B", "D"),
        ("C", "D"),

        ("B", "E"),
        ("D", "E"),

        ("C", "F"),
        ("D", "F"),

        ("E", "G"),
        ("F", "G"),
    ]

    for u, v in edges:
        g.add_edge(u, v)

    order = g.topological_sort()

    assert g.is_dag()

    return g, order


if __name__ == "__main__":

    graph, topo_order = topo_demo()

    print("拓扑排序结果：")
    print(topo_order)