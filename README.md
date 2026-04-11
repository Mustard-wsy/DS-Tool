# DSVis - 数据结构可视化工具

一个强大的数据结构动态可视化和调试工具，支持多种数据结构的实时可视化和单步执行跟踪。

## 项目结构

```
dsvis/
├── src/                              # 核心源代码
│   ├── dsvis.py                      # 主模块入口
│   ├── template.html                 # 可视化前端模板
│   ├── runtime/                      # 运行时系统
│   │   ├── config.py                 # 配置管理
│   │   ├── scheduler.py              # 调度器（核心）
│   │   ├── trigger.py                # 触发器
│   │   ├── ast_hook.py               # AST 钩子系统
│   │   ├── auto.py                   # 自动追踪
│   │   └── injector.py               # 代码注入
│   └── algorithms/                   # 数据结构实现
│       ├── Btree.py                  # B树
│       ├── Bubble.py                 # 冒泡排序
│       ├── hash.py                   # 哈希表
│       ├── queue.py                  # 队列
│       ├── stack.py                  # 栈
│       └── LongList.py               # 长链表
├── examples/                         # 使用示例和演示
│   ├── run_ast.py                    # AST 演示示例
│   └── user_code.py                  # 用户代码示例
├── docs/                             # API 文档
│   ├── API_REFERENCE.md              # API 参考
│   ├── INTERFACES_QUICK_REFERENCE.md # 快速参考
│   └── UNIFIED_MODE_DOCUMENTATION.md # 统一模式文档
├── tests/                            # 测试套件
│   ├── test1.py                      # 基础测试
│   └── test_comprehensive.py         # 综合测试
└── .gitignore                        # Git 配置（仅上传核心内容）
```

## 核心功能

### 1. **捕获模式** (Capture Mode)
使用装饰器 `@capture` 标记函数，自动记录执行步骤：
```python
from src.dsvis import capture

@capture()
def my_algorithm():
    # 您的代码
    pass
```

### 2. **自动模式** (Auto Mode)
使用 `@auto` 装饰器自动追踪变量变化：
```python
from src.dsvis import auto

@auto()
def process_data():
    pass
```

### 3. **观察模式** (Watch Mode)
手动观察特定变量和数据结构的变化。

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt  # 如果有的话
```

### 基本使用
```python
from src.dsvis import capture, auto

@capture()
def example():
    arr = [3, 1, 2]
    arr.sort()
    return arr

# 运行并查看可视化
if __name__ == '__main__':
    result = example()
```

### 支持的数据结构
- 列表 (List)
- 字典 (Dict) 
- 集合 (Set)
- 自定义数据结构 (Btree, Queue, Stack 等)

## 文档

- [API 参考](docs/API_REFERENCE.md) - 完整 API 文档
- [快速参考](docs/INTERFACES_QUICK_REFERENCE.md) - 常用接口速查
- [统一模式文档](docs/UNIFIED_MODE_DOCUMENTATION.md) - 详细模式说明

## 测试

运行测试套件：
```bash
python tests/test1.py
python tests/test_comprehensive.py
```

## 示例

查看 `examples/` 目录获取详细使用示例：
- `run_ast.py` - AST 工作原理演示
- `user_code.py` - 用户代码执行示例

## 配置文件说明 (.gitignore)

该项目的 `.gitignore` 配置仅上传核心代码文件，排除：
- Python 缓存文件 (`__pycache__/`, `*.pyc`)
- 虚拟环境 (`.venv/`, `venv/`)
- IDE 配置文件 (`.vscode/`, `.idea/`)
- 生成的报告和详细文档
- 临时文件和调试输出

## 许可证

[您的许可证信息]

## 贡献

欢迎提交问题和改进建议！

---

**最后更新**: 2026-04-11  
**项目版本**: 1.0.0
