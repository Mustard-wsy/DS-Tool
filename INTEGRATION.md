# 📦 DSVis - 集成使用指南

> DSVis 是一个**可以直接集成到你项目中的库**

## 🚀 最快开始

### 方式 1：复制到你的项目

```bash
your_project/
├── main.py
├── dsvis/              # 复制本项目的 dsvis/ 文件夹
│   ├── __init__.py
│   ├── dsvis.py
│   ├── runtime/
│   └── template.html
└── demo.py
```

### 方式 2：直接导入使用

在 `demo.py` 中：

```python
from dsvis import capture, auto, watch_vars

@capture()
def my_algorithm():
    arr = [5, 2, 8, 1, 9]
    arr.sort()
    return arr

if __name__ == "__main__":
    result = my_algorithm()
```

运行：
```bash
python demo.py
```

就会在浏览器中看到完整的可视化！

---

## 📋 项目结构说明

```
DSVis/（这是我们提供的库）
├── dsvis/              👈 这个目录就是你需要的
│   ├── __init__.py     # 导出所有公共 API
│   ├── dsvis.py        # 核心模块
│   ├── runtime/        # 运行时系统
│   ├── template.html   # 可视化前端
│   └── __init__.py
├── examples/           # 示例代码（供参考）
│   ├── demo_btree.py
│   ├── demo_bubble.py
│   └── ...
├── docs/              # 文档
├── README.md          # 项目说明
└── .gitignore
```

**要点**：只需复制 `dsvis/` 目录到你的项目中！

---

## 💻 实际例子

### 例子 1：在自己的项目中使用

```python
# my_project/main.py
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

项目结构：
```
my_project/
├── main.py          # 上面的代码
├── dsvis/           # 复制来的库
│   ├── __init__.py
│   ├── dsvis.py
│   ├── runtime/
│   └── template.html
```

运行：
```bash
python main.py
```

完成！ 🎉

### 例子 2：监控自定义数据结构

```python
# my_project/custom.py
from dsvis import bind_fields, capture

class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

@capture()
def build_tree():
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    
    # 告诉 dsvis 如何显示这些字段
    bind_fields(root, val=("值", 1), left=("左", 1), right=("右", 1))
    bind_fields(root.left, val=("值", 1), left=("左", 1), right=("右", 1))
    bind_fields(root.right, val=("值", 1), left=("左", 1), right=("右", 1))
    
    return root

if __name__ == "__main__":
    tree = build_tree()
```

---

## ⚙️ 核心 API

### `@capture()` - 捕获函数执行

```python
from dsvis import capture

@capture()
def your_function():
    # ... 代码 ...
    pass
```

**作用**：记录函数执行的每一步

**参数**：
- `title` (可选) - 自定义界面标题

### `@auto()` - 自动追踪变量

```python
from dsvis import auto

@auto()
def your_function():
    x = []
    x.append(1)  # 自动记录
```

**作用**：自动追踪所有变量的变化

### `watch_vars(*variables)` - 观察特定变量

```python
from dsvis import capture, watch_vars

@capture()
def algorithm():
    data = [1, 2, 3]
    watch_vars(data)  # 开始观察
    # ... 对 data 的操作
```

### `bind_fields(obj, **fields)` - 自定义对象显示

```python
from dsvis import bind_fields

class MyClass:
    def __init__(self):
        self.value = None
        self.children = []

obj = MyClass()
bind_fields(
    obj,
    value=("值", 1),        # ("显示名", 层级)
    children=("子节点", 1)
)
```

---

## 📚 完整文档

- [API 参考](docs/API_REFERENCE.md) - 所有函数详解
- [快速参考](docs/INTERFACES_QUICK_REFERENCE.md) - 常用速查
- [高级用法](docs/UNIFIED_MODE_DOCUMENTATION.md) - 深入理解

---

## ✅ 集成检查清单

- [ ] 复制 `dsvis/` 目录到自己的项目
- [ ] 在代码中导入：`from dsvis import capture`
- [ ] 用 `@capture()` 装饰想要可视化的函数
- [ ] 运行脚本，浏览器会自动打开可视化界面

---

## ❓ 常见问题

**Q：DSVis 有依赖项吗？**  
A：没有外部依赖！纯 Python 实现。只需要 Python 3.8+

**Q：可以集成到 Django/Flask 项目中吗？**  
A：可以，用 `@capture()` 装饰任何函数，然后在后端调用即可。

**Q：能否自定义界面样式？**  
A：可以修改 `dsvis/template.html`。查看[高级文档](docs/UNIFIED_MODE_DOCUMENTATION.md)。

**Q：生成的 HTML 文件可以保存吗？**  
A：会自动保存在临时目录，可在高级文档中了解如何定制。

---

## 🎯 使用场景

### 学习算法
在学习数据结构和算法时，用 DSVis 可视化执行过程：
```python
from dsvis import capture

@capture()
def quicksort(arr):
    # 实现快排
    pass
```

### 调试复杂代码
在不确定代码逻辑时，用可视化调试：
```python
@capture()
def complex_function():
    # 可视化每一步
    pass
```

### 教学展示
为学生演示算法工作原理：
```python
@capture(title="二分查找过程")
def binary_search(arr, target):
    # ...
    pass
```

---

## 📦 项目文件说明

| 文件/目录 | 说明 |
|----------|------|
| `dsvis/` | **核心库（必须）** |
| `dsvis/__init__.py` | 公共 API 导出 |
| `dsvis/dsvis.py` | 主模块 |
| `dsvis/runtime/` | 运行时系统 |
| `dsvis/template.html` | 可视化前端 |
| `examples/` | 示例代码（可选参考） |
| `docs/` | 详细文档 |

**你只需要 `dsvis/` 目录！**

---

## 🔗 下一步

1. **查看示例** - 参考 `examples/` 中的 demo 文件
2. **阅读 API 文档** - `docs/API_REFERENCE.md`
3. **开始集成** - 复制 `dsvis/` 到你的项目

---

**准备好集成到你的项目了吗？** 🚀

复制 `dsvis/` 文件夹，然后 `from dsvis import capture`！
