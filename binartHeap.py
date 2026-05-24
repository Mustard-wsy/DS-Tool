import dsvis
dsvis.auto()

class BinaryHeap:
    def __init__(self):
        self.heap = []

    # =========================
    # 父子节点
    # =========================

    def parent(self, i):
        return (i - 1) // 2

    def left(self, i):
        return i * 2 + 1

    def right(self, i):
        return i * 2 + 2

    # =========================
    # 上滤
    # =========================

    def sift_up(self, index):

        while index > 0:

            p = self.parent(index)

            if self.heap[p] <= self.heap[index]:
                break

            self.heap[p], self.heap[index] = (
                self.heap[index],
                self.heap[p],
            )

            index = p

    # =========================
    # 下滤
    # =========================

    def sift_down(self, index):

        n = len(self.heap)

        while True:

            smallest = index

            l = self.left(index)
            r = self.right(index)

            if (
                l < n
                and self.heap[l] < self.heap[smallest]
            ):
                smallest = l

            if (
                r < n
                and self.heap[r] < self.heap[smallest]
            ):
                smallest = r

            if smallest == index:
                break

            self.heap[index], self.heap[smallest] = (
                self.heap[smallest],
                self.heap[index],
            )

            index = smallest

    # =========================
    # 插入
    # =========================

    def push(self, value):

        self.heap.append(value)

        self.sift_up(len(self.heap) - 1)

    # =========================
    # 删除堆顶
    # =========================

    def pop(self):

        if not self.heap:
            raise Exception("Heap is empty")

        top = self.heap[0]

        last = self.heap.pop()

        if self.heap:
            self.heap[0] = last
            self.sift_down(0)

        return top

    # =========================
    # 建堆
    # =========================

    def heapify(self, data):

        self.heap = data[:]

        for i in range(
            len(self.heap) // 2 - 1,
            -1,
            -1,
        ):
            self.sift_down(i)

    # =========================
    # 查看堆顶
    # =========================

    def top(self):

        if not self.heap:
            return None

        return self.heap[0]

    # =========================
    # 校验堆性质
    # =========================

    def validate(self):

        n = len(self.heap)

        for i in range(n):

            l = self.left(i)
            r = self.right(i)

            if (
                l < n
                and self.heap[i] > self.heap[l]
            ):
                return False

            if (
                r < n
                and self.heap[i] > self.heap[r]
            ):
                return False

        return True


# =====================================
# 教学演示
# =====================================

def heap_demo():

    heap = BinaryHeap()

    # =====================
    # heapify 演示
    # =====================

    initial_data = [
        45,
        20,
        14,
        12,
        31,
        7,
        11,
        13,
        7
    ]

    heap.heapify(initial_data)

    # =====================
    # 插入演示
    # =====================

    insert_data = [
        5,
        2,
        18
    ]

    for value in insert_data:
        heap.push(value)

    # =====================
    # 删除堆顶演示
    # =====================

    popped = []

    for _ in range(3):
        popped.append(heap.pop())

    assert popped == sorted(popped)

    assert heap.validate()

    return heap


if __name__ == "__main__":

    binary_heap = heap_demo()

    print(binary_heap.heap)