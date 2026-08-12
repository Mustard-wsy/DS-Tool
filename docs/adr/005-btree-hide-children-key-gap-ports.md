# ADR-005: B-Tree 显示模式 —— 隐藏 children + 指针从 keys 间隔发出

**日期**: 2026-08-12
**状态**: 已采纳
**决策者**: 用户 + AI Assistant

---

## 背景

B-Tree 节点在默认纵向网格里会展开全部字段（`t`、`leaf`、`children[0..n]`、
`keys`、`keys[0..n]`），导致：

1. `children` 列把节点撑得很宽，且子节点指针的"发出点"位于每个 children 列的
   中心，视觉上不符合 B-Tree 的习惯表达；
2. 用户期望 B-Tree 模式下隐藏 `children`，同时让子指针从 **keys 的间隔线**
   （首 key 左侧、key 与 key 之间、末 key 右侧）发出，更直观形象。

## 现状与约束

现有可见性模型表达不了"隐藏 `children[i]` 行但保留子边"：

- `self`：只隐藏精确的 `children` 键，**不**级联到带索引的 `children[i]`
  （`isFieldVisible` 对 `...[...]` 形式只对 `cascade`/`false` 做 base 级联）；
- `cascade` / `false`：隐藏 `children[i]` 的同时**删除子边**（孤儿边模式）。

因此需要一套 **B-Tree 专属的前端变换**，而不是复用可见性级联。

## 决策

在 `template.html` 新增 `adaptBTreeNodes(graphData)`，仅在
`structureType === 'btree' | 'bplustree'` 且节点样式为纵向网格时生效：

1. **识别**：通过 `STRUCTURE_TYPES[type].proxyRules` 取 `keyField='keys'`、
   `childField='children'`；节点同时具备 `keys[i]` 行和 `children[i]` 行才算
   B-Tree 节点（容器节点 `BTree` 因无此组合而自动跳过）。
2. **只显示 keys**：重建节点为单行值网格 —— `gridValues = keys[i]` 的值、
   `gridNames` 置空、`gridRefs=[]`、`rowDisplayMode='value'`、`titleColW=0`，
   卡片宽度按 key 个数紧凑计算（`w = padX*2 + numKeys*colW`）。
3. **隐藏 children**：children 行不再进入网格（`gridRefs=[]` 且不渲染），
   **但子边全部保留**。
4. **指针从 keys 间隔发出**：为 `i = 0..numKeys` 建立间隔端口
   `pt{i}/pb{i}`，横坐标 = `(padX + i*colW)/w`（首 key 左侧、key 之间、末 key
   右侧）；`portLayout.ref = [{idx:i, ports:['pb'+i,'pt'+i]}]`。
5. **重映射子边**：把 `label` 形如 `children[i]` 的边 `data.refIndex` 改为
   `i`，使其落在对应的间隔端口上。

调用时机：`renderStepImpl` 中 `adaptNodesForTextFlow()` 之后、
`filterHiddenNodes()` 之前。由于 `applyUniformEdgePorts` 只处理被隐藏成
"孤儿"的边，本变换（保留边、不隐藏为孤儿）不会与均匀边逻辑冲突。

## 后果

- B-Tree 节点呈现为紧凑的 keys 行，children 列消失但 4 条子边仍在；
- 子指针精确落在 keys 的间隔线上（首 key 左侧、key 之间、末 key 右侧）；
- 节点宽度随之大幅收敛，顺带缓解了此前 keys 展开导致的超宽问题；
- 非 btree/bplustree 结构类型完全不受影响（变换提前返回）；
- 若节点只有 keys 没有 children（如构造中间态），变换自动跳过，回退默认网格。

## 后续可选

- 是否保留 `t`/`leaf` 等元数据列（当前 B-Tree 模式默认只显示 keys）；
- B+ Tree 叶子节点的 `next` 链如何表达（当前仅当 `keys`+`children` 同时存在
  时变换才生效）。
