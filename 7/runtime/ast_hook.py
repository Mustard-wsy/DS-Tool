import ast
import os

from .injector import InjectTrigger

PRINT_TRANSFORMED_CODE = False


def _to_bool_env(value):
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def run_file(filepath, print_transformed_code=False):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    tree = ast.parse(code, filename=filepath)

    transformer = InjectTrigger()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    should_print = (
        bool(print_transformed_code)
        or PRINT_TRANSFORMED_CODE
        or _to_bool_env(os.environ.get("DSVIS_PRINT_AST"))
    )
    if should_print:
        print("[dsvis] Injected AST result:")
        print(ast.unparse(new_tree))

    compiled = compile(new_tree, filename=filepath, mode="exec")

    previous_flag = os.environ.get("DSVIS_AST_RUNNING")
    os.environ["DSVIS_AST_RUNNING"] = "1"
    from .trigger import trigger

    global_env = {
        "trigger": trigger,
        "__name__": "__main__",
        "__file__": filepath,
    }
    try:
        exec(compiled, global_env)
    finally:
        if previous_flag is None:
            os.environ.pop("DSVIS_AST_RUNNING", None)
        else:
            os.environ["DSVIS_AST_RUNNING"] = previous_flag
