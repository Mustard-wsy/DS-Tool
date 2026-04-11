# DSVis 模式统一文档

## 目标
将 capture 模式和 auto 模式统一，使 capture 像手动 trigger 一样工作，共享同一个调试界面。

## 改造内容

### 1. Capture 模式的变化

**原始行为：**
- `dsvis.capture()` 立即生成单个 G6 图表
- 使用 `template.html` 渲染
- 每次 capture 都会打开一个新的 HTML 文件

**新行为：**
- `dsvis.capture()` 将步骤添加到 scheduler
- 所有 capture 被收集到 steps 列表中
- 程序结束时统一通过 `scheduler.flush()` 渲染
- 使用 `template.html` 渲染，支持多步骤导航

### 2. 核心实现变更

#### dsvis.py - capture() 函数
```python
# 原始：直接调用 _render_g6()
# 新：调用 scheduler.request_update()
scheduler.request_update(
    caller_frame=caller,
    lineno=caller.f_lineno,
    observed_vars=merged_focus,
    pointer_watchers=merged_pointers,
    tag=title,
    max_nodes=max_nodes,
    include_private=include_private,
)
```

#### scheduler.py - request_update() 方法
```python
# 添加参数：max_nodes, include_private
def request_update(self, caller_frame=None, lineno=None, observed_vars=None, 
                   pointer_watchers=None, tag=None, max_nodes=None, include_private=None):
```

### 3. 统一的工作流

```
Auto 模式：
代码 → AST 注入 trigger() → scheduler.request_update() → scheduler.flush() → template.html

Capture 模式（改造后）：
代码 → 手动 capture() → scheduler.request_update() → scheduler.flush() → template.html

两者现在完全统一！
```

### 4. 用户感受的变化

#### 之前（capture 模式）
```python
# 立即生成单个快照 HTML
dsvis.capture()
dsvis.capture()  # 生成第二个 HTML，覆盖前面的
```

#### 之后（capture 模式）
```python
# 所有 capture 被收集到一个 HTML 中，可以导航
dsvis.capture(title="Step 1")
dsvis.capture(title="Step 2")
# 程序结束時会生成一个 template.html，可以 Prev/Next 在各步骤间切换
```

### 5. 与 Auto 模式的协作

- 如果只用 capture，行为如上
- 如果混合 capture 和 auto，所有步骤（自动 + 手动）都会被收集到同一个 HTML 中
- Prev/Next 会在所有 capture 点和自动触发点之间导航

### 6. 新增功能

#### Capture 参数现在完全生效
- `max_nodes`: 限制显示的最大节点数（作用到 scheduler）
- `include_private`: 是否显示私有属性
- `layout`: 图表布局配置
- `focus_vars`: 关注的变量
- `pointer_watchers`: 指针监听器

## 测试验证

已创建以下测试验证统一模式：

1. **test_unified_capture.py** - 基础功能测试
   - 多个 capture 被正确收集
   - scheduler 自动 flush

2. **test_unified_complete.py** - 完整功能测试
   - 数据变化检测（重复 capture 被跳过）
   - 步骤统计验证

3. **test_capture_stack.py** - 实际数据结构测试
   - Stack 的多步骤操作
   - capture 在不同阶段正确工作

## 文件改动总结

| 文件 | 改动 |
|-----|-----|
| `dsvis.py` | 修改 `capture()` 函数，改用 scheduler |
| `dsvis.py` | 添加 `from runtime.scheduler import scheduler` 导入 |
| `scheduler.py` | 添加 `max_nodes`, `include_private` 属性 |
| `scheduler.py` | 修改 `request_update()` 方法签名 |

## 向后兼容性

✓ 完全向后兼容
- 用户代码无需改动
- `capture()` 的所有参数仍然有效
- 现有的 `template.html` 已经是所有功能的统一模板

## 优势

1. **统一的调试界面** - capture 和 auto 使用同一个 template.html
2. **多步骤导航** - 可以在各个 capture 点间切换
3. **代码同步显示** - 源代码和当前行自动高亮
4. **灵活的标记** - capture 可以标记每个步骤
5. **内存高效** - 只在程序结束时生成 HTML，不会重复创建文件
