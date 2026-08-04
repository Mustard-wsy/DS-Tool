# ADR-002: Agent-native 语义能力架构

**日期**: 2026-07-22  
**状态**: 已采纳  
**决策者**: 用户 + AI Assistant（经逐项确认）

---

## 背景

DSVis 当前通过 CDN 加载 [PageAgent](https://github.com/alibaba/page-agent)（一个基于 DOM 的 GUI Agent 库），提供自然语言交互能力。但现有集成存在三个问题：

1. **双 AI 面板冲突**：PageAgent CDN 自带浮动 UI，DSVis 也有自己的 `#pageAgentPanel`，两者同时存在且功能不协调
2. **LLM 只能读 DOM**：PageAgent 默认将页面 DOM 文本化发送给 LLM，LLM 看到的是 `<button>Next</button>` 而非 "gotoStep(18)"
3. **语义能力未暴露**：DSVis 内部拥有丰富的结构语义（当前步、算法名、树结构、变量、事件历史），但这些信息对 AI 完全不可见

目标：**把 DSVis 设计为 Agent-first 可视化平台** — PageAgent 只是第一个客户端，未来任何 Agent 都可以通过同一套语义接口与 DSVis 交互。

## 决策

### 1. PageAgent 集成方式

- **保留 PageAgent 库**，但通过 CDN 参数 `?autoInit=false` 禁止其自动创建自带 UI
- DSVis 手动构造 `new PageAgent({...})`，将 DSVis 自己的 `#pageAgentPanel` 作为唯一 AI 交互入口
- 通过 `instructions.system` 注入 DSVis 专用指令，**叠加**（而非覆盖）PageAgent 默认系统提示词，保留其 DOM 理解能力作为后备

### 2. API 组织结构：六类嵌套命名空间

```
dsvis.agent.
├─ navigation   (7)  时间线控制
├─ runtime      (6)  运行时语义
├─ query        (3)  历史搜索
├─ explain      (2)  教学解释
├─ focus        (5)  视觉焦点
└─ presentation (10) 展示配置
```

选择理由：
- 语义清晰，Manifest 天然映射到分类
- 后续扩展不影响其他模块
- 现有 `DSVisAgentAPI`（扁平结构）可无痛迁移到 `presentation.*` 下

### 3. 能力注册：`dsvis.define()`

每个能力在实现处自描述注册，Manifest 自动生成：

```js
dsvis.define('navigation.gotoStep', {
  description: '跳转到指定步',
  params: { step: { type: 'number', description: '目标步号（从0开始）' } },
  handler: (args) => { /* 实现 */ },
});
```

选择理由：
- 实现和声明放在一起，永不脱节
- Manifest 从注册表自动派生，无需手工维护两份数据
- `dsvis.registry` 可被 Agent、调试面板、文档生成等多种消费者读取

### 4. PageAgent 工具桥接：自动转换

`dsvis.registry` → 自动生成 PageAgent `customTools`：

```
define() 注册                       PageAgent 要求
┌─────────────────┐               ┌──────────────────┐
│ params: {        │   自动桥接     │ inputSchema:      │
│   step: {        │  ─────────→   │   z.object({      │
│     type: 'num', │               │     step: z.number │
│     desc: '...'  │               │   })              │
│   }              │               │ execute: handler   │
│ }                │               └──────────────────┘
└─────────────────┘
```

选择理由：
- 单一事实来源（`dsvis.define()`），不维护两份能力描述
- 桥接层 < 30 行代码，无需引入 Zod 运行时依赖
- 未来如果换 Agent 框架，只需替换桥接层

### 5. 系统提示词注入

- 使用 `instructions.system`（非 `customSystemPrompt`）
- 写入 `<system_instructions>` 标签，保留 PageAgent 默认行为
- 注入内容包含：角色定义、当前算法上下文、能力清单、优先使用工具的指令

### 6. AI 面板 UI

- 保持右下角固定浮窗形态
- 工具调用对用户透明（Agent 执行时不刷屏展示调用链）
- 聊天区以自然语言呈现结果

## 完整能力清单

### navigation（7 个）

| 方法 | 参数 | 说明 |
|------|------|------|
| `gotoStep(step)` | `step: number` | 跳到第 N 个 Display Step |
| `next()` | — | 下一步 |
| `prev()` | — | 上一步 |
| `play()` | — | 自动回放 |
| `pause()` | — | 暂停回放 |
| `restart()` | — | 回到第 0 步 |
| `gotoRawStep(rawIndex)` | `rawIndex: number` | 跳到第 N 个 Raw Step |

### runtime（6 个）

| 方法 | 参数 | 说明 |
|------|------|------|
| `getState()` | — | 当前步完整语义状态（step/event/algorithm/variables/stack/line） |
| `getTree()` | — | 当前图结构（nodes/edges/root） |
| `getHistory()` | — | 操作历史列表 |
| `getVariables()` | — | 当前步变量快照 |
| `getSourceCode()` | — | 源码全文及行号映射 |
| `getAlgorithm()` | — | 算法名称 |

### query（3 个）

| 方法 | 参数 | 说明 |
|------|------|------|
| `findEvent({ type })` | `type: string` | 找到第一个匹配事件类型的步 |
| `findVariableChange({ varName })` | `varName: string` | 找到变量变化步 |
| `findSourceLine({ line })` | `line: number` | 找到第一个执行到指定行的步 |

### explain（2 个）

| 方法 | 参数 | 说明 |
|------|------|------|
| `currentContext()` | — | 当前语义上下文（algorithm/step/event/balanceFactor/affectedNodes/reason/codeLine） |
| `algorithmSummary()` | — | 算法简介 |

### focus（5 个）

| 方法 | 参数 | 说明 |
|------|------|------|
| `highlightNode(id)` | `id: string\|number` | 高亮节点 |
| `highlightEdge(id)` | `id: string` | 高亮边 |
| `highlightSubtree(id)` | `id: string\|number` | 高亮节点及其后代 |
| `clearHighlight()` | — | 清除所有高亮 |
| `zoomToFit()` | — | 画布自适应 |

### presentation（10 个）

| 方法 | 参数 | 说明 |
|------|------|------|
| `setTextFlow(flow)` | `flow: 'horizontal'\|'vertical'` | 文本方向 |
| `showPanel(name)` | `name: 'stack'\|'code'` | 显示面板 |
| `hidePanel(name)` | `name: 'stack'\|'code'` | 隐藏面板 |
| `applyPreset(id)` | `id: string` | 应用预设 |
| `setFieldVisibility(fieldKey, state)` | `fieldKey: string`, `state: string` | 字段可见性 |
| `setTitleField(className, fieldKey)` | `className: string`, `fieldKey: string\|null` | 标题替换 |
| `setEdgeProxy(targetKey, rule)` | `targetKey: string`, `rule: object\|null` | 边代理 |
| `restoreHiddenNode(nodeId)` | `nodeId: string` | 恢复隐藏节点 |
| `getConfig()` | — | 当前展示配置 |
| `resetLayout()` | — | 重置布局 |

## 架构不变式

- **I7（能力注册单源）**: 所有 Agent 能力必须通过 `dsvis.define()` 注册；Manifest 和 `customTools` 均为其派生
- **I8（语义优先于 DOM）**: Agent 优先使用语义工具函数；DOM 操作仅作为后备
- **I9（自包含 HTML）**: 不改动 I5（自包含 HTML）；所有 Agent 逻辑在生成页面时内嵌，不依赖外部运行时

## 后果

- **正面**：Agent 不再盲读 DOM，可以语义化地跳步、查询、解释、高亮
- **正面**：Capability Manifest 自动生成，换 Agent 框架只需换桥接层
- **正面**：六类 API 对用户代码（Python 侧）透明，不影响 `dsvis.auto()` 的使用体验
- **负面**：`template.html` 脚本体积增加（估计 +8~12 KB），其中桥接层和注册表占主要部分
- **风险**：PageAgent 版本升级可能改变 `instructions.system` 的注入方式，需要关注 CHANGELOG
