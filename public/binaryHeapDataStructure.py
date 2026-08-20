import dsvis
from collections import deque
dsvis.auto()

class HeapNode:
    def __init__(self, value):
        self.value = value

        self.parent = None
        self.left = None
        self.right = None


class BinaryHeap:
    def __init__(self):
        self.root = None
        self.size = 0

    # =========================
    # 获取插入位置
    # =========================

    def get_insert_parent(self):

        q = deque([self.root])

        while q:

            node = q.popleft()

            # 找到第一个不满节点
            if node.left is None or node.right is None:
                return node

            q.append(node.left)
            q.append(node.right)

    # =========================
    # 获取最后节点
    # =========================

    def get_last_node(self):

        q = deque([self.root])

        last = None

        while q:

            last = q.popleft()

            if last.left:
                q.append(last.left)

            if last.right:
                q.append(last.right)

        return last

    # =========================
    # 插入
    # =========================

    def push(self, value):

        new_node = HeapNode(value)

        # 第一个节点
        if self.root is None:
            self.root = new_node
            self.size = 1
            return

        parent = self.get_insert_parent()

        new_node.parent = parent

        if parent.left is None:
            parent.left = new_node
        else:
            parent.right = new_node

        self.size += 1

        self.sift_up(new_node)

    # =========================
    # 上滤
    # =========================

    def sift_up(self, node):

        while (
            node.parent
            and node.value < node.parent.value
        ):

            node.value, node.parent.value = (
                node.parent.value,
                node.value,
            )

            node = node.parent

    # =========================
    # 删除堆顶
    # =========================

    def pop(self):

        if self.root is None:
            raise Exception("Heap is empty")

        top = self.root.value

        # 只有一个节点
        if self.size == 1:
            self.root = None
            self.size = 0
            return top

        last = self.get_last_node()

        # 最后节点值覆盖根
        self.root.value = last.value

        # 删除最后节点
        parent = last.parent

        if parent.left == last:
            parent.left = None
        else:
            parent.right = None

        self.size -= 1

        self.sift_down(self.root)

        return top

    # =========================
    # 下滤
    # =========================

    def sift_down(self, node):

        while node:

            smallest = node

            if (
                node.left
                and node.left.value < smallest.value
            ):
                smallest = node.left

            if (
                node.right
                and node.right.value < smallest.value
            ):
                smallest = node.right

            if smallest == node:
                break

            node.value, smallest.value = (
                smallest.value,
                node.value,
            )

            node = smallest

    # =========================
    # 层序遍历
    # =========================

    def level_order(self):

        if self.root is None:
            return []

        result = []

        q = deque([self.root])

        while q:

            node = q.popleft()

            result.append(node.value)

            if node.left:
                q.append(node.left)

            if node.right:
                q.append(node.right)

        return result

    # =========================
    # 校验堆性质
    # =========================

    def validate(self):

        if self.root is None:
            return True

        q = deque([self.root])

        while q:

            node = q.popleft()

            if (
                node.left
                and node.left.value < node.value
            ):
                return False

            if (
                node.right
                and node.right.value < node.value
            ):
                return False

            if node.left:
                q.append(node.left)

            if node.right:
                q.append(node.right)

        return True


# =====================================
# 教学演示
# =====================================

def heap_demo():

    heap = BinaryHeap()

    # 精心设计的数据：
    # 展示：
    # - 完全二叉树
    # - 上滤
    # - 下滤

    insert_data = [
        40,
        20,
        35,
        10,
        15,
        30,
        5,
        12,
        8,
    ]

    for value in insert_data:
        heap.push(value)

    popped = []

    for _ in range(3):
        popped.append(heap.pop())

    assert popped == sorted(popped)

    assert heap.validate()

    return heap


if __name__ == "__main__":

    binary_heap = heap_demo()

    print(binary_heap.level_order())