"""DSVis — 数据结构可视化库的公共 API 层。

所有内部实现已拆分到独立模块：
- ``introspection``    类型内省
- ``stack_serializer`` 调用栈序列化
- ``graph_builder``    图遍历 (walk_graph)
- ``card_renderer``    G6 卡片渲染 (build_g6_data / render_debugger)
- ``field_binding``    字段绑定 (bind_fields)
"""

import functools
import inspect
import os
from pathlib import Path
from typing import Any, Callable, TypeVar, overload

from .runtime.config import (
    get_mode,
    get_pointer_watchers,
    get_watch_vars,
    add_global_watch_vars,
    remove_global_watch_vars,
    set_layout,
    set_text_flow,
    set_mode,
    enable_breakpoints as _enable_bp,
    disable_breakpoints as _disable_bp,
)
from .runtime.scheduler import scheduler

# Re-export implementation functions so callers that used the old private API
# (e.g. scheduler, tests) continue to work.
from .introspection import (          # noqa: F401 — re-exported
    typename as _typename,
    short as _short,
    stack_display_text as _stack_display_text,
    stack_tree_item_text as _stack_tree_item_text,
    is_primitive as _is_primitive,
    is_class_object as _is_class_object,
    is_container as _is_container,
    is_renderable as _is_renderable,
    is_graph_root_value as _is_graph_root_value,
    format_typed_label as _format_typed_label,
    iter_container_items as _iter_container_items,
    iter_object_items as _iter_object_items,
)
from .stack_serializer import (       # noqa: F401
    serialize_runtime_stack as _serialize_runtime_stack,
    serialize_scope_rows as _serialize_scope_rows,
)
from .graph_builder import (          # noqa: F401
    walk_graph as _walk,
)
from .card_renderer import (          # noqa: F401
    build_g6_data as _build_g6_data,
    render_debugger as _render_debugger,
)
from .field_binding import bind_fields  # noqa: F401 — public re-export

__all__ = [
    "capture",
    "auto",
    "visualize",
    "watch_vars",
    "bind_fields",
    "set_mode",
    "set_layout",
    "set_text_flow",
    "enable_breakpoints",
]

_DEFAULT_LAYOUT = {
    "type": "dagre",
    "rankdir": "LR",
    "nodesep": 120,
    "ranksep": 220,
}

_PACKAGE_ROOT = Path(__file__).resolve().parent
_DecoratorFunc = TypeVar("_DecoratorFunc", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def _normalize_watch_names(var_names):
    if len(var_names) == 1 and isinstance(var_names[0], (list, tuple, set, frozenset)):
        candidates = var_names[0]
    else:
        candidates = var_names

    normalized = []
    for name in candidates:
        text = str(name).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_layout(layout):
    if layout is None:
        return dict(_DEFAULT_LAYOUT)

    if isinstance(layout, str):
        normalized = layout.strip().lower()
        if not normalized or normalized == "default":
            return dict(_DEFAULT_LAYOUT)
        if normalized in {"horizontal", "horizon", "lr"}:
            merged = dict(_DEFAULT_LAYOUT)
            merged["rankdir"] = "LR"
            return merged
        if normalized in {"vertical", "tb"}:
            merged = dict(_DEFAULT_LAYOUT)
            merged["rankdir"] = "TB"
            return merged

    if isinstance(layout, bool):
        merged = dict(_DEFAULT_LAYOUT)
        merged["rankdir"] = "LR" if layout else "TB"
        return merged

    if isinstance(layout, dict):
        merged = dict(_DEFAULT_LAYOUT)
        merged.update(layout)
        if "horizon" in merged:
            merged["rankdir"] = "LR" if bool(merged.pop("horizon")) else "TB"
        layout_type = str(merged.get("type", "")).strip().lower()
        if layout_type in {"snake", "concentric", "snakelayout", "concentriclayout"}:
            raise ValueError("snake / concentric 布局已移除，仅支持 dagre 类布局参数")
        return merged

    raise ValueError("layout 参数类型无效，必须是布局字典或 None")


# ---------------------------------------------------------------------------
# watch_vars
# ---------------------------------------------------------------------------

class _WatchVarsToken:
    def __init__(self, names):
        self._names = set(names)

    def __call__(self, fn):
        remove_global_watch_vars(self._names)
        setattr(fn, "__dsvis_watch_vars__", set(self._names))
        return fn


@overload
def watch_vars(*var_names: str) -> _WatchVarsToken: ...


def watch_vars(*var_names):
    """控制变量观察范围。

    1) 直接调用：全局名字匹配
       watch_vars("arr", "head")

    2) 装饰器：仅当前函数内变量
       @watch_vars("arr", "i")
       def run(...):
           ...
    """
    names = _normalize_watch_names(var_names)
    add_global_watch_vars(names)
    return _WatchVarsToken(names)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def capture(
    max_nodes=300,
    include_private=False,
    include_containers=None,
    focus_vars=None,
    pointer_watchers=None,
    _caller_frame=None,
):
    frame = inspect.currentframe()
    caller = _caller_frame if _caller_frame is not None else (frame.f_back if frame else None)

    if not caller:
        print("[dsvis] 无法获取调用帧")
        return

    try:
        mode = get_mode()
        container_flag = (mode == "fine") if include_containers is None else include_containers
        merged_focus = set(get_watch_vars()) | set(focus_vars or [])
        merged_pointers = list(get_pointer_watchers()) + list(pointer_watchers or [])

        scheduler.request_update(
            caller_frame=caller,
            lineno=caller.f_lineno,
            observed_vars=merged_focus,
            pointer_watchers=merged_pointers,
            max_nodes=max_nodes,
            include_private=include_private,
            include_containers=container_flag,
        )
    finally:
        del frame
        if _caller_frame is None and caller:
            del caller


def _find_main_script():
    frame = inspect.currentframe()
    try:
        current = frame.f_back if frame else None
        while current:
            g = current.f_globals
            if g.get("__name__") == "__main__" and g.get("__file__"):
                return str(Path(g["__file__"]).resolve())
            current = current.f_back
    finally:
        if frame:
            del frame
    return None


def auto():
    """自动追踪模式。

    在脚本顶部调用，启用 AST 自动插桩：:

        import dsvis
        dsvis.auto()

        def main():
            ...

        main()
    """
    frame = inspect.currentframe()
    try:
        caller = frame.f_back if frame else None
        if caller and caller.f_code.co_name == "<module>":
            if os.environ.get("DSVIS_AST_RUNNING") != "1":
                main_file = _find_main_script()
                if main_file and Path(main_file).resolve() != Path(__file__).resolve():
                    from .runtime.ast_hook import run_file
                    run_file(main_file)
                    raise SystemExit(0)
    finally:
        del frame


def disable_breakpoints():
    """关闭断点模式。

    关闭后采集粒度由 set_mode() 决定（默认 fine），前端不再显示
    逐行步进按钮且断点点击失效。
    """
    _disable_bp()


def enable_breakpoints():
    """启用断点模式（默认开启）。

    强制以 line 粒度采集，前端可逐行步进和插入断点。
    """
    _enable_bp()
