import heapq
import random
import dsvis
dsvis.auto()

random.seed(42)

class PriorityQueue:
    def __init__(self):
        self.heap = []

    def push(self, x):
        heapq.heappush(self.heap, x)

    def pop(self):
        if self.heap:
            return heapq.heappop(self.heap)

pq = PriorityQueue()

data = [random.randint(1, 100) for _ in range(20)]

for x in data:
    pq.push(x)

for _ in range(10):
    pq.pop()