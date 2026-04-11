#!/usr/bin/env python3
"""
验证修复后的 capture 模式
应该正确生成 debug_template.html
"""

import dsvis

class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

print("开始创建链表...")

head = Node(1)
print("✓ 创建节点1")
dsvis.capture(title="Step 1: 创建节点1")

head.next = Node(2)
print("✓ 添加节点2")
dsvis.capture(title="Step 2: 添加节点2")

head.next.next = Node(3)
print("✓ 添加节点3")
dsvis.capture(title="Step 3: 添加节点3")

print("\n✓ 所有 capture 完成，将在程序结束时生成 HTML...")
print("✓ 请检查浏览器中是否打开了 debug_template.html")
