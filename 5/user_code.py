import dsvis


class Node:
    def __init__(self, value):
        self.next = None
        self.prev = None
        self.value = value


a = Node(1)
b = Node(2)
c = Node(3)

a.next = b
b.next = c
c.prev = b

numbers = []
numbers.append(a.value)

# 手动 capture 仍可保留，AST 插桩会自动追加 trigger。
#dsvis.capture()
