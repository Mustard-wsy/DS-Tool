import dsvis
dsvis.auto()

class RBNode:
    RED = True
    BLACK = False

    def __init__(self, key, color=RED):
        self.key = key
        self.color = color

        self.left = None
        self.right = None
        self.parent = None


class RedBlackTree:
    def __init__(self):
        self.root = None

    # =========================
    # 工具函数
    # =========================

    def color_of(self, node):
        return RBNode.BLACK if node is None else node.color

    # =========================
    # 左旋
    # =========================

    def left_rotate(self, x):
        y = x.right
        t2 = y.left

        y.left = x
        x.right = t2

        if t2:
            t2.parent = x

        y.parent = x.parent

        if x.parent is None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        x.parent = y

    # =========================
    # 右旋
    # =========================

    def right_rotate(self, y):
        x = y.left
        t2 = x.right

        x.right = y
        y.left = t2

        if t2:
            t2.parent = y

        x.parent = y.parent

        if y.parent is None:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x

        y.parent = x

    # =========================
    # 插入
    # =========================

    def insert(self, key):
        node = RBNode(key)

        parent = None
        current = self.root

        while current:
            parent = current

            if key < current.key:
                current = current.left
            else:
                current = current.right

        node.parent = parent

        if parent is None:
            self.root = node
        elif key < parent.key:
            parent.left = node
        else:
            parent.right = node

        self.fix_insert(node)

    # =========================
    # 插入修复
    # =========================

    def fix_insert(self, z):

        while (
            z.parent
            and z.parent.color == RBNode.RED
        ):

            # 父节点在左边
            if z.parent == z.parent.parent.left:

                uncle = z.parent.parent.right

                # Case 1: 叔叔红
                if self.color_of(uncle) == RBNode.RED:

                    z.parent.color = RBNode.BLACK
                    uncle.color = RBNode.BLACK
                    z.parent.parent.color = RBNode.RED

                    z = z.parent.parent

                else:

                    # Case 2: LR
                    if z == z.parent.right:
                        z = z.parent
                        self.left_rotate(z)

                    # Case 3: LL
                    z.parent.color = RBNode.BLACK
                    z.parent.parent.color = RBNode.RED

                    self.right_rotate(z.parent.parent)

            # 父节点在右边
            else:

                uncle = z.parent.parent.left

                # Case 1: 叔叔红
                if self.color_of(uncle) == RBNode.RED:

                    z.parent.color = RBNode.BLACK
                    uncle.color = RBNode.BLACK
                    z.parent.parent.color = RBNode.RED

                    z = z.parent.parent

                else:

                    # Case 2: RL
                    if z == z.parent.left:
                        z = z.parent
                        self.right_rotate(z)

                    # Case 3: RR
                    z.parent.color = RBNode.BLACK
                    z.parent.parent.color = RBNode.RED

                    self.left_rotate(z.parent.parent)

        self.root.color = RBNode.BLACK

    # =========================
    # 中序遍历
    # =========================

    def inorder(self, node=None):

        if node is None:
            node = self.root

        result = []

        def dfs(cur):
            if cur is None:
                return

            dfs(cur.left)

            result.append(
                (
                    cur.key,
                    "R" if cur.color else "B"
                )
            )

            dfs(cur.right)

        dfs(node)

        return result

    # =========================
    # 校验红黑树
    # =========================

    def validate(self):

        if self.root is None:
            return True

        # 根必须黑
        if self.root.color != RBNode.BLACK:
            return False

        def dfs(node):

            if node is None:
                return True, 1

            # 红节点不能接红节点
            if node.color == RBNode.RED:

                if (
                    self.color_of(node.left) == RBNode.RED
                    or self.color_of(node.right) == RBNode.RED
                ):
                    return False, 0

            ok_l, bh_l = dfs(node.left)
            ok_r, bh_r = dfs(node.right)

            if not ok_l or not ok_r:
                return False, 0

            # 黑高必须一致
            if bh_l != bh_r:
                return False, 0

            return (
                True,
                bh_l + (
                    1 if node.color == RBNode.BLACK else 0
                )
            )

        return dfs(self.root)[0]


# =====================================
# 教学演示
# =====================================

def rb_tree_demo():

    tree = RedBlackTree()

    # 精心设计的数据：
    # 包含：
    # - recolor
    # - LL
    # - RR
    # - LR
    # - RL

    demo_data = [
        10,
        20,
        30,   # RR
        15,   # recolor
        5,
        1,    # LL
        25,
        27,   # LR
        50,
        60,
        55    # RL
    ]

    for value in demo_data:
        tree.insert(value)

    return tree


if __name__ == "__main__":

    rb_tree = rb_tree_demo()

    assert rb_tree.validate()