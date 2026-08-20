# ADR-006: 非空容器不显示聚合行 + 面板容器组快捷键

**日期**: 2026-08-14
**状态**: 已采纳
**决策者**: 用户 + AI Assistant（经 grilling 逐项确认）

---

## 背景

对于 `keys = [4, 9, 15]` 这类容器字段，后端目前会**同时**生成聚合行
（`keys = [4, 9, 15]`）和展开行（`keys[0] = 4`…）。用户希望：

1. 图中不再显示非空容器的聚合行，只展开显示各项；
2. 样式面板仍保留 `keys` 这一栏，作为"总开关"：隐藏它即隐藏所有
   `keys[i]` 项；面板状态同步。

## 决策（grilling 共识）

| # | 决策 | 结论 |
|---|------|------|
| Q1 | 实现层 | **后端 `graph_builder.py`** |
| Q2 | 容器范围 | **统一处理** list/tuple/set/frozenset/dict/deque；空容器保留聚合行 |
| Q3 | 组按钮语义 | ~~2 态切换~~ → **3 态循环**（visible → self → cascade → visible），
       与普通字段一致（2026-08-14 用户要求回退） |
| Q4 | 状态同步 | ~~显式传播~~ → **不显式传播**：靠 `isFieldVisible` 的 base 级联 +
       面板成员用 `isFieldVisible()` 计算有效可见性（2026-08-14 回退） |
| Q5 | 成员可单独点 | **保留** |
| Q6 | 组机制范围 | **所有 `[...]` 后缀字段统一生成组** |
| Q7 | 面板呈现 | **组按钮区分样式 + 成员归组排列（组在前）** |

### 3 态语义（2026-08-14 修订）

- **visible**：显示所有成员 `a[i]`（若有聚合行如空数组 `a = []` 也显示）；
  不强制恢复被单独隐藏的成员。
- **self（仅自身隐藏）**：只隐藏聚合行（空数组 `a = []`）；成员保持显示。
  对非空数组图里本无聚合行，该态无可见变化但仍保留在循环中。
- **cascade（隐藏+子项）**：隐藏聚合行 + 所有成员（经 `isFieldVisible` base 级联）。

## 实现

### 后端（graph_builder.py）

`_resolve_object_fields`：容器字段非空时只生成 `X[i]` 展开行；空时保留聚合行
`X = []`。原 `all_refs`（纯引用数组跳过聚合行）逻辑并入统一规则。

### 前端（template.html）

- `buildNodeTypeRegistry`：由 `X[i]` 成员反推合成 `X` 组（`isGroup: true`）；
  若 `X` 已有真实条目（来自空数组聚合行），**升级**为组而非跳过。
  重排使每个组紧贴其成员之前，其余字段保持相对顺序。
- 新增 `baseKeyOfFieldKey()`、`getGroupMemberKeys()`、`setContainerGroupHidden()`、
  `toggleContainerGroup()`、`isGroupFieldKey()`。
- 面板：组按钮带 `node-type-group-btn` 样式（加粗/描边）；成员用
  `isFieldVisible()` 计算有效可见性，组隐藏时成员按钮同步显示隐藏。
  组按钮点击走标准 3 态 `toggleNodeFieldVisible`；右键菜单对组字段与普通字段
  相同（`setNodeFieldVisible` self/cascade）。2 态辅助函数
  （`toggleContainerGroup`/`setContainerGroupHidden`/`getGroupMemberKeys`/
  `isGroupFieldKey`）已移除。
- styles.css：新增 `.node-type-group-btn` 样式。

## 后果

- 图节点不再出现 `keys = [4, 9, 15]` 这类冗余聚合行，仅展开各项；
  空数组保留 `keys = []`。
- 面板 `keys`/`children` 作为组：标准 3 态循环；`cascade` 经 base 级联隐藏
  全部成员；`self` 只隐藏空数组聚合行；成员仍可单独切换，且不强制恢复。
- 组隐藏 `children` 会级联隐藏子边与子节点（现有 cascade 语义）。
- 潜在影响：所有算法中非空容器字段都不再显示聚合摘要行（统一行为）；
  若某处依赖聚合行文本，需改用展开行。

## 验证

- btree：根节点行 `t, leaf, children[0..3], keys[0..2]`（无 `keys` 聚合）；
  叶子保留 `children = []`。
- 面板：`keys`（isGroup）在 `keys[0..4]` 前，`children`（isGroup）在
  `children[0..3]` 前。
- 3 态循环实测：`keys` 第 1 击 → `self`（成员仍 visible，组按钮 self-hidden）；
  第 2 击 → `cascade`（成员按钮经有效可见性显示 cascade-hidden，图中
  `keys[i]` 行被过滤）；第 3 击 → `visible` 全部恢复。
- 回归：`test_title_collapse.py`、`test_graph_viewer.py` 通过；
  `node --check` 通过。
