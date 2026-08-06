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

## 相关实现

- `dsvis/card_renderer.py`：`build_g6_data()` 尊重初始可见性并保留 `titleColW = 0`
- `dsvis/template.html`：渲染阶段尊重收到的 `titleColW` 值
- `scripts/test_title_collapse.py`：回归测试（标题可见/隐藏、作用域、横向不受影响）
