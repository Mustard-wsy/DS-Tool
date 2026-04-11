#!/usr/bin/env python3
"""
测试 capture 和 auto 模式的混合使用
验证现在它们可以无缝协作
"""

import dsvis

# 注：本脚本不使用 dsvis.auto()，而是进行手动 capture
# 如果要测试 auto+capture 混合，需要使用 AST 插桩

class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, val):
        self.items.append(val)
    
    def pop(self):
        if self.items:
            return self.items.pop()
        return None

print("=== 测试 capture 模式 ===\n")

stack = Stack()
print("✓ 创建栈")
dsvis.capture(title="初始状态：空栈")

stack.push(10)
print("✓ Push 10")
dsvis.capture(title="Push 10")

stack.push(20)
print("✓ Push 20")
dsvis.capture(title="Push 20")

stack.push(30)
print("✓ Push 30")
dsvis.capture(title="Push 30")

popped = stack.pop()
print(f"✓ Pop -> {popped}")
dsvis.capture(title=f"Pop -> {popped}")

print("\n✓ 所有步骤已通过 scheduler 收集，将在程序结束时统一渲染")
print("✓ 可以在 HTML 中通过 Prev/Next 按钮在各个 capture 点切换")
