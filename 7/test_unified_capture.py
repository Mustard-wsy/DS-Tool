#!/usr/bin/env python3
"""
测试统一的 capture 模式
验证 capture 现在像 trigger 一样工作，通过 scheduler 收集 steps，最后一起渲染
"""

import dsvis

class Node:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

# 手动构建一个简单的树结构，在不同的阶段 capture
root = Node(1)
print("Created root node")
dsvis.capture(title="Step 1: Root created")

root.left = Node(2)
print("Added left child")
dsvis.capture(title="Step 2: Added left child")

root.right = Node(3)
print("Added right child")
dsvis.capture(title="Step 3: Added right child")

root.left.left = Node(4)
print("Added left-left child")
dsvis.capture(title="Step 4: Added left-left")

print("\nAll captures added to scheduler, will render on exit...")
