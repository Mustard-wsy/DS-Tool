# DSVis - 数据结构可视化库

> 一个可以直接集成到你项目中的实时可视化工具。让算法执行过程一目了然！

## ⚡ 最快开始（2 步）

### 1. 复制库到你的项目

```bash
your_project/
├── main.py
└── dsvis/          # 复制本项目的 dsvis/ 文件夹过来
    ├── __init__.py
    ├── dsvis.py
    ├── runtime/
    └── template.html
```

### 2. 在代码中使用

```python
from dsvis import capture

@capture()
def my_algorithm():
    arr = [5, 2, 8, 1, 9]
    arr.sort()
    return arr

if __name__ == "__main__":
    my_algorithm()
```

**就这样！** 运行后浏览器会自动打开可视化界面。

---

## ✨ 核心特性

- 🎬 **单步执行跟踪** - 看到每一步执行过程
- 📊 **自动数据结构可视化** - 数组、链表、树等自动展示
- 💻 **零配置使用** - 一个装饰器搞定
- 🌐 **浏览器可视化** - 交互式 HTML 界面
- 📦 **易于集成** - 直接复制到项目中，无依赖

---

## 📖 核心概念（3 个装饰器）

### `@capture()` - 捕获函数执行

```python
from dsvis import capture

@capture()
def algorithm():
    # 代码执行过程会被完整记录
    pass
```

### `@auto()` - 自动追踪变量

```python
from dsvis import auto

@auto()
def process():
    # 所有变量改变都被追踪
    pass
```

### `watch_vars()` - 观察特定变量

```python
from dsvis import capture, watch_vars

@capture()
def algo():
    data = [1, 2, 3]
    watch_vars(data)
    # data 的每次改变都会显示
```

---

## 💡 实际例子

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
    bubble_sort([3, 1, 4, 1, 5, 9])
```

### 例子 2：自定义数据结构

```python
from dsvis import capture, bind_fields

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
    
    bind_fields(root, val=("值", 1), left=("左", 1), right=("右", 1))
    return root

if __name__ == "__main__":
    tree = build_tree()
```

---

## 📚 如何学习

| 方法 | 时间 | 适合 |
|------|------|------|
| [INTEGRATION.md](INTEGRATION.md) ⭐ | 5 分钟 | 集成使用 |
| [examples/](examples/) | 10 分钟 | 看代码学习 |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | 30 分钟 | 深入 API |
| [docs/UNIFIED_MODE_DOCUMENTATION.md](docs/UNIFIED_MODE_DOCUMENTATION.md) | 1 小时 | 高级特性 |

---

## 📁 项目结构

```
DSVis/
├── dsvis/              # 👈 复制这个到你的项目
│   ├── __init__.py     # 公共 API 导出
│   ├── dsvis.py        # 核心模块
│   ├── runtime/        # 运行时系统
│   └── template.html   # 可视化前端
├── examples/           # 示例代码（参考）
│   ├── demo_btree.py
│   ├── demo_bubble.py
│   └── ...
├── docs/              # 详细文档
├── INTEGRATION.md     # 集成指南 ⭐
├── README.md          # 本文件
└── .gitignore
```

**只需 `dsvis/` 目录就能工作！**

---

## 🎯 为什么选择 DSVis？

| 方面 | 优势 |
|------|------|
| **易于集成** | 直接复制文件夹，无需 pip 安装 |
| **零依赖** | 纯 Python，不依赖任何外部库 |
| **即时可视化** | `@capture()` 一行搞定 |
| **完整文档** | 从快速开始到高级用法 |
| **实用工具** | 学习、调试、教学都能用 |

---

## ✅ 快速检查

- [ ] 阅读 [INTEGRATION.md](INTEGRATION.md)（5 分钟）
- [ ] 复制 `dsvis/` 到你的项目
- [ ] 运行一个 `demo_*.py` 看效果
- [ ] 在自己的代码中使用 `@capture()`

---

## ❓ 常见问题

**Q：为什么不直接 pip install？**  
A：可以直接集成，不需要发布到 PyPI。直接复制 `dsvis/` 文件夹即可。

**Q：可以在 IDE 中使用吗？**  
A：可以！只要是 Python 环境就支持，会自动打开浏览器显示可视化。

**Q：支持哪些 Python 版本？**  
A：Python 3.8 及以上

**Q：是否支持网络环境（无法打开浏览器）？**  
A：会生成 HTML 文件，可以手动打开。详见[文档](docs/UNIFIED_MODE_DOCUMENTATION.md)。

---

## 🚀 集成步骤

```bash
# 1. 将 dsvis/ 目录复制到你的项目
cp -r dsvis/ my_project/

# 2. 在代码中导入
from dsvis import capture

# 3. 使用装饰器
@capture()
def algorithm():
    pass

# 4. 运行
python my_script.py
```

**就这么简单！** 🎉

---

## 📚 完整文档导航

| 文档 | 内容 |
|------|------|
| [INTEGRATION.md](INTEGRATION.md) ⭐ | 如何集成和使用 |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | 完整 API 文档 |
| [docs/INTERFACES_QUICK_REFERENCE.md](docs/INTERFACES_QUICK_REFERENCE.md) | 快速速查表 |
| [docs/UNIFIED_MODE_DOCUMENTATION.md](docs/UNIFIED_MODE_DOCUMENTATION.md) | 深入理解 |
| [examples/](examples/) | 代码示例 |

---

## 🎓 学习建议

**初级用户** (15 分钟)
1. 读 [INTEGRATION.md](INTEGRATION.md)
2. 复制 `dsvis/` 到项目
3. 运行 `examples/demo_bubble.py` 看效果

**中级用户** (1 小时)
1. 查看 [examples/](examples/) 中的所有示例
2. 阅读 [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
3. 在自己的项目中集成

**高级用户** (2 小时)
1. 阅读 [docs/UNIFIED_MODE_DOCUMENTATION.md](docs/UNIFIED_MODE_DOCUMENTATION.md)
2. 修改 `dsvis/template.html` 定制样式
3. 在企业项目中使用

---

## 💬 需要帮助？

- 查看 [INTEGRATION.md](INTEGRATION.md) 了解如何集成
- 查看 [examples/](examples/) 中的代码示例
- 阅读 API 文档：[docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

**准备好了？** 👇

```bash
# 1. 复制 dsvis/ 文件夹
# 2. from dsvis import capture
# 3. @capture() 装饰你的函数
# 4. 享受可视化！
```

---

**版本**: 1.0.0 | **最后更新**: 2026-04-11
