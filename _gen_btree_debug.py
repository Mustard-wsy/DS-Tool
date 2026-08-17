"""Regenerate _btree_debug.html from bTree.py using the DSVis runtime."""
import sys
import os
sys.path.insert(0, r'e:\Study\DataStructure\DSVis')
os.chdir(r'e:\Study\DataStructure\DSVis')

from dsvis.runtime.ast_hook import run_file
from dsvis.runtime.scheduler import scheduler
from dsvis.card_renderer import render_debugger

# Prevent the scheduler's flush() from writing to a temp file + opening a browser.
scheduler.flush = lambda: None

algo = r'e:\Study\DataStructure\DSVis\bTree.py'
run_file(algo)

steps = list(scheduler.steps)
source_lines = list(scheduler.source_lines or [])
source_file = scheduler.source_file

display_indices = [i for i, s in enumerate(steps) if s.get('_visible', True)]

title = f"DSVis Debugger ({os.path.basename(source_file) if source_file else 'script'})"
from pathlib import Path
html_path = render_debugger(
    steps, source_lines,
    title=title,
    layout=None,
    display_indices=display_indices,
    source_file=source_file,
)

out = r'e:\Study\DataStructure\DSVis\_btree_debug.html'
html_text = Path(html_path).read_text(encoding='utf-8')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html_text)
print(f"Generated {out} ({len(html_text)} chars), steps={len(steps)}, visible={len(display_indices)}")
