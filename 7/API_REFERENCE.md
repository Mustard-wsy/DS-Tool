# DSVis 对外接口文档

## 核心接口

### 1. `dsvis.capture()`

**激活方式：** 手动在代码中调用

**函数签名：**
```python
def capture(
    title="AutoViz Snapshot",
    max_nodes=300,
    include_private=False,
    include_containers=None,
    focus_vars=None,
    pointer_watchers=None,
    layout=None,
    _caller_frame=None,
)
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|-----|
| `title` | str | "AutoViz Snapshot" | 步骤的标签名称，显示在调试 HTML 的步骤列表中 |
| `max_nodes` | int | 300 | 最多显示的对象节点数 |
| `include_private` | bool | False | 是否显示对象的私有属性（下划线开头的字段） |
| `include_containers` | bool \| None | None | 是否递归显示容器（list/dict/set 等）内部元素；None 时根据 mode 决定 |
| `focus_vars` | set \| list | None | 指定重点监控的变量名，这些变量会被优先显示 |
| `pointer_watchers` | list | None | 指针监听列表，格式：`[("pointer_name", "container_name"), ...]` |
| `layout` | dict \| None | None | 图表布局配置（**已弃用**，保留以向后兼容） |
| `_caller_frame` | frame | None | 内部使用，不应由用户设置 |

**返回值：** None（HTML 在程序结束时通过 `atexit` 自动生成）

**工作流程：**
1. 调用 `capture()` 时，将当前状态快照添加到 scheduler 的 steps 列表
2. 自动检测数据是否有变化（通过签名对比）
3. 如果数据变化，新增一个 step；否则跳过
4. 程序结束时，scheduler 自动 flush，生成包含所有 steps 的调试 HTML
5. HTML 打开后，可用 Prev/Next 按钮在各个 capture 点间导航

**使用示例：**

```python
import dsvis

class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

root = Node(10)
dsvis.capture(title="创建root节点")

root.next = Node(20)
dsvis.capture(title="添加Next指针")

root.next.next = Node(30)
dsvis.capture(title="添加Next的Next")

# 程序结束时，生成 debug_template.html，包含 3 个步骤
```

---

### 2. `dsvis.auto()`

**激活方式：** 在脚本顶部显式调用（仅需一次）

**函数签名：**
```python
def auto():
    """
    显式启用 AST 自动插桩模式
    """
```

**参数说明：** 无参数

**返回值：** None（会启动 AST 转换并执行脚本）

**工作流程：**
1. 调用 `auto()` 后，脚本通过 AST 修改进行静态分析
2. 在以下位置自动插入 `trigger()` 调用：
   - 赋值语句（特别是构造函数调用）
   - 容器结构修改（`[]`，`.attr` 赋值）
   - 方法调用（黑名单除外：`__init__`, `__repr__` 等）
   - 循环体迭代（fine 模式）
3. 每个自动 trigger 都将快照添加到 scheduler
4. 程序结束时，scheduler 自动 flush，生成调试 HTML

**使用示例：**

```python
import dsvis
dsvis.auto()  # 放在脚本最开始

class Node:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

root = Node(1)
root.left = Node(2)      # 自动 trigger
root.left.right = Node(3) # 自动 trigger
root.right = Node(4)      # 自动 trigger

# 程序结束时自动生成 HTML
```

---

### 3. `dsvis.observe()`

**激活方式：** 手动在关键位置调用

**函数签名：**
```python
def observe(tag=None, vars=None, pointers=None):
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|-----|
| `tag` | str \| None | None | 步骤标签 |
| `vars` | set \| list | None | 要关注的变量名集合 |
| `pointers` | list | None | 指针列表，同 capture 的 pointer_watchers |

**返回值：** None

**说明：** 与 `capture()` 类似，但仅监控指定的变量，其他变量不显示

**使用示例：**

```python
import dsvis

class Stack:
    def __init__(self):
        self.items = []

stack = Stack()
stack.items.append(10)
dsvis.observe(tag="Push 10", vars={"stack"})

stack.items.append(20)
dsvis.observe(tag="Push 20", vars={"stack"})
```

---

### 4. `dsvis.observe_ptr()`

**激活方式：** 手动在关键位置调用（监听指针变化）

**函数签名：**
```python
def observe_ptr(name, container, tag=None):
```

**参数说明：**

| 参数 | 类型 | 说明 |
|-----|------|-----|
| `name` | str | 指针变量的名称 |
| `container` | str | 容器变量的名称 |
| `tag` | str \| None | 步骤标签 |

**返回值：** None

**说明：** 监听一个整数指针在容器中的位置变化

**使用示例：**

```python
import dsvis

class Array:
    def __init__(self, data):
        self.data = data

arr = Array([10, 20, 30, 40, 50])
i = 0
dsvis.observe_ptr("i", "arr.data", tag="指针在位置0")

i = 2
dsvis.observe_ptr("i", "arr.data", tag="指针移到位置2")
```

---

### 5. `dsvis.watch_vars()`

**激活方式：** 作为函数装饰器使用

**函数签名：**
```python
def watch_vars(*names, pointers=None):
```

**参数说明：**

| 参数 | 类型 | 说明 |
|-----|------|-----|
| `*names` | str 变长参数 | 要监控的变量名 |
| `pointers` | list | 可选的指针列表 |

**返回值：** 装饰器函数

**说明：** 使用装饰器包装一个函数，该函数内的所有 trigger 都会优先显示指定的变量

**使用示例：**

```python
import dsvis

@dsvis.watch_vars("root", "queue")
def build_tree():
    class Node:
        def __init__(self, val):
            self.val = val
            self.left = None
            self.right = None
    
    from collections import deque
    root = Node(1)
    queue = deque([root])
    # ...

# 调用该函数（配合 auto() 使用）
build_tree()
```

---

### 6. `dsvis.set_mode()`

**激活方式：** 在脚本中调用以改变工作模式

**函数签名：**
```python
def set_mode(mode):
```

**参数说明：**

| 参数 | 可选值 | 说明 |
|-----|-------|-----|
| `mode` | "coarse" \| "fine" | "coarse"：只在关键点（赋值、方法调用）插桩；"fine"：详细模式，包含循环迭代 |

**返回值：** None

**使用示例：**

```python
import dsvis

dsvis.set_mode("fine")  # 详细模式
dsvis.auto()

# 代码会被更密集地插桩
```

---

### 7. `dsvis.bind_fields()`

**激活方式：** 在对象创建后调用，用于控制容器字段的渲染方式

**函数签名：**
```python
def bind_fields(obj, **field_specs):
```

**参数说明：**

| 参数 | 类型 | 说明 |
|-----|------|-----|
| `obj` | object | 要绑定的对象 |
| `**field_specs` | dict | 字段绑定规格，格式：`field_name=("group_name", ratio)` |

**返回值：** None

**说明：** 用于控制如何在多个容器字段间同步显示元素（分组显示）

**使用示例：**

```python
import dsvis

class Node:
    def __init__(self):
        self.keys = []
        self.values = []

node = Node()
node.keys = [1, 2, 3, 4, 5, 6]
node.values = ['a', 'b', 'c', 'd', 'e', 'f']

# 将 keys 和 values 分组，3:1 的比例显示
dsvis.bind_fields(node, keys=("A", 3), values=("A", 1))
dsvis.capture(title="绑定字段")
```

---

### 8. `dsvis.bind_field()`

**激活方式：** 在对象创建后调用，逐个绑定字段

**函数签名：**
```python
def bind_field(obj, field, group, ratio=1):
```

**参数说明：**

| 参数 | 类型 | 说明 |
|-----|------|-----|
| `obj` | object | 要绑定的对象 |
| `field` | str | 字段名 |
| `group` | str | 分组名 |
| `ratio` | int | 每轮取多少个元素（1=同步，3=该字段取3个） |

**返回值：** None

**使用示例：**

```python
dsvis.bind_field(node, "keys", "A", 3)
dsvis.bind_field(node, "values", "A", 1)
```

---

### 9. `dsvis.bind_lists()` / `@dsvis.bind_lists()`

**激活方式：** 作为类装饰器使用

**函数签名：**
```python
def bind_lists(*tokens):
```

**参数说明：**

| 参数 | 类型 | 格式 | 说明 |
|-----|------|------|-----|
| `*tokens` | str 列表 | "field@group:ratio" | 字符串格式的绑定说明 |

**返回值：** 装饰器

**使用示例：**

```python
import dsvis

@dsvis.bind_lists("keys@A:3", "values@A:1", "children@B:1")
class Node:
    def __init__(self):
        self.keys = []
        self.values = []
        self.children = []

# Node 的实例会自动应用这些绑定
```

---

## 工作模式对比

| 特性 | capture | auto | observe |
|-----|---------|------|---------|
| 激活方式 | 手动调用 | 脚本顶部 | 手动调用 |
| 代码修改 | 需要手动添加 | AST 自动修改 | 需要手动添加 |
| 触发点 | 显式指定 | 自动检测 | 手动指定 |
| 灵活性 | 高 | 低 | 中等 |
| 性能开销 | 低 | 中等 | 低 |
| 最终界面 | debug_template.html | debug_template.html | debug_template.html |

---

## 输出文件

所有模式最终都使用同一个调试界面：

- **debug_template.html** - 多步骤调试界面
  - 左侧：数据结构可视化图表
  - 右侧：源代码查看器（自动滚动到当前行）
  - 底部：步骤导航（Prev/Next 按钮、步骤计数、自动缩放选项）

---

## 常见用法

### 场景1：快速查看数据结构变化

```python
import dsvis

class Tree:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

root = Tree(1)
dsvis.capture()

root.left = Tree(2)
dsvis.capture()

root.right = Tree(3)
dsvis.capture()
```

### 场景2：详细追踪所有操作

```python
import dsvis
dsvis.auto()

class LinkedList:
    def __init__(self):
        self.head = None
    
    def insert(self, val):
        # ...自动插桩会在这里追踪

# 代码会自动生成完整的调试 HTML
```

### 场景3：混合手动和自动监控

```python
import dsvis
dsvis.auto()

result = some_algorithm()
dsvis.observe(tag="算法完成", vars={"result"})
```

---

## 配置和环境变量

| 环境变量 | 说明 |
|---------|-----|
| `DSVIS_AST_RUNNING` | 内部使用，标记 AST 转换是否进行中 |
| `DSVIS_MODE` | 工作模式，"coarse" 或 "fine" |

---

## 已弃用的接口

| 接口 | 替代方案 |
|-----|---------|
| `layout=None` 参数 | 不再需要显式传递，系统自动处理布局 |
| 单个 HTML 快照（旧 capture） | 改用统一的多步骤 debug_template.html |

