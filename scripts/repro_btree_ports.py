"""Repro: B-tree mode — hide children, emit child ports from key gaps.

Runs bTree.py in a clean namespace (avoids polluting the captured global
scope with Path objects) and renders to a fixed output file
`_btree_ports.html` (system browser suppressed) for inspection.
"""
import os
import sys
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Prevent bTree.py's dsvis.auto() from AST-re-running the caller script.
os.environ["DSVIS_AST_RUNNING"] = "1"

import dsvis  # noqa: E402

dsvis.set_mode("coarse")
dsvis.set_text_flow("vertical")
dsvis.set_layout("vertical")

import dsvis.card_renderer as cr  # noqa: E402
import dsvis.runtime.scheduler as sched  # noqa: E402
import webbrowser  # noqa: E402

webbrowser.open = lambda *a, **k: None
_orig_render = cr.render_debugger


def patched_render(steps, source_lines, **kw):
    p = _orig_render(steps, source_lines, **kw)
    out = ROOT / "_btree_ports.html"
    out.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"WROTE {out}")
    return out


cr.render_debugger = patched_render
sched.render_debugger = patched_render

# Run bTree.py as __main__ in a fresh namespace (its own globals only).
ns = {"__name__": "__main__", "__file__": str(ROOT / "bTree.py")}
runpy.run_path(str(ROOT / "bTree.py"), run_name="__main__", init_globals=ns)
