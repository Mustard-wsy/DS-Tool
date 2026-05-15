"""
DSVis - 数据结构可视化工具

主要模块导出
"""

from .dsvis import (
    capture,
    auto,
    watch_vars,
    bind_fields,
    set_mode,
    enable_breakpoints,
    disable_breakpoints,
)

__version__ = "1.0.0"
__all__ = [
    "capture",
    "auto",
    "watch_vars",
    "bind_fields",
    "set_mode",
    "enable_breakpoints",
    "disable_breakpoints",
]
