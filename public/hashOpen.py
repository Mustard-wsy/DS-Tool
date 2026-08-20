import dsvis
dsvis.auto()

class Node:
    def __init__(self, key):
        self.key = key
        self.next = None


class HashTable:
    def __init__(self, capacity=7):
        self.capacity = capacity
        self.table = [None] * capacity
        self.size = 0

    # =========================
    # 哈希函数
    # =========================

    def hash(self, key):
        return key % self.capacity

    # =========================
    # 插入
    # =========================

    def insert(self, key):

        index = self.hash(key)

        # 已存在则不插入
        cur = self.table[index]

        while cur:
            if cur.key == key:
                return
            cur = cur.next

        new_node = Node(key)

        # 头插法
        new_node.next = self.table[index]
        self.table[index] = new_node

        self.size += 1

    # =========================
    # 查找
    # =========================

    def search(self, key):

        index = self.hash(key)

        cur = self.table[index]

        while cur:

            if cur.key == key:
                return True

            cur = cur.next

        return False

    # =========================
    # 删除
    # =========================

    def delete(self, key):

        index = self.hash(key)

        cur = self.table[index]
        prev = None

        while cur:

            if cur.key == key:

                if prev:
                    prev.next = cur.next
                else:
                    self.table[index] = cur.next

                self.size -= 1
                return True

            prev = cur
            cur = cur.next

        return False

    # =========================
    # 获取当前状态
    # =========================

    def snapshot(self):

        result = []

        for head in self.table:

            chain = []

            cur = head

            while cur:
                chain.append(cur.key)
                cur = cur.next

            result.append(chain)

        return result

    # =========================
    # 校验
    # =========================

    def validate(self):

        count = 0

        for head in self.table:

            cur = head

            while cur:
                count += 1
                cur = cur.next

        return count == self.size


# =====================================
# 教学演示
# =====================================

def hash_table_demo():

    ht = HashTable(capacity=7)

    # 精心设计的数据：
    # 大量冲突
    # 清晰形成链表

    insert_data = [
        10, 17, 24,   # -> bucket 3
        5, 12, 19,    # -> bucket 5
        7, 14, 21     # -> bucket 0
    ]

    for value in insert_data:
        ht.insert(value)

    # 查找
    assert ht.search(24)
    assert ht.search(19)
    assert not ht.search(100)

    # 删除
    ht.delete(12)
    ht.delete(21)

    # 删除后继续插入
    ht.insert(26)
    ht.insert(33)

    assert ht.validate()

    return ht


if __name__ == "__main__":

    hash_table = hash_table_demo()

    print(hash_table.snapshot())