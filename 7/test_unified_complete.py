#!/usr/bin/env python3
"""
完整测试：验证统一的 capture 模式
- 多个 capture 点
- 数据变化检测（只记录变化的步骤）
- 步骤之间的导航
"""

import dsvis
from runtime.scheduler import scheduler

class LinkedListNode:
    def __init__(self, val):
        self.val = val
        self.next = None

# 构建链表，在各个阶段 capture
print("=== 测试统一的 capture 模式 ===\n")

head = LinkedListNode(10)
print("✓ 创建了头节点 (val=10)")
dsvis.capture(title="Step 1: 创建头节点")

head.next = LinkedListNode(20)
print("✓ 添加了第二个节点 (val=20)")
dsvis.capture(title="Step 2: 添加第二个节点")

head.next.next = LinkedListNode(30)
print("✓ 添加了第三个节点 (val=30)")
dsvis.capture(title="Step 3: 添加第三个节点")

# 这个 capture 不会添加到 steps，因为数据没有实际变化（capture之间没有结构变化）
print("✓ 重复 capture（不会创建新的 step，因为数据未变化）")
dsvis.capture(title="重复capture")

head.next.next.next = LinkedListNode(40)
print("✓ 添加了第四个节点 (val=40)")
dsvis.capture(title="Step 4: 添加第四个节点")

print("\n统计：")
print(f"  - scheduler.steps 中的步骤数: {len(scheduler.steps)}")
print(f"  - 期望：4 个步骤（第2个capture因为数据未变化应该被跳过）")
print("\n程序结束时，所有步骤将被 scheduler.flush() 一起渲染到 debug_template.html")
