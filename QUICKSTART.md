# 🚀 DSVis - 快速开始指南

**让你 5 分钟上手 DSVis 数据结构可视化工具**

## ⚡ 最快开始（3 步）

### 1️⃣ 查看示例
```bash
cd src
python Btree.py        # B树示例
python Bubble.py       # 冒泡排序示例
python hash.py         # 哈希表示例
python queue.py        # 队列示例
python stack.py        # 栈示例
python LongList.py     # 长链表示例
```

每个示例都会在浏览器中打开可视化界面！

### 2️⃣ 在你的代码中使用

创建文件 `my_code.py`：

```python
from dsvis import capture

@capture()
def my_function():
    arr = [3, 1, 2]
    arr.sort()
    return arr

if __name__ == "__main__":
    result = my_function()
```

运行：
```bash
python my_code.py
```

### 3️⃣ 查看可视化
浏览器自动打开，显示代码执行的每一步！

---

## 📚 核心概念

### `@capture()` - 捕获执行步骤
```python
from dsvis import capture

@capture()
def algorithm():
    # 你的代码
    pass
```
**用途**: 记录函数执行的每一步，支持多次调用的单步跟踪

### `@auto()` - 自动追踪变量
```python
from dsvis import auto

@auto()
def process():
    x = []
    x.append(1)
```
**用途**: 自动记录变量的每次改变

### `watch_vars()` - 手动观察变量
```python
from dsvis import watch_vars, capture

@capture()
def my_func():
    data = [1, 2, 3]
    watch_vars(data)  # 开始观察
    # ... 对 data 的操作
```

---

## 🎯 实际例子

### 例子 1：排序可视化
```python
from dsvis import capture

@capture()
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

if __name__ == "__main__":
    result = bubble_sort([3, 1, 4, 1, 5, 9, 2, 6])
```

运行后会看到：
- 每次比较和交换的过程
- 数组的实时变化
- 执行进度和步数

### 例子 2：数据结构追踪
```python
from dsvis import auto

@auto()
class MyStack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        return self.items.pop()

# 使用
stack = MyStack()
stack.push(1)
stack.push(2)
stack.pop()
```

---

## 🔧 常用配置

### 自定义界面标题
```python
from dsvis import capture

@capture(title="我的算法演示")
def algorithm():
    pass
```

### 观察特定的字段
```python
class TreeNode:
    def __init__(self):
        self.value = None
        self.left = None
        self.right = None

from dsvis import bind_fields

node = TreeNode()
bind_fields(node, value=("V", 1), left=("L", 1), right=("R", 1))
```

---

## 📖 完整文档

- [API 详细参考](../docs/API_REFERENCE.md) - 所有函数和类
- [快速参考](../docs/INTERFACES_QUICK_REFERENCE.md) - 常用接口速查表
- [高级用法](../docs/UNIFIED_MODE_DOCUMENTATION.md) - 深入理解工作原理

---

## ✅ 检查表

- [ ] 我已经看过至少一个示例（在 `src/` 目录）
- [ ] 我理解了 `@capture()` 的用法
- [ ] 我创建了一个简单的脚本来测试
- [ ] 我能看到浏览器中的可视化

---

## 🆘 常见问题

### Q: 为什么没有看到可视化界面？
**A**: 确保：
1. 你在 `src/` 目录运行脚本（`cd src && python your_script.py`）
2. 你的浏览器没有被阻止弹出窗口
3. 脚本中使用了 `@capture()` 或 `@auto()`

### Q: 如何修改可视化的样式？
**A**: 可视化的样式由 `src/template.html` 决定。查看[高级文档](../docs/UNIFIED_MODE_DOCUMENTATION.md)了解自定义选项。

### Q: 能否在 Jupyter Notebook 中使用？
**A**: 目前不支持，但你可以在脚本中运行然后在浏览器中查看。

---

## 🎓 进阶学习路径

1. **初级** (15 分钟)
   - 运行 `src/Btree.py` 或 `src/Bubble.py`
   - 理解可视化界面的含义

2. **中级** (30 分钟)
   - 创建自己的脚本使用 `@capture()`
   - 尝试 `bind_fields()` 来观察数据结构

3. **高级** (1 小时)
   - 阅读[完整 API 文档](../docs/API_REFERENCE.md)
   - 使用 `@auto()` 进行自动追踪
   - 自定义界面样式

---

## 📞 需要帮助？

1. 查看 [API 参考](../docs/API_REFERENCE.md)
2. 运行并研究 `src/` 目录下的示例
3. 查看 `examples/run_ast.py` 了解高级用法

---

**准备好了？进入 `src/` 目录，运行你的第一个示例吧！** 🎉

```bash
cd src
python Btree.py  # 或任何其他示例
```

