# DSVis — 数据结构可视化库

> 零依赖、即插即用的算法执行过程可视化工具。一行调用，浏览器自动打开交互式界面。

## 快速开始

```python
import dsvis
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

运行后浏览器自动打开可视化界面，提供单步导航、调用栈查看、断点调试（默认开启）。

---

## ✨ 核心特性

- 🎬 **单步执行跟踪** — 每条语句的执行状态一目了然
- 📊 **自动数据结构可视化** — 数组、链表、树、图自动渲染
- 🎯 **断点调试** — 点击行号插入断点，默认开启，前向导航自动命中
- 💻 **零配置** — 复制 `dsvis/` 目录到项目即可使用
- 🌐 **交互式界面** — 三栏布局（调用栈 | 图 | 源代码）
- 📦 **零依赖** — 仅用 Python 标准库 + 前端 G6 CDN

---

## 📖 接口速览

| 接口 | 用途 |
|------|------|
| `auto()` | 脚本顶部调用，自动追踪整段代码 |
| `capture()` | 手动在此处插入一个快照 |
| `set_mode(mode)` | 切换采集粒度：`"coarse"` / `"fine"` / `"line"` ,默认为"fine"|
| `disable_breakpoints()` | 关闭断点模式（默认开启） |
| `watch_vars(*names)` | 强制将指定变量作为图节点展示 |
| `bind_fields(obj, ...)` | 绑定对象字段到动画组（适合自定义数据结构） |

---

## 🧩 接口详解

### `auto()` — 自动追踪模式

在脚本顶部调用，自动对整段代码做 AST 插桩：

```python
import dsvis
dsvis.auto()

def my_algorithm():
    arr = [1, 2, 3]
    arr[0] = 42

if __name__ == "__main__":
    my_algorithm()
```

`auto()` 会自动在关键位置注入触发器，执行完毕后生成可视化界面。

---

### `capture()` — 手动快照

在代码中手动插入捕获点，精确控制哪些时刻被记录。

```python
from dsvis import capture

def algorithm():
    a = [1, 2, 3]
    capture()                        # 快照 1
    a[0] = 99
    capture(focus_vars=["a"])        # 快照 2，强制展示变量 a

algorithm()
```

参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_nodes` | `300` | 图节点数上限 |
| `include_private` | `False` | 是否包含 `_` 开头的私有属性 |
| `focus_vars` | `None` | 强制展示的变量名列表 |
| `pointer_watchers` | `None` | 指针观察器（索引→容器） |

---

### `set_mode(mode)` — 采集粒度

```python
from dsvis import set_mode

set_mode("line")   # 每行都采集（默认）
set_mode("fine")   # 所有赋值 + 函数调用
set_mode("coarse") # 仅关键结构变化
```

| 模式 | 采集内容 | 适用场景 |
|------|----------|----------|
| `coarse` | 结构变化（`arr[i]=x`, `node.next=x`, `list.append()`） | 概览算法结构 |
| `fine` | 所有赋值、循环、函数调用 | 细粒度追踪 |
| `line` | 每条语句 | 断点调试 |

---

### `disable_breakpoints()` — 关闭断点

断点默认开启。关闭后采集粒度由 `set_mode()` 决定（默认 `"fine"`），
前端不再显示逐行步进按钮且断点点击失效：

```python
from dsvis import disable_breakpoints

disable_breakpoints()

# 此时 set_mode 独立生效，可自由切换 coarse/fine/line
from dsvis import set_mode
set_mode("coarse")  # 只看关键结构变化
```

### `watch_vars(*names)` — 变量关注

强制将指定变量作为图节点展示，即使其类型本不会被渲染。

```python
from dsvis import watch_vars

watch_vars("pivot", "left")   # 全局生效

def quicksort(arr):
    pivot = arr[0]   # pivot 会作为节点显示
    left = []        # left 也会显示
    # ...
```

也可作为装饰器，仅作用于当前函数：

```python
@watch_vars("i", "j")
def loop():
    for i in range(3):
        for j in range(3):
            pass
```

---

### `bind_fields(obj, **field_specs)` — 字段绑定

将对象的多个容器字段绑定到动画组，适合树、链表等自定义结构。

```python
from dsvis import bind_fields

class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

def build_tree():
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)

    bind_fields(root, left=("A", 1), right=("A", 1))
    return root

build_tree()
```

支持两种写法：

```python
bind_fields(obj, keys=("A", 3), children=("A", 1))   # 元组 (组名, 比例)
bind_fields(obj, keys="A:3", vals="B:2")              # 字符串 "组名:比例"
```

---

## 📁 项目结构

```
DSVis/
├── dsvis/                  # 👈 复制这个目录到你的项目
│   ├── __init__.py          # 公共 API
│   ├── dsvis.py             # 入口 + 布局工具
│   ├── introspection.py     # 类型内省
│   ├── stack_serializer.py  # 调用栈序列化
│   ├── graph_builder.py     # 图遍历（BFS）
│   ├── card_renderer.py     # G6 卡片布局 + HTML 生成
│   ├── field_binding.py     # 字段绑定
│   ├── styles.css           # 前端样式
│   ├── template.html        # 前端骨架
│   └── runtime/             # 运行时（AST 插桩 + 调度）
└── README.md
```

**只复制 `dsvis/` 目录即可使用。**

---

## ⌨️ 界面快捷键

| 按键 | 行为 |
|------|------|
| `←` | 上一个执行步骤 |
| `→` | 下一个执行步骤 |
| `Esc` | 取消悬停高亮 |
| 点击行号 | 插入 / 移除断点 |

---

## 📋 更多示例

项目根目录下的 `demo_*.py` 文件涵盖了排序、B 树、哈希表、队列、栈等典型场景，可以直接运行：

```bash
python demo_btree.py
python demo_bubble.py
python demo_hash.py
```
