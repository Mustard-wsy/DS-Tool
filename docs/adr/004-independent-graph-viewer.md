# ADR-004: 独立的"图查看器"模式

**日期**: 2026-08-06
**状态**: 已采纳
**决策者**: 用户 + AI Assistant

---

## 背景

图算法（Prim / Kruskal / DFS / BFS / SCC…）在卡片模式下会被矩形卡片 + 字段行
渲染，包含大量杂质（Edge 对象本身也变成节点、`edges[0]` 这类字段名），既不好看
也不符合通用图查看器的直觉。用户希望为"图模式"做一个**独立**的图显示器：
只显示节点值（无值用遍历序）与边值/方向，圆形节点，不显示数据类型等。

## 决策

**触发**：`structureType === 'graph'`（前端"数据结构类型 = 图"）→ 进入完全独立的
图查看器渲染，绕开卡片 / 字段可见性 / dagre 管线。

**后端**（新增独立模块 `dsvis/graph_viewer.py`，不碰卡片代码）
- 输入：每步已有的 BFS `nodes/edges`（复用 `graph_builder` 输出，不重新遍历）。
- 输出 `graphView`：
  `{ nodes:[{id,value,index,fields}], edges:[{source,target,value,edgeId,fields}], undirected }`
- 分类三态：
  - **边对象** = 在顶点引用集合中、有单个 `to`-类引用的类对象（如 `Edge(to, weight)`）；
  - **顶点** = 出现在顶点引用集合或根图顶点集合中的类对象；
  - **其它**（根容器、辅助对象）→ 忽略不渲染。
- 顶点值：`value → val → data → key → id → name → label` → 第一个标量字段 → 遍历序索引。
- 边值：边对象标量字段 `weight → w → cost → dist → value`；直接顶点引用无边值。
- 方向：**全对称且每对权重相同 → 无向**（合并对称对为一条、无箭头）；否则有向（全保留、有箭头）。
- `render_debugger` 每步**同时输出 `graph` + `graphView`**。

**前端**（`structureType='graph'` 走独立分支）
- 独立 **circle** 节点（`graph-node`）：半径可调（默认 24）、值居中、超长截断。
- **force** 力导向布局，节点可拖动，画布缩放/平移。
- 边：无向无线箭头、有向有箭头；边值标签在线的中上方（浅灰小字）。
- 步进高亮：新增节点/边（相对上一步 diff）橙色高亮。
- 点击节点弹浮层显示顶点字段详情（复用 `nodeContextMenu`）。
- 栈/代码面板照常。
- 样式面板图专属选项：**顶点值字段、边值字段、方向（自动/强制有向/强制无向）、节点半径**。

## 后果

- 图算法可视化达到通用图查看器水准，无 Edge 对象杂质、无卡片字段噪音。
- 与卡片系统完全解耦，后续不会互相影响（吸取了标题列兼容问题的教训）。
- HTML 体积略增（每步多一份紧凑的 `graphView`）。

## 相关实现

- `dsvis/graph_viewer.py`：独立图视图数据生成器
- `dsvis/card_renderer.py`：`render_debugger` 每步输出 `graphView`
- `dsvis/template.html`：`renderStepImpl` 图模式分支、`graph-node` 圆节点、
  force 布局、边方向/权重标签、步进高亮、点击浮层、图查看器设置面板
- `scripts/test_graph_viewer.py`：后端回归测试（有向无权 / 无向带权 / 无向无权）
