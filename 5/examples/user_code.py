import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 用户只需在脚本开头引入这一行即可启用 AST 自动插桩。
if os.environ.get("DSVIS_AST_RUNNING") != "1":
    import runtime.auto  # noqa: F401

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
