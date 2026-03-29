import random
import dsvis
dsvis.auto()

class BTreeNode:
    def __init__(self, t, leaf=False):
        self.t = t                  # 最小度数
        self.leaf = leaf            # 是否叶子节点
        self.keys = []              # 存储键
        self.children = []          # 子节点


class BTree:
    def __init__(self, t):
        self.t = t
        self.root = BTreeNode(t, leaf=True)

    # 分裂子节点
    def split_child(self, parent, index):
        t = self.t
        full_child = parent.children[index]
        new_child = BTreeNode(t, leaf=full_child.leaf)

        # 中间 key 上移
        mid_key = full_child.keys[t - 1]

        # 新节点拿右半部分
        new_child.keys = full_child.keys[t:]
        full_child.keys = full_child.keys[:t - 1]

        # 如果不是叶子，分裂子节点指针
        if not full_child.leaf:
            new_child.children = full_child.children[t:]
            full_child.children = full_child.children[:t]

        # 插入到父节点
        parent.children.insert(index + 1, new_child)
        parent.keys.insert(index, mid_key)

    # 插入非满节点
    def insert_non_full(self, node, key):
        i = len(node.keys) - 1

        if node.leaf:
            # 插入到叶子节点
            node.keys.append(0)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            # 找到应该插入的子节点
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1

            # 如果子节点满了，先分裂
            if len(node.children[i].keys) == (2 * self.t - 1):
                self.split_child(node, i)

                if key > node.keys[i]:
                    i += 1

            self.insert_non_full(node.children[i], key)

    # 插入入口
    def insert(self, key):
        root = self.root

        # 如果根满了，先分裂
        if len(root.keys) == (2 * self.t - 1):
            new_root = BTreeNode(self.t, leaf=False)
            new_root.children.append(root)

            self.split_child(new_root, 0)
            self.root = new_root

            self.insert_non_full(new_root, key)
        else:
            self.insert_non_full(root, key)


# ===============================
# 内部测试（无输入输出）
# ===============================

def build_random_btree():
    t = 3
    btree = BTree(t)

    # 随机生成数据
    data = list(range(50))
    random.shuffle(data)

    for num in data:
        btree.insert(num)

    return btree


# 执行构建
btree_instance = build_random_btree()