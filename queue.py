import random
import dsvis
dsvis.auto()

# 简单队列（基于 list）
class Queue:
    def __init__(self):
        self.data = []

    def enqueue(self, x):
        self.data.append(x)   # 入队（尾部加）

    def dequeue(self):
        if self.is_empty():
            return None
        return self.data.pop(0)  # 出队（头部出）

    def is_empty(self):
        return len(self.data) == 0

    def __str__(self):
        return str(self.data)

# 测试
q = Queue()

# 随机入队 10 个元素
for _ in range(10):
    q.enqueue(random.randint(0, 100))

print("初始队列:", q)

# 出队 5 个元素
for _ in range(5):
    print("出队:", q.dequeue())

print("剩余队列:", q)