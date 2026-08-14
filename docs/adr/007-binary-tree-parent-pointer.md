# ADR-007: 二叉树父指针（parent pointer）显示

**日期**: 2026-08-14
**状态**: 已采纳
**决策者**: 用户 + AI Assistant（经 grilling 逐项确认）

---

## 背景

二叉树（如 `rbTree.py` 的 `RBNode.parent`）存在父指针回边（child→parent）。
需要：
1. 像 left/right 一样把 `parent` 当普通 ref 字段处理（默认可见、可从格子端口出边）；
2. 隐藏 `parent` 格时，回边走"标题式"处理（锚在节点边中点）；
3. 与 left/right 边共享锚点，形成双向箭头。

## 决策（grilling 共识）

| # | 决策 | 结论 |
|---|------|------|
| Q1 | 中点语义 | 子节点顶边中点 `[0.5,0]` → 父节点底边中点 `[0.5,1]` |
| Q2 | 默认可见 | parent 回边默认显示（从 parent 格端口连父节点） |
| Q3 | 字段可配 | 结构参数加「父指针」下拉（默认 `parent`） |
| Q4 | 双向箭头 | 仅当 left/right 格与 parent 格都隐藏时，两边上共享中点线成双向箭头 |

## 场景矩阵（父 P、子 C）

| 场景 | P 的 left/right 格 | C 的 parent 格 | parent 边行为 | 树边行为 |
|---|---|---|---|---|
| 1 | 可见 | 可见 | `pt{parent格} → inB`（普通，同 left/right） | 正常 `pb{格} → inT` |
| 2 | 可见 | 隐藏(self) | `cT`(子顶中) → `cB`(父底中) | 正常 |
| 3 | 隐藏(self) | 可见 | 普通 `pt{parent格} → inB` | 孤儿均匀 `_u0 → inT` |
| 4 | 隐藏(self) | 隐藏(self) | `inT`(子顶入) → `cB`(父底中) | `cB → inT`（与 parent 边共享=双向箭头） |

cascade 隐藏 parent → 整条边隐藏（含级联子节点），不出现上述特殊路由。

## 实现（template.html）

- `STRUCTURE_TYPES['binary-tree'].parentField = 'parent'`；`DEFAULT_VIS_CONFIG`
  新增 `parentFieldKey: ''`（用户选择器覆盖类型默认）。
- `getEffectiveParentField()`：`parentFieldKey || 类型默认 parentField`。
- `buildStructureParams` 二叉树区新增「父指针」下拉（复用 `buildFieldSelect`）。
- `adaptNodesForTextFlow`：每个纵向节点追加中点端口 `cT`[0.5,0] / `cB`[0.5,1]。
- `applyNodeTypeVisibility`：
  - parent 字段 self 隐藏且非 cascade → 边标记 `_parentCenter`（不落 uniform 孤儿）；
  - 后处理：找反向树边（父→子的 left/right）——
    - 反向边是孤儿（场景 4）→ parent 边 `{inT→cB}`、反向边转 `{cB→inT}`（移除 `_orphan`，成双向箭头）；
    - 否则（场景 2）→ parent 边 `{cT→cB}`。
- `resolvePortsForEdge`：优先处理 `e.data._parentCenter`，按 `_parentCenterPorts`
  返回端口（端口不存在则返回 null 走默认）。

## 后果

- 二叉树默认显示 parent 回边（从 parent 格端口），与 left/right 对称；
- 隐藏 parent 格 → 回边锚到节点中点；同时隐藏 left/right 格 → 双向箭头；
- 机制通用：nary-tree 已有 `parentField='parent'`，自动同样受益；
- 布局已用 LAYER_EDGES 过滤回边，不扭曲树形。

## 验证

- 四场景端口实测：场景1 `pt4→inB`；场景2 `cT→cB`；场景3 left `_u0→inT`、
  parent 普通（refIndex=4）；场景4 parent `inT→cB` + left/right `cB→inT`。
- 回归 `test_title_collapse.py` / `test_graph_viewer.py` 通过；`node --check` 通过。
