import dsvis
dsvis.auto()

import random


# 定义节点
class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


# 生成链表
def generate_list(n):
    if n <= 0:
        return None

    head = Node(random.randint(0, 100))
    cur = head

    for _ in range(n - 1):
        cur.next = Node(random.randint(0, 100))
        cur = cur.next

    return head


# 打印链表
def print_list(head):
    cur = head
    while cur:
        print(cur.val, end=" -> ")
        cur = cur.next
    print("None")


# 生成一个长度为 50 的链表
head = generate_list(50)

# 输出
print_list(head)