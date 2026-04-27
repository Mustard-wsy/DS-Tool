import dsvis
dsvis.auto()
import random
random.seed(42)

class Node:
    def __init__(self, id):
        self.id = id
        self.neighbors = []

        # Tarjan相关属性（直接挂在节点上）
        self.index = -1
        self.lowlink = -1
        self.on_stack = False

class Graph:
    def __init__(self, n):
        self.nodes = [Node(i) for i in range(n)]

    def add_edge(self, u, v):
        self.nodes[u].neighbors.append(self.nodes[v])


def tarjan(graph):
    index = 0
    stack = []
    sccs = []

    def dfs(node):
        nonlocal index

        node.index = index
        node.lowlink = index
        index += 1

        stack.append(node)
        node.on_stack = True

        for nei in node.neighbors:
            if nei.index == -1:
                dfs(nei)
                node.lowlink = min(node.lowlink, nei.lowlink)
            elif nei.on_stack:
                node.lowlink = min(node.lowlink, nei.index)

        # root of SCC
        if node.lowlink == node.index:
            comp = []
            while True:
                top = stack.pop()
                top.on_stack = False
                comp.append(top)
                if top == node:
                    break
            sccs.append(comp)

    for node in graph.nodes:
        if node.index == -1:
            dfs(node)

    return sccs


# ===== 自动构建图 =====
n = 10
g = Graph(n)

for _ in range(20):
    u = random.randint(0, n-1)
    v = random.randint(0, n-1)
    g.add_edge(u, v)

# ===== 运行 =====
scc_result = tarjan(g)