import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dsvis

dsvis.set_mode("coarse")
dsvis.set_text_flow("vertical")
dsvis.set_layout("vertical")           # TB rankdir
dsvis.hide_field("AVLNode.__title__")  # 隐藏标题 → 标题列应折叠为 0
dsvis.auto()


class AVLNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1


class AVLTree:
    def __init__(self):
        self.root = None

    def get_height(self, node):
        return node.height if node else 0

    def update_height(self, node):
        node.height = max(self.get_height(node.left), self.get_height(node.right)) + 1

    def get_balance(self, node):
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    def right_rotate(self, y):
        x = y.left
        t2 = x.right
        x.right = y
        y.left = t2
        self.update_height(y)
        self.update_height(x)
        return x

    def left_rotate(self, x):
        y = x.right
        t2 = y.left
        y.left = x
        x.right = t2
        self.update_height(x)
        self.update_height(y)
        return y

    def insert(self, node, key):
        if not node:
            return AVLNode(key)
        if key < node.key:
            node.left = self.insert(node.left, key)
        else:
            node.right = self.insert(node.right, key)
        self.update_height(node)
        balance = self.get_balance(node)
        if balance > 1 and key < node.left.key:
            return self.right_rotate(node)
        if balance < -1 and key > node.right.key:
            return self.left_rotate(node)
        if balance > 1 and key > node.left.key:
            node.left = self.left_rotate(node.left)
            return self.right_rotate(node)
        if balance < -1 and key < node.right.key:
            node.right = self.right_rotate(node.right)
            return self.left_rotate(node)
        return node

    def add(self, key):
        self.root = self.insert(self.root, key)

    def validate(self):
        def check(node):
            if not node:
                return True, 0
            ok_l, h_l = check(node.left)
            ok_r, h_r = check(node.right)
            if not ok_l or not ok_r:
                return False, 0
            if abs(h_l - h_r) > 1:
                return False, 0
            if node.height != max(h_l, h_r) + 1:
                return False, 0
            return True, node.height
        return check(self.root)[0]


def avl_demo():
    tree = AVLTree()
    for value in [30, 20, 10, 40, 50, 25, 45, 42]:
        tree.add(value)
    return tree


if __name__ == "__main__":
    avl = avl_demo()
    assert avl.validate()
