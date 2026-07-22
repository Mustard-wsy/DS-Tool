# ADR-001: 内联日志对象 DSVisLogger

**日期**: 2026-07-22  
**状态**: 已采纳  
**决策者**: AI Assistant（经用户确认）

---

## 背景

`dsvis/template.html` 是一个自包含的单文件 HTML 模板。其 PageAgent 模块（agent API、预设切换、字段可见性、边代理等操作）需要记录运行时诊断信息，以便调试生成的回放页面。这些调用已遍布 PageAgent 代码中：

```js
DSVisLogger.info('agent', 'preset-applied', { id });
DSVisLogger.info('agent', 'field-visibility-updated', { key, state });
DSVisLogger.info('agent', 'edge-proxy-updated', { key, rule: ... });
```

但 `DSVisLogger` 对象**从未在模板中定义**。生成的回放 HTML 在浏览器中运行时报错：

```
Uncaught ReferenceError: DSVisLogger is not defined
```

这导致后续 JS 初始化全部中断，表现为：源码区空白、节点样式异常、G6 未能正常渲染。

## 决策

在 `template.html` 中，于 `createAgentAPI()` 函数之前添加一个**自执行函数（IIFE）**定义 `DSVisLogger`，提供分级的控制台日志输出：

```js
const DSVisLogger = (() => {
  let _level = 'info';
  const levels = { debug: 0, info: 1, warn: 2, error: 3, none: 4 };
  function log(level, module, event, data) {
    if (levels[level] >= levels[_level]) {
      const prefix = `[dsvis:${module}]`;
      const extra = data != null ? ' ' + JSON.stringify(data) : '';
      const msg = event + extra;
      switch (level) {
        case 'error': console.error(prefix, msg); break;
        case 'warn': console.warn(prefix, msg); break;
        default: console.log(prefix, msg);
      }
    }
  }
  return {
    get level() { return _level; },
    setLevel(l) { if (levels[l] !== undefined) _level = l; },
    debug: (m, e, d) => log('debug', m, e, d),
    info: (m, e, d) => log('info', m, e, d),
    warn: (m, e, d) => log('warn', m, e, d),
    error: (m, e, d) => log('error', m, e, d),
  };
})();
```

### 设计要点

| 特性 | 选择 | 理由 |
|------|------|------|
| 实现方式 | IIFE 闭包 | 不污染全局作用域，`_level` 和 `levels` 完全私有 |
| 输出目标 | `console.log/warn/error` | 与浏览器开发者工具兼容，无需额外依赖 |
| 分级控制 | `level` 属性 + `setLevel()` | Agent API 可通过 `setLogLevel()` 控制输出粒度 |
| 消息前缀 | `[dsvis:module]` | 在控制台过滤时易于识别来源 |
| 位置 | `createAgentAPI()` 之前 | 保证 PageAgent 初始化时 DSVisLogger 已可用 |

## 后果

- **正面**：`template.html` 保持自包含，无需外部脚本；PageAgent 初始化不再中断
- **正面**：回放页面的控制台日志便于用户和开发者调试
- **负面**：极轻微的模板体积增加（约 0.6 KB），可忽略

## 替代方案（已排除）

1. **外置 JS 文件（如 logger.js）**：违反架构不变式 I5（自包含 HTML），排除
2. **用 `console.log` 直接替换所有调用**：丢失分级和前缀信息，Agent API 的 `setLogLevel()` 接口无法工作
3. **从 Python 端注入 logger 定义**：大幅增加生成逻辑复杂度，收益不匹配
