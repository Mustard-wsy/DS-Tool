# .gitignore 配置说明

## 目的
此 `.gitignore` 配置仅在版本控制中保留 **核心代码文件**，排除所有生成、临时和配置文件，保持仓库整洁。

## 排除的文件类别

### 1. Python 缓存和编译文件
```
__pycache__/     # Python 字节码缓存目录
*.py[cod]        # 编译的 Python 文件
*$py.class       # 特定编译格式
*.so             # C 扩展编译文件
```
**原因**: 这些是在本地生成的临时文件，每台机器都会自动生成

### 2. Python 虚拟环境
```
.venv/
venv/
ENV/
env/
.env
```
**原因**: 虚拟环境是机器特定的，应该通过 `requirements.txt` 管理依赖

### 3. IDE 和编辑器配置
```
.vscode/         # Visual Studio Code 配置
.idea/           # JetBrains IDE（PyCharm，IntelliJ 等）
*.swp            # Vim 交换文件
*.swo            # Vim 交换文件
*~               # Backup 文件
.DS_Store        # macOS 系统文件
.project         # Eclipse 配置
.pydevproject    # Eclipse PyDev 配置
.settings/       # Eclipse 设置
*.sublime-*      # Sublime Text 项目文件
```
**原因**: IDE 配置是个人偏好，不应该强制给团队成员

### 4. 测试和覆盖率报告
```
.pytest_cache/   # pytest 缓存
.coverage        # 覆盖率数据文件
htmlcov/         # HTML 覆盖率报告
.tox/            # tox 环境
.hypothesis/     # Hypothesis 缓存
```
**原因**: 这些是本地测试生成的文件，不需要版本控制

### 5. 临时和生成的文件
```
*.tmp            # 临时文件
*.bak            # 备份文件
*.log            # 日志文件
*.out            # 程序输出文件
*.html           # 生成的 HTML（调试可视化除外）
!template.html   # 例外：保留模板文件
debug-logs/      # 调试日志目录
```
**原因**: 这些文件在每次运行时都会重新生成

### 6. 项目报告文档
```
BUGFIX_SUMMARY.md              # 修复总结报告
COMPLETION_REPORT.md           # 完成报告
FINAL_REPORT.md                # 最终报告
TEST_COMPREHENSIVE_GUIDE.md    # 测试指南
TEST_QUICK_REFERENCE.md        # 测试快速参考
TEST_SUMMARY_REPORT.md         # 测试总结报告
```
**原因**: 这些是开发过程中的临时文档，不属于项目的最终交付物

### 7. 操作系统文件
```
.DS_Store        # macOS 系统文件
Thumbs.db        # Windows 缩略图缓存
```
**原因**: 操作系统自动生成，与项目无关

### 8. 前端工具文件（如适用）
```
node_modules/
npm-debug.log
yarn-error.log
```
**原因**: Node.js 依赖应通过 `package.json` 管理

## 保留在版本控制中的文件

### 核心代码
- `src/dsvis.py` - 主模块
- `src/runtime/*.py` - 运行时系统
- `src/algorithms/*.py` - 数据结构实现
- `src/template.html` - 前端模板

### 文档
- `README.md` - 项目主文档
- `docs/API_REFERENCE.md` - API 文档
- `docs/INTERFACES_QUICK_REFERENCE.md` - 快速参考
- `docs/UNIFIED_MODE_DOCUMENTATION.md` - 模式文档

### 示例和测试
- `examples/*.py` - 使用示例
- `tests/*.py` - 测试代码

### 项目配置
- `.gitignore` - 本文件
- `setup.py` (如适用) - 包安装配置
- `requirements.txt` (如适用) - 依赖列表

## 如何使用

该 `.gitignore` 已自动应用于此项目。Git 会自动排除指定的文件和目录。

## 验证配置

查看哪些文件被忽略：
```bash
git status --ignored
```

查看一个特定文件是否会被忽略：
```bash
git check-ignore -v <file-path>
```

## 修改配置

如需调整忽略规则：
1. 编辑 `.gitignore` 文件
2. 使用 `git add .gitignore` 提交更改
3. 如需忽略已追踪的文件，使用：
   ```bash
   git rm --cached <file-path>
   ```

## 最佳实践

1. **定期审查**: 每周检查是否有不必要的文件被提交
2. **及时更新**: 当项目新增文件类型时，及时更新 `.gitignore`
3. **不要添加个人配置**: 个人的 IDE 配置应使用全局 `.gitignore`
   ```bash
   git config --global core.excludesfile ~/.gitignore_global
   ```

---

**最后更新**: 2026-04-11
