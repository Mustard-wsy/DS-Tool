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

## 修订（2026-08-15）：力布局 `force` → `d3-force`

**问题**：图模式下节点全部挤在一起完全重合并持续颤动。

**根因**：`initGraphViewer` 使用 `layout: { type: 'force' }`。在 G6 v5 中
`'force'` 解析到自定义力布局（id="force"），实测它
- 不分离节点（最小节点间距 ≈ 1px，节点重叠）；
- 模拟永不收敛（持续颤动）；
- 步骤切换时 `setData + render` 复用已塌缩的位置 → 节点缩成窄条。

**决策**：改用 d3 版力布局 `type: 'd3-force'`。

**补充（2026-08-15）：d3-force 必须用嵌套选项**
`d3-force` 只识别**嵌套**对象 `link`/`manyBody`/`collide`/`center`；顶层的
`linkDistance`/`nodeStrength`/`preventOverlap`/`nodeSize` 会被**静默忽略**
（`setSimulation` 只按 `t.link`/`t.manyBody`/`t.collide` 是否存在来建力）。
此前把 `linkDistance/nodeStrength` 放顶层 → 这些力根本没生效（仅默认弱力，
节点最小间距被压到 ~22px，拥挤）。正确配置：

```js
layout: {
  type: 'd3-force',
  link:    { distance: 170, strength: 0.4 },
  manyBody:{ strength: -350 },
  collide: { radius: (节点半径)+12, strength: 0.8 },  // 最小间距 ≈ 2×radius
  center:  { x: w/2, y: h/2 },
}
```

**验证**（scc 有向 / prim 无向）：
- 节点正确分离（最小间距 ≈ 72px = 2×collide radius），x/y 双轴散开、居中；
- 约 1.2s 后收敛、位置冻结（无颤动）；步骤切换后仍保持散开；
- **缩放无关性**：布局距离在 world 坐标，不受相机 zoom 影响；`fitView` 仅在
  图包围盒超过画布时才缩小（小图 zoom≈1，屏显=world 距离）。
- 回归 `test_title_collapse.py` / `test_graph_viewer.py` 通过。
