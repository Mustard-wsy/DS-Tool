import dsvis
dsvis.auto()
class Node:
    """链表节点"""
    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedStack:
    """用链表实现的栈"""
    def __init__(self):
        self.top = None  # 栈顶
        self.size = 0

    def is_empty(self):
        return self.top is None

    def push(self, value):
        """入栈"""
        new_node = Node(value)
        new_node.next = self.top
        self.top = new_node
        self.size += 1

    def pop(self):
        """出栈"""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        value = self.top.value
        self.top = self.top.next
        self.size -= 1
        return value

    def peek(self):
        """查看栈顶元素"""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.top.value

    def __len__(self):
        return self.size

    def __str__(self):
        """打印栈（从栈顶到栈底）"""
        current = self.top
        values = []
        while current:
            values.append(str(current.value))
            current = current.next
        return " -> ".join(values)

import random

# 假设 LinkedStack 已经定义好了
stack = LinkedStack()

operations = ["push", "pop"]

for i in range(15):  # 执行15次随机操作
    op = random.choice(operations)

    if op == "push":
        value = random.randint(1, 100)
        stack.push(value)
        print(f"操作 {i+1}: push({value})")
    else:
        if stack.is_empty():
            print(f"操作 {i+1}: pop() -> 栈为空，跳过")
        else:
            value = stack.pop()
            print(f"操作 {i+1}: pop() -> {value}")

    print("当前栈:", stack)
    print("-" * 40)