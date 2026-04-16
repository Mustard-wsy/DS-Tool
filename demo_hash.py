import random
import string
import dsvis
dsvis.auto()
dsvis.set_mode("fine")
class Node:
    """链表节点（用于哈希冲突）"""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class HashTable:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.buckets = [None] * capacity
        self.size = 0

    def _hash(self, key):
        """哈希函数"""
        return hash(key) % self.capacity

    def put(self, key, value):
        """插入 / 更新"""
        index = self._hash(key)
        head = self.buckets[index]

        current = head
        while current:
            if current.key == key:
                current.value = value  # 更新
                return
            current = current.next

        # 插入新节点（头插法）
        new_node = Node(key, value)
        new_node.next = head
        self.buckets[index] = new_node
        self.size += 1

    def get(self, key):
        """查找"""
        index = self._hash(key)
        current = self.buckets[index]

        while current:
            if current.key == key:
                return current.value
            current = current.next

        raise KeyError(f"{key} 不存在")

    def remove(self, key):
        """删除"""
        index = self._hash(key)
        current = self.buckets[index]
        prev = None

        while current:
            if current.key == key:
                if prev:
                    prev.next = current.next
                else:
                    self.buckets[index] = current.next
                self.size -= 1
                return
            prev = current
            current = current.next

        raise KeyError(f"{key} 不存在")

    def __len__(self):
        return self.size

    def __str__(self):
        result = []
        for i, node in enumerate(self.buckets):
            current = node
            chain = []
            while current:
                chain.append(f"({current.key}:{current.value})")
                current = current.next
            result.append(f"{i}: " + " -> ".join(chain))
        return "\n".join(result)


ht = HashTable()

for i in range(15):
    op = random.choice(["put", "get", "remove"])
    key = random.choice(string.ascii_lowercase[:5])  # a-e

    try:
        if op == "put":
            value = random.randint(1, 100)
            ht.put(key, value)
            print(f"操作 {i+1}: put({key}, {value})")

        elif op == "get":
            value = ht.get(key)
            print(f"操作 {i+1}: get({key}) -> {value}")

        else:
            ht.remove(key)
            print(f"操作 {i+1}: remove({key})")

    except KeyError:
        print(f"操作 {i+1}: {op}({key}) -> KeyError")

    print(ht)
    print("-" * 40)