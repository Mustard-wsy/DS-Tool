import auto_viz

class DNode:
    def __init__(self, val):
        self.tag = "dbl"
        self.val = val
        self.prev = None
        self.next = None

def append(tail, node):
    tail.next = node
    node.prev = tail
    return node

def insert_after(node, new_node):
    right = node.next
    new_node.prev = node
    new_node.next = node.next
    if right is not None:
        right.prev = new_node
    node.next = new_node

# 构造双链表 1 <-> 2 <-> 3 <-> 4
h = DNode(1)
t = append(h, DNode(2))
t = append(t, DNode(3))
t = append(t, DNode(4))

auto_viz.capture(
    direction="LR",
    title="双链表-初始",
    prefer="graphviz",
    arrow_start="attribute",
    arrow_compass="auto",
    layout="hierarchical",
    edge_routing="polyline",
)

insert_after(h.next, DNode(99))
auto_viz.capture(
    direction="LR",
    title="双链表-插入99后",
    prefer="graphviz",
    arrow_start="attribute",
    arrow_compass="auto",
    layout="hierarchical",
    edge_routing="polyline",
)

# 构造环：tail.next -> head，head.prev -> tail
tail = h
while tail.next is not None:
    tail = tail.next
tail.next = h
h.prev = tail

auto_viz.capture(
    direction="LR",
    title="双链表-成环",
    prefer="graphviz",
    arrow_start="attribute",
    arrow_compass="auto",
    layout="hierarchical",
    edge_routing="polyline",
)

# 对比：从节点中心出发（非属性锚点）
auto_viz.capture(
    direction="LR",
    title="双链表-成环(节点中心出发)",
    prefer="graphviz",
    arrow_start="node",
    layout="hierarchical",
    edge_routing="polyline",
)

auto_viz.capture(
    direction="LR",
    title="双链表-成环(SVG后端)",
    prefer="svg",
    arrow_start="attribute",
    arrow_compass="auto",
    edge_routing="polyline",
)