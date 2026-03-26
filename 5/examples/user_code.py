import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__" and os.environ.get("DSVIS_AST_RUNNING") != "1":
    from runtime.ast_hook import run_file

    run_file(str(Path(__file__).resolve()))
    raise SystemExit(0)

import dsvis


class Node:
    def __init__(self, value):
        self.next = None
        self.prev = None
        self.value = value


a = Node(1)
b = Node(2)
c = Node(3)

a.next = b
b.next = c
c.prev = b

numbers = []
numbers.append(a.value)

# 手动 capture 仍可保留，AST 插桩会自动追加 trigger。
dsvis.capture()
