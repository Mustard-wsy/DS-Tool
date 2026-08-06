# ADR-003: 隐藏标题时保留零宽标题列

**日期**: 2026-08-05  
**状态**: 已采纳  
**决策者**: 用户 + AI Assistant

---

## 背景

DSVis 的纵向节点使用 `titleColW` 表示标题列宽度。当用户隐藏 `__title__` 字段时，标题列应当完全折叠，否则会出现如下错误布局：

`|Title|1|2|3|` 隐藏标题后变成 `|1||2|3|`

这说明标题文本已经隐藏，但标题列本身仍保留了默认宽度，导致字段列整体错位。

## 根因

`card_renderer.py` 在序列化节点样式时，把 `title_col_w` 当作布尔值处理：

```py
if self.title_col_w:
    d["titleColW"] = self.title_col_w
```

当 `title_col_w == 0` 时，该字段不会被写入 HTML 数据。前端 `drawKeyShape()` 随后回退到默认值 `80`，于是标题列不会折叠，只是内容被隐藏。

## 决策

将 `title_col_w` 的序列化条件从“truthy”改为“非 None”：

- `0` 必须被保留并传到前端
- 前端若收到 `titleColW: 0`，就应当把标题列宽折叠为 0
- 标题可见性与标题列宽度分离：
  - `__title__` 控制标题文本是否显示
  - `titleColW` 控制标题列是否占位

## 后果

- 隐藏标题时，纵向节点字段列会从 `|Title|1|2|3|` 正确折叠为 `|1|2|3|`
- 字段可见性逻辑不会再依赖标题列的默认回退宽度
- 需要保持前端对 `titleColW: 0` 的兼容，避免把它当作缺失值处理

## 实现进展（2026-08-06）

序列化条件修复（保留 `titleColW: 0`）只是第一步 —— 后端之前仍然
根据节点名称计算非零 `titleColW`，隐藏 `__title__` 时数据里依旧是
`titleColW: 66`，与初始可见性不一致。现已补齐后端逻辑：

- `build_g6_data()` 新增 `field_visibility` 参数（来自
  `runtime.config.get_field_visibility()`）
- 当 `ClassName.__title__` 的初始可见性为 `self` / `cascade` 时，
  纵向节点的 `title_col_w` 强制置为 `0`，并按去掉标题列后的宽度
  重新计算卡片宽度，使生成的数据自洽
- `render_debugger()` 把可见性传入 `build_g6_data()`

前端 `template.html` 的 `adaptNodesForTextFlow()` 仍保留防御性重算
（用 `attributes.titleColW != null ? attributes.titleColW : 80` 判断，
确保合法的 `0` 不被回退），与后端修复互为冗余、不冲突。

## 补充调查（2026-08-06，问题"仍未解决"的排查）

用户反馈隐藏标题后仍看到 `Title|40|2 → 40||2`。逐层排查（数据管线、
`adaptNodesForTextFlow`、G6 实际渲染的 shape 几何）后确认：

1. **标题列折叠本身是正常的** —— `titleColW` 确实从 66 折叠为 0，
   标题文本被清空、入口端口移到首列中心、卡片宽度相应收缩。
2. **`40||2` 的真实来源是"仅值"行显示模式下 ref 字段的空列**：
   ref 字段（如 `left`/`right`）是指针，在"仅值"模式下没有值可显示，
   于是渲染成空列，被误认为"未折叠的标题列"。用户日志中
   `cardH: 36`（单行）佐证了用户处于"仅值/仅字段名"单行模式。

### 决策（试过后已回滚）：仅值模式丢弃 ref 列 → 不可行

曾尝试在 `adaptNodesForTextFlow()` 中，当 `rowDisplayMode === 'value'`
时过滤掉无值的 ref 列（使 `30|||4 → 30|4`），**但随后被回滚**：
- 丢弃 ref 列会连带删除 ref 端口（蓝色圆点），导致 `left` / `right`
  两条边从同一个锚点发出
- 并触发 `updateNodeData`/`updateEdgeData` 的 "Node/Edge not found"
  错误（端口布局与网格不一致）

结论：**ref 列在任意行显示模式下都应保留**（它们承载端口与边锚点）。
仅值模式下 ref 列显示为空是预期行为（ref 无值可显示）。

### 顺带加固：过渡期元素已移除的良性错误

`updateEdgePorts()` 在步进切换（节点/边增删）时，`afterlayout` /
`afterrender` 回调可能对已移除的节点/边执行端口更新，G6 抛出
"Node/Edge not found for id"。这些是过渡期的良性错误，已用
`try/catch` 包裹 `updateNodeData` / `updateEdgeData` 静默处理。

## 相关实现

- `dsvis/card_renderer.py`：`build_g6_data()` 尊重初始可见性并保留 `titleColW = 0`
- `dsvis/template.html`：
  - 渲染阶段尊重收到的 `titleColW` 值（`!= null` 判断）
  - `updateEdgePorts()` 对"过渡期元素已移除"错误做防御处理
- `scripts/test_title_collapse.py`：后端回归测试（标题可见/隐藏、作用域、横向不受影响）
