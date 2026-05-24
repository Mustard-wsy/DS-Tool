import dsvis
dsvis.auto()

import heapq


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

    # =========================
    # 添加节点
    # =========================

    def add_node(self, value):

        if value not in self.nodes:
            self.nodes[value] = GraphNode(value)

    # =========================
    # 添加无向带权边
    # =========================

    def add_edge(self, u, v, w):

        self.add_node(u)
        self.add_node(v)

        self.nodes[u].edges.append(
            Edge(self.nodes[v], w)
        )

        self.nodes[v].edges.append(
            Edge(self.nodes[u], w)
        )

    # =========================
    # Prim 最小生成树
    # =========================

    def prim(self, start):

        visited = set()

        mst_edges = []
        total_weight = 0

        pq = []

        visited.add(start)

        # 起点邻边入堆
        for edge in self.nodes[start].edges:

            heapq.heappush(
                pq,
                (
                    edge.weight,
                    start,
                    edge.to.value,
                )
            )

        while pq:

            weight, u, v = heapq.heappop(pq)

            if v in visited:
                continue

            visited.add(v)

            mst_edges.append((u, v, weight))

            total_weight += weight

            # 新节点邻边入堆
            for edge in self.nodes[v].edges:

                if edge.to.value not in visited:

                    heapq.heappush(
                        pq,
                        (
                            edge.weight,
                            v,
                            edge.to.value,
                        )
                    )

        return mst_edges, total_weight

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

            for edge in node.edges:

                if edge.to.value not in visited:
                    dfs(edge.to)

        dfs(self.nodes[start])

        return len(visited) == len(self.nodes)


# =====================================
# 教学演示
# =====================================

def prim_demo():

    g = Graph()

    # 精心设计的经典教材图
    #
    #        A
    #      /   \
    #    4/     \2
    #    B---1---C
    #    |\      |
    #  5 | \8    |10
    #    |  \    |
    #    D---2---E
    #       3
    #

    edges = [
        ("A", "B", 4),
        ("A", "C", 2),

        ("B", "C", 1),
        ("B", "D", 5),
        ("B", "E", 8),

        ("C", "E", 10),

        ("D", "E", 2),
        ("C", "D", 3),
    ]

    for u, v, w in edges:
        g.add_edge(u, v, w)

    mst, total = g.prim("A")

    assert g.is_connected()

    return g, mst, total


if __name__ == "__main__":

    graph, mst_edges, total_weight = prim_demo()

    print("Prim 最小生成树：")

    for u, v, w in mst_edges:
        print(f"{u} - {v} : {w}")

    print()

    print("总权值：", total_weight)