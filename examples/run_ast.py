import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.ast_hook import run_file


if __name__ == "__main__":
    run_file(str(Path(__file__).resolve().parent / "user_code.py"))
