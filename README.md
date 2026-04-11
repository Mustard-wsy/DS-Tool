# DSVis - 数据结构可视化库

> 一个可以直接集成到你项目中的实时可视化工具。让算法执行过程一目了然！

## 快速开始

### 1. 复制库到你的项目

```bash
your_project/
├── main.py         # 你的脚本
└── dsvis/          # 复制本项目的 dsvis/ 文件夹过来
    ├── __init__.py
    ├── dsvis.py
    ├── runtime/
    └── template.html
```

### 2. 在代码中使用

```python
from dsvis import auto

auto()
def my_algorithm():
    arr = [5, 2, 8, 1, 9]
    arr.sort()
    return arr

if __name__ == "__main__":
    my_algorithm()
```

运行后浏览器会自动打开可视化界面。

---

## ✨ 核心特性

- 🎬 **单步执行跟踪** - 看到每一步执行过程
- 📊 **自动数据结构可视化** - 数组、链表、树等自动展示
- 💻 **零配置使用** - 一个装饰器搞定
- 🌐 **浏览器可视化** - 交互式 HTML 界面
- 📦 **易于集成** - 直接复制到项目中，无依赖

---

## 📖 核心概念

### `capture()` - 手动模式-捕获当前状态

```python
from dsvis import capture


def algorithm():
    line 1
    capture() # 将当前这一步加入到捕获队列
    line 2
    pass
```

### `auto()` - 自动模式-捕获可能有用的状态

```python
from dsvis import auto

auto()
def process():
    # 所有变量改变都被追踪
    pass
```
你可以通过 `dsvis.set_mode()` 来切换精简模式和详细模式。在没有特殊声明的时候,模式默认为精简模式。

- 精简模式（coarse）只会捕获**数据结构的关键变化**，包括属性修改（如 `node.next = x`）、容器修改（如 `arr[i] = x`）、删除操作以及可能影响结构的方法调用（如 `list.append()`）。该模式噪音低，适合可视化核心结构变化。

- 详细模式（fine）会捕获**更细粒度的执行过程**，包括所有赋值操作（如 `i = 1`）、每一轮循环的执行，以及所有函数调用语句，从而提供更完整的执行轨迹。


---

## 实际例子

### 例子 1：排序可视化

```python
import dsvis
dsvis.set_mode("fine")
dsvis.auto()
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

if __name__ == "__main__":
    bubble_sort([3, 1, 4, 1, 5, 9])
```

### 例子 2：自定义数据结构

```python
from dsvis import auto, bind_fields
auto()

class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None


def build_tree():
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    
    bind_fields(root, val=("值", 1), left=("左", 1), right=("右", 1))
    return root

if __name__ == "__main__":
    tree = build_tree()
```

> 你可以从项目根目录所有`demo_*.py`来查看更多具体的本项目应用场景

## 📁 项目结构

```
DSVis/
├── dsvis/              # 👈 复制这个到你的项目
│   ├── __init__.py     # 公共 API 导出
│   ├── dsvis.py        # 核心模块
│   ├── runtime/        # 运行时系统
│   └── template.html   # 可视化前端
├── docs/              # 详细文档
├── README.md          # 本文件
└── .gitignore
```

**只需 `dsvis/` 目录就能工作！**



## 🚀 集成步骤

```bash
# 1. 将 dsvis/ 目录复制到你的项目
cp -r dsvis/ my_project/

# 2. 在代码中导入
import dsvis

# 3. 使用接口
dsvis.auto()
def algorithm():
    pass

# 4. 运行
python my_script.py
```

---

## 📚 完整文档导航

| 文档 | 内容 |
|------|------|
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | 完整 API 文档 |
| [docs/INTERFACES_QUICK_REFERENCE.md](docs/INTERFACES_QUICK_REFERENCE.md) | 快速速查表 |
| [docs/UNIFIED_MODE_DOCUMENTATION.md](docs/UNIFIED_MODE_DOCUMENTATION.md) | 深入理解 |
| [examples/](examples/) | 代码示例 |

---

**版本**: 0.0.1 | **最后更新**: 2026-04-11
