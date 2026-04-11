# DSVis 对外接口快速参考

## 📋 接口列表

### 核心模式激活

#### 1️⃣ `capture()` - 手动快照

```python
import dsvis

# 基础用法
dsvis.capture()
dsvis.capture(title="My Step")

# 完整用法
dsvis.capture(
    title="Step Name",              # 步骤标签
    max_nodes=300,                  # 最多显示节点数
    include_private=False,          # 显示私有属性
    focus_vars={"var1", "var2"},   # 关注的变量
    pointer_watchers=[("i", "arr")], # 指针监听
)
```

**特点：** 
- 手动调用，灵活性高
- 自动检测变化（去重）
- 所有 capture 被收集到一个 HTML

---

#### 2️⃣ `auto()` - 自动插桩

```python
import dsvis
dsvis.auto()  # 必须在脚本最开始

# 之后的代码会自动被 AST 修改，在关键点自动插桩
# - 赋值语句
# - 方法调用
# - 容器修改

class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

root = Node(1)       # ← 自动 trigger
root.next = Node(2)  # ← 自动 trigger
```

**特点：**
- 自动化程度高
- 需要 AST 修改
- 性能开销

---

### 观察接口

#### 3️⃣ `observe()` - 自定义观察点

```python
import dsvis

# 基础用法
dsvis.observe(tag="标签")

# 监控特定变量
dsvis.observe(
    tag="Step Name",
    vars={"stack", "queue"},
    pointers=[("i", "arr")]
)
```

---

#### 4️⃣ `observe_ptr()` - 指针监听

```python
# 简便方法：监听整数指针在数组中的位置
dsvis.observe_ptr("i", "arr", tag="移动指针")

# 等价于
dsvis.observe(tag="移动指针", pointers=[("i", "arr")])
```

---

### 装饰器

#### 5️⃣ `@watch_vars(*names)` - 函数级变量监听

```python
import dsvis

@dsvis.watch_vars("root", "queue")
def build_tree():
    # 这个函数内的每个 trigger 都会优先显示 root 和 queue
    pass
```

---

### 字段绑定

#### 6️⃣ `bind_fields()` - 对象字段绑定

```python
# 控制多个容器字段的同步显示（分组显示）
dsvis.bind_fields(
    node,
    keys=("group_A", 3),    # keys 字段，3:1 比例
    values=("group_A", 1),  # values 字段
)

# 单字段版本
dsvis.bind_field(node, "keys", "group_A", ratio=3)
```

---

#### 7️⃣ `@bind_lists()` - 类装饰器方式

```python
@dsvis.bind_lists(
    "keys@A:3",      # 字段名 @ 分组名 : 比例
    "values@A:1",
    "children@B:1"
)
class Node:
    def __init__(self):
        self.keys = []
        self.values = []
        self.children = []

# 该类的所有实例自动应用这些绑定
```

---

### 配置

#### 8️⃣ `set_mode()` - 工作模式切换

```python
import dsvis

# "coarse": 只在赋值、方法调用处触发（默认）
# "fine": 详细模式，包括循环迭代
dsvis.set_mode("fine")

dsvis.auto()
# 代码会被更密集地插桩
```

---

## 🎯 快速对比

| 接口 | 用途 | 调用方式 | 代码改动 |
|-----|-----|---------|--------|
| `capture()` | 手动快照 | 直接调用 | 需要 |
| `auto()` | 自动插桩 | 脚本顶部一次 | 不需要（AST 修改） |
| `observe()` | 自定义观察 | 直接调用 | 需要 |
| `observe_ptr()` | 指针监听 | 直接调用 | 需要 |
| `@watch_vars()` | 函数级关注 | 装饰器 | 需要 |
| `bind_fields()` | 字段绑定 | 直接调用 | 需要 |
| `@bind_lists()` | 类级字段绑定 | 类装饰器 | 可选 |
| `set_mode()` | 模式配置 | 调用 | 需要 |

---

## 📊 常用场景

### 场景 1: 快速调试链表

```python
import dsvis

class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

head = Node(1)
dsvis.capture(title="创建head")

head.next = Node(2)
dsvis.capture(title="添加next")

head.next.next = Node(3)
dsvis.capture(title="继续添加")
```

**输出：** debug_template.html，包含 3 个步骤，可用 Prev/Next 导航

---

### 场景 2: 详细追踪算法执行

```python
import dsvis
dsvis.auto()  # 自动追踪所有操作

class BST:
    def insert(self, val):
        # 所有操作都会自动被追踪
        pass

bst = BST()
bst.insert(5)
bst.insert(3)
bst.insert(7)
```

**输出：** debug_template.html，包含所有自动 trigger 的步骤

---

### 场景 3: 监听特定变量和指针

```python
import dsvis

arr = [10, 20, 30, 40, 50]
left, right = 0, 4

# 移动指针时观察
while left < right:
    dsvis.observe_ptr("left", arr, tag=f"left={left}")
    left += 1
    dsvis.observe_ptr("right", arr, tag=f"right={right}")
    right -= 1
```

---

### 场景 4: 分组显示字段

```python
import dsvis

class BTree:
    def __init__(self):
        self.keys = []
        self.children = []
    
    def insert(self, key):
        self.keys.append(key)
        # 由于绑定，keys 和 children 会同步跟踪

# 应用字段绑定
btree = BTree()
dsvis.bind_fields(btree, keys=("A", 2), children=("A", 1))

btree.keys.append(10)
dsvis.capture(title="插入key 10")

btree.children.append(None)
dsvis.capture(title="扩展children")
```

---

## 📁 输出文件

所有模式都输出同一个调试界面格式：

**debug_template.html** 
- 左：数据结构可视化（G6 图表）
- 中：源代码查看器
- 右/下：步骤导航和控制

---

## ⚙️ 常用参数

### capture / observe 的共同参数

| 参数 | 默认值 | 说明 |
|-----|--------|-----|
| `title` / `tag` | 无 | 步骤的显示名称 |
| `max_nodes` | 300 | 最多显示多少个对象节点 |
| `include_private` | False | 是否显示 `_field` 这样的私有字段 |
| `focus_vars` | None | 优先显示的变量名集合 |
| `pointer_watchers` | None | 指针监听列表：`[("i", "arr"), ...]` |

---

## 🔧 调试技巧

### Tip 1: 追踪特定变量

```python
# 只看 tree 这个变量的变化
dsvis.capture(focus_vars={"tree"})
```

### Tip 2: 限制显示节点数

```python
# 大型数据结构：只显示前 100 个节点
dsvis.capture(max_nodes=100)
```

### Tip 3: 查看私有属性

```python
# BST 有 _size 等内部属性，需要显示的话：
dsvis.capture(include_private=True)
```

### Tip 4: 监听指针位置

```python
# 追踪 i 在 arr 中的位置（自动显示 arr[i] 的值）
dsvis.observe_ptr("i", "arr")
```

---

## 📎 相关文档

- **API_REFERENCE.md** - 详细的接口文档
- **UNIFIED_MODE_DOCUMENTATION.md** - 设计理念和工作流
- **BUGFIX_SUMMARY.md** - 最近的修复总结

---

## ⚡ 快速开始

### 最简单的方式 - Capture

```python
import dsvis

# 定义你的类
class Node:
    pass

# 在关键点调用 capture
obj = Node()
dsvis.capture(title="Initial state")

# ...修改对象...

dsvis.capture(title="After changes")

# 程序结束时自动打开 debug_template.html
```

### 最自动的方式 - Auto

```python
import dsvis
dsvis.auto()  # 一行代码

# 之后的代码会自动被追踪
obj = Node()
obj.next = Node()
obj.next.next = Node()

# 程序结束时自动生成完整的调试 HTML
```

---

**结论：** 选择 `capture()` 以获得最大控制，选择 `auto()` 以最小化代码改动。
