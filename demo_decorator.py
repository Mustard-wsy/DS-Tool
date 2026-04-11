"""
DSVis 装饰器演示

本示例展示 DSVis 提供的所有装饰器方式：
1. @auto() - 自动追踪整个脚本（需要在主函数上）
2. @watch_vars() - 监视特定变量的变化
3. observe() - 手动触发观察（不是装饰器，但是观察工具）
"""

import dsvis


# ============================================
# 示例 1: @watch_vars 装饰器 - 监视特定变量
# ============================================

@dsvis.watch_vars('x', 'accumulator')
def calculate_sum():
    """
    使用 @watch_vars 装饰器监视特定变量的每次变化。
    只有指定的变量变化时才会被记录。
    """
    accumulator = 0
    
    for x in range(5):
        accumulator += x
        
    return accumulator


# ============================================
# 示例 2: observe() - 手动触发观察
# ============================================

def manual_observation():
    """
    使用 observe() 在代码中的特定位置手动触发观察。
    """
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    
    # 第一次观察
    dsvis.observe(vars=['data'])
    
    # 处理数据
    data.sort()
    
    # 第二次观察
    dsvis.observe(vars=['data'])
    
    return data


# ============================================
# 示例 3: @auto() 装饰器 - 自动追踪整个函数
# ============================================

def fibonacci(n):
    """计算斐波那契数列"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@dsvis.auto()
def demo_auto():
    """
    @auto() 装饰器会自动追踪函数内的所有执行步骤。
    所有变量变化都会被可视化。
    """
    print("开始斐波那契计算...")
    
    fib_list = []
    for i in range(7):
        result = fibonacci(i)
        fib_list.append(result)
    
    return fib_list


# ============================================
# 示例 4: bind_fields() 与 @auto()
# ============================================

class SimpleList:
    """演示 bind_fields 用于数据结构可视化"""
    
    def __init__(self):
        self.items = []
        self.size = 0
        
        # 绑定字段用于可视化
        dsvis.bind_fields(
            self,
            items=("Data", 3),  # 分组名为 "Data"，每次显示 3 个
            size=("Meta", 1)     # 分组名为 "Meta"，显示尺寸
        )
    
    def add(self, value):
        self.items.append(value)
        self.size += 1
    
    def remove(self):
        if self.items:
            self.items.pop()
            self.size -= 1


@dsvis.auto()
def demo_with_bind_fields():
    """
    演示 bind_fields 与 @auto() 的配合使用。
    bind_fields 定义了哪些字段如何分组显示。
    """
    my_list = SimpleList()
    
    # 逐个添加元素
    for value in [10, 20, 30, 40, 50, 60]:
        my_list.add(value)
    
    # 移除一些元素
    my_list.remove()
    my_list.remove()
    
    return my_list


# ============================================
# 程序入口
# ============================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("DSVis 装饰器演示")
    print("=" * 60)
    
    # 演示选择
    demos = {
        "1": ("@watch_vars 监视特定变量", calculate_sum),
        "2": ("observe() 手动观察", manual_observation),
        "3": ("@auto() 自动追踪", demo_auto),
        "4": ("bind_fields + @auto()", demo_with_bind_fields),
    }
    
    print("\n可用的演示：")
    for key, (desc, _) in demos.items():
        print(f"  {key}: {desc}")
    
    choice = input("\n请选择要运行的演示 (1-4，或按 Enter 运行全部): ").strip()
    
    if choice in demos:
        # 运行单个演示
        desc, func = demos[choice]
        print(f"\n运行：{desc}")
        print("-" * 60)
        result = func()
        print(f"\n结果: {result}")
    else:
        # 运行全部演示
        print("\n运行所有演示...\n")
        
        print("1. @watch_vars 示例")
        print("-" * 60)
        result1 = calculate_sum()
        print(f"求和结果: {result1}\n")
        
        print("2. observe() 示例")
        print("-" * 60)
        result2 = manual_observation()
        print(f"排序结果: {result2}\n")
        
        print("3. @auto() 示例")
        print("-" * 60)
        demo_auto()
        
        print("4. bind_fields + @auto() 示例")
        print("-" * 60)
        demo_with_bind_fields()
