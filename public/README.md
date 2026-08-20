# DSVis — 数据结构可视化库

> 面向教学和调试的数据结构可视化工具。默认使用方式保持简单：用户代码里只需要 `import dsvis` 并调用 `dsvis.auto()`，布局、字段显示、边代理、标题替换以及页面 AI 助手等复杂配置尽量在生成的浏览器页面中完成。

## 快速开始（推荐用法）

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

运行脚本后，DSVis 会执行一次用户程序、记录回放历史，并自动打开浏览器可视化页面。大多数用户不需要在算法代码中写额外的可视化配置；请在页面右侧的设置面板中调整布局和显示方式。

---

## 当前交互方式

生成页面中可以完成这些操作：

- 单步回放、继续、暂停、重启、停止。
- 点击源码行号设置 / 取消断点。
- 切换横向 / 纵向文本方向。
- 对同类节点的字段做统一显示控制。
- 对树类结构配置边代理，例如让 `children` 的边从 `keys` 的位置发出，使 B-Tree / B+Tree 更接近教科书渲染。
- 使用标题替换，把节点标题替换为某个字段值，例如把 B 树节点显示为 `keys = [...]`。
- 启用 PageAgent 页面 AI 助手，让用户通过自然语言辅助修改页面设置。

> 注意：PageAgent 是前端可选能力。只有在页面设置中启用后才会加载。若同时配置 API URL、Token、模型，则使用用户自己的 OpenAI-compatible API；否则使用 PageAgent 默认测试接口。生产环境不要把真实密钥直接放在前端页面里，应通过后端代理托管密钥和权限控制。

---

## Python API 策略

DSVis 的长期方向是 **Python 侧尽量薄，前端配置尽量强**：

| 接口 | 状态 | 说明 |
|------|------|------|
| `auto()` | 推荐 | 脚本顶部调用，自动追踪整段代码。普通用户只需要这个。 |
| `capture()` | 保留 | 低层手动快照接口，主要用于调试 DSVis 自身或特殊场景。 |
| `set_mode(mode)` | 兼容 | 临时切换采集粒度；未来应尽量由页面设置或运行配置承接。 |
| `set_layout(...)` | 兼容 | 当前用于脚本默认布局；长期应迁移到前端设置 / preset。 |
| `set_text_flow(...)` | 兼容 | 当前用于脚本默认文本方向；长期应迁移到前端设置 / preset。 |
| `watch_vars(*names)` | 不再扩展 | 复杂变量关注逻辑不再作为主要能力维护，后续应转到前端字段/节点选择。 |
| `bind_fields(obj, ...)` | 不再扩展 | 字段绑定不再作为主要能力维护，后续应由前端边代理、字段可见性和 AI 设置完成。 |

已经存在的兼容接口不会立刻删除，但新增能力优先落在前端配置层，避免用户为了可视化污染算法代码。

---

## 典型数据结构渲染建议

### B-Tree / B+Tree

推荐在生成页面中应用 B-Tree 或 B+Tree 预设：

1. 打开右侧设置面板。
2. 选择 `B-Tree` 或 `B+ Tree` 预设。
3. 使用纵向布局。
4. 将节点标题替换为 `keys`。
5. 将 `children` 边代理到 `keys`，并启用“含端点”，使边从 key 槽位附近发出。

这样比在 Python 代码里调用 `bind_fields()` 更适合后续维护，也更便于 PageAgent 根据页面状态自动修改设置。

---

## PageAgent 接入说明

DSVis 页面内置了可选 PageAgent 入口：

- 点击工具栏中的“页面 AI 助手”按钮会启用 PageAgent 并打开设置面板。
- 在设置面板中可填写：
  - API URL
  - Token
  - 模型名
- 三项都填写时，前端会以这些配置初始化 PageAgent。
- 任意一项为空时，前端会回退到 PageAgent 默认 demo/testing 脚本。

建议的生产部署方式：

1. 前端只配置你的后端代理地址，例如 `/api/llm-proxy`。
2. Token 保存在服务端环境变量，不暴露给浏览器。
3. 后端代理负责登录校验、权限控制、速率限制、额度控制、日志脱敏和敏感数据过滤。

---

## 下一阶段重构目标

当前 `dsvis/template.html` 过大，已经同时承担模板、状态管理、布局计算、字段配置、边代理、PageAgent 初始化等职责。为了支持“用户或 AI 在前端修改页面设置”的目标，后续重构建议按以下方向推进：

1. **给 AI 暴露稳定的数据接口**
   - 提供只读页面状态接口，例如当前节点类型、字段、preset、布局、隐藏节点、边代理规则。
   - 提供受控写接口，例如应用 preset、切换字段可见性、设置标题字段、设置边代理、切换布局。
   - 将这些接口挂到明确命名空间，例如 `window.DSVisAgentAPI`，避免 PageAgent 直接依赖 DOM 细节。

2. **优化渲染链条**
   - 将“原始图数据 → 过滤/代理/标题替换 → 布局测量 → G6 数据 → 渲染”拆成清晰阶段。
   - 每个阶段输入输出都保持可序列化，便于调试、回放和 AI 分析。
   - B-Tree / B+Tree 等结构优先通过前端 preset 和代理规则表达，而不是要求用户在 Python 侧写特殊绑定。

3. **引入日志系统**
   - Python 侧用标准 `logging`，至少区分 capture、AST hook、scheduler、graph builder、renderer payload 等模块。
   - 前端提供 `DSVIS_LOG_LEVEL` 或页面设置，统一控制 `debug/info/warn/error`。
   - 关键渲染阶段输出结构化日志，方便定位“字段丢失、边代理失效、布局异常、PageAgent 初始化失败”等问题。

4. **拆分前端模板**
   - 将当前单文件模板拆成状态管理、graph transform、G6 renderer、settings UI、PageAgent adapter、debug controls 等模块。
   - 生成 HTML 时可以先保持单文件产物，但源码应模块化，再由构建步骤或 Python 打包逻辑内联。

---

## 项目结构

```text
DS-Tool/
├── dsvis/
│   ├── __init__.py          # 公共 API
│   ├── dsvis.py             # Python 入口 + HTML 生成入口
│   ├── introspection.py     # 类型内省
│   ├── stack_serializer.py  # 调用栈序列化
│   ├── graph_builder.py     # Python 对象图遍历
│   ├── card_renderer.py     # G6 数据构建 + HTML 模板填充
│   ├── field_binding.py     # 兼容层：字段绑定（不再扩展）
│   ├── styles.css           # 前端样式
│   ├── template.html        # 当前前端单文件模板（待拆分）
│   └── runtime/             # AST 插桩、触发器、调度器
├── bTree.py                 # B-Tree 示例
├── bPlusTree.py             # B+Tree 示例
└── README.md
```

---

## 示例脚本

仓库根目录提供多个可直接运行的示例，例如：

```bash
python bTree.py
python bPlusTree.py
python bubbleSort.py
python hashOpen.py
python queue.py
```
