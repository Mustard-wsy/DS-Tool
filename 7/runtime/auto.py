"""One-line auto hook: put `import runtime.auto` at the top of user scripts."""

import inspect
import os
from pathlib import Path

from .ast_hook import run_file


def _find_main_script() -> str | None:
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


def _bootstrap() -> None:
    if os.environ.get("DSVIS_AST_RUNNING") == "1":
        return

    main_file = _find_main_script()
    if not main_file:
        return

    run_file(main_file)
    raise SystemExit(0)


_bootstrap()
