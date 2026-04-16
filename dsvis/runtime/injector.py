import ast
from .config import get_mode


class InjectTrigger(ast.NodeTransformer):
    METHOD_BLACKLIST = {
        "__init__",
        "__repr__",
        "__str__",
        "__len__",
        "__iter__",
        "__next__",
        "__contains__",
    }

    def __init__(self):
        super().__init__()
        self._func_stack = []

    def _make_trigger(self, node):
        trigger_node = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="trigger", ctx=ast.Load()),
                args=[ast.Constant(value=getattr(node, "lineno", None))],
                keywords=[],
            )
        )
        setattr(trigger_node, "_injected", True)
        return ast.copy_location(trigger_node, node)

    @staticmethod
    def _is_struct_target(target):
        return isinstance(target, (ast.Attribute, ast.Subscript))

    def _target_contains_struct(self, target):
        if self._is_struct_target(target):
            return True
        if isinstance(target, ast.Starred):
            return self._target_contains_struct(target.value)
        if isinstance(target, (ast.Tuple, ast.List)):
            return any(self._target_contains_struct(elt) for elt in target.elts)
        return False

    @staticmethod
    def _is_constructor_call(value):
        if not isinstance(value, ast.Call):
            return False
        fn = value.func
        if isinstance(fn, ast.Name):
            return fn.id[:1].isupper()
        if isinstance(fn, ast.Attribute):
            return fn.attr[:1].isupper()
        return False

    def _should_trigger_assign(self, node):
        if get_mode() == "fine":
            return bool(node.targets)
        if any(self._target_contains_struct(t) for t in node.targets):
            return True
        has_name_target = any(isinstance(t, ast.Name) for t in node.targets)
        return has_name_target and self._is_constructor_call(node.value)

    def _in_init(self):
        return bool(self._func_stack and self._func_stack[-1] == "__init__")

    def visit_FunctionDef(self, node):
        self._func_stack.append(node.name)
        try:
            return self.generic_visit(node)
        finally:
            self._func_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self._func_stack.append(node.name)
        try:
            return self.generic_visit(node)
        finally:
            self._func_stack.pop()

    def visit_Assign(self, node):
        self.generic_visit(node)
        if self._in_init():
            return node
        if self._should_trigger_assign(node):
            return [node, self._make_trigger(node)]
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if self._in_init():
            return node
        if node.target and self._target_contains_struct(node.target):
            return [node, self._make_trigger(node)]
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if self._in_init():
            return node
        if self._target_contains_struct(node.target):
            return [node, self._make_trigger(node)]
        return node

    def visit_Delete(self, node):
        self.generic_visit(node)
        if self._in_init():
            return node
        if any(self._target_contains_struct(t) for t in node.targets):
            return [node, self._make_trigger(node)]
        return node

    def _inject_loop_iteration_trigger(self, node):
        if get_mode() != "fine" or self._in_init():
            return node
        loop_trigger = self._make_trigger(node)
        node.body.insert(0, loop_trigger)
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        return self._inject_loop_iteration_trigger(node)

    def visit_AsyncFor(self, node):
        self.generic_visit(node)
        return self._inject_loop_iteration_trigger(node)

    def visit_While(self, node):
        self.generic_visit(node)
        return self._inject_loop_iteration_trigger(node)

    def visit_Expr(self, node):
        """捕捉对象方法调用（黑名单除外）；是否真的变化交给 scheduler 判定。"""
        self.generic_visit(node)
        if self._in_init():
            return node

        if not isinstance(node.value, ast.Call) or getattr(node, "_injected", False):
            return node

        if get_mode() == "fine":
            return [node, self._make_trigger(node)]

        fn = node.value.func
        if isinstance(fn, ast.Attribute):
            if fn.attr in self.METHOD_BLACKLIST:
                return node
            if fn.attr.startswith("__") and fn.attr.endswith("__"):
                return node
            return [node, self._make_trigger(node)]

        return node
