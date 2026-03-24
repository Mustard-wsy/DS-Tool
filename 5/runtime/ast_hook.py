import ast

from .injector import InjectTrigger

PRINT_TRANSFORMED_CODE = True


def run_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    tree = ast.parse(code, filename=filepath)

    transformer = InjectTrigger()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    if PRINT_TRANSFORMED_CODE:
        print(ast.unparse(new_tree))

    compiled = compile(new_tree, filename=filepath, mode="exec")

    from .trigger import trigger

    global_env = {
        "trigger": trigger,
        "__name__": "__main__",
        "__file__": filepath,
    }

    exec(compiled, global_env)
