import random
import dsvis
dsvis.auto()

class BTreeNode:
    __dsvis_bindings__ = [
        "keys@A:3",
        "children@A:1",
    ]

    def __init__(self, t, leaf=False):
        self.t = t                  # 最小度数
        self.leaf = leaf            # 是否叶子节点
        self.keys = []                                  # 存储键
        self.children = []                              # 子节点
        dsvis.bind_fields(self, keys=("A", 3), children=("A", 1))


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

    def inorder(self, node=None):
        """中序遍历，便于快速检查 B 树内容是否正确。"""
        node = self.root if node is None else node
        if node.leaf:
            return node.keys[:]

        out = []
        for i, key in enumerate(node.keys):
            out.extend(self.inorder(node.children[i]))
            out.append(key)
        out.extend(self.inorder(node.children[len(node.keys)]))
        return out

    def validate(self):
        """检查关键 B 树不变式（key 个数、有序性、子节点数量）。"""
        t = self.t

        def _check(node, is_root):
            if node.keys != sorted(node.keys):
                return False, "节点 key 不是升序"

            if is_root:
                if len(node.keys) > 2 * t - 1:
                    return False, "根节点 key 数过多"
            else:
                if len(node.keys) < t - 1 or len(node.keys) > 2 * t - 1:
                    return False, "非根节点 key 数不合法"

            if node.leaf:
                if node.children:
                    return False, "叶子节点不应包含 children"
                return True, ""

            if len(node.children) != len(node.keys) + 1:
                return False, "内部节点 children 数应为 keys+1"

            for child in node.children:
                ok, msg = _check(child, False)
                if not ok:
                    return False, msg
            return True, ""

        return _check(self.root, True)


# ===============================
# 内部测试（无输入输出）
# ===============================

def build_random_btree():
    t = 3
    btree = BTree(t)

    # 固定随机种子，便于复现
    random.seed(42)
    data = list(range(20))
    random.shuffle(data)

    for num in data:
        btree.insert(num)
        #dsvis.capture()

    return btree


if __name__ == "__main__":
    # 执行构建
    btree_instance = build_random_btree()
    ok, msg = btree_instance.validate()
    assert ok, f"BTree 校验失败: {msg}"
