import dsvis
dsvis.auto()
class HashTable:
    EMPTY = None
    DELETED = object()

    def __init__(self, capacity=13):
        self.capacity = capacity
        self.table = [self.EMPTY] * capacity
        self.size = 0

    # =========================
    # 哈希函数
    # =========================

    def hash(self, key):
        return key % self.capacity

    # =========================
    # 线性探测
    # =========================

    def probe(self, index):
        return (index + 1) % self.capacity

    # =========================
    # 插入
    # =========================

    def insert(self, key):

        if self.size >= self.capacity:
            raise Exception("Hash Table Full")

        index = self.hash(key)

        while (
            self.table[index] is not self.EMPTY
            and self.table[index] is not self.DELETED
        ):

            # 已存在
            if self.table[index] == key:
                return

            index = self.probe(index)

        self.table[index] = key
        self.size += 1

    # =========================
    # 查找
    # =========================

    def search(self, key):

        index = self.hash(key)
        start = index

        while self.table[index] is not self.EMPTY:

            if self.table[index] == key:
                return index

            index = self.probe(index)

            # 回到起点
            if index == start:
                break

        return -1

    # =========================
    # 删除
    # =========================

    def delete(self, key):

        index = self.search(key)

        if index != -1:
            self.table[index] = self.DELETED
            self.size -= 1
            return True

        return False

    # =========================
    # 获取当前状态
    # =========================

    def snapshot(self):

        result = []

        for value in self.table:

            if value is self.EMPTY:
                result.append("EMPTY")

            elif value is self.DELETED:
                result.append("DELETED")

            else:
                result.append(value)

        return result

    # =========================
    # 校验
    # =========================

    def validate(self):

        count = 0

        for value in self.table:
            if (
                value is not self.EMPTY
                and value is not self.DELETED
            ):
                count += 1

        return count == self.size


# =====================================
# 教学演示
# =====================================

def hash_table_demo():

    ht = HashTable(capacity=13)


    insert_data = [
        18, 41, 22, 44,
        59, 32, 31, 73
    ]

    # 插入
    for value in insert_data:
        ht.insert(value)

    # 查找
    assert ht.search(44) != -1
    assert ht.search(73) != -1
    assert ht.search(100) == -1

    # 删除
    ht.delete(22)
    ht.delete(44)

    # 删除后继续插入
    ht.insert(57)
    ht.insert(70)

    assert ht.validate()

    return ht


if __name__ == "__main__":

    hash_table = hash_table_demo()

    print(hash_table.snapshot())