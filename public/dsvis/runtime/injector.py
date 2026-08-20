import ast
from .config import get_mode, breakpoints_enabled


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
        self._watch_vars_stack = []

    @staticmethod
    def _parse_watch_vars_from_decorators(decorators):
        watched = set()
        for deco in decorators or []:
            if not isinstance(deco, ast.Call):
                continue

            fn = deco.func
            is_watch_vars = False
            if isinstance(fn, ast.Name) and fn.id == "watch_vars":
                is_watch_vars = True
            elif isinstance(fn, ast.Attribute) and fn.attr == "watch_vars":
                is_watch_vars = True

            if not is_watch_vars:
                continue

            for arg in deco.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    text = arg.value.strip()
                    if text:
                        watched.add(text)
                    continue
                if isinstance(arg, (ast.List, ast.Tuple, ast.Set)):
                    for elt in arg.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            text = elt.value.strip()
                            if text:
                                watched.add(text)
        return watched

    def _make_trigger(self, node, _source="mode"):
        watched_vars = self._watch_vars_stack[-1] if self._watch_vars_stack else set()
        keywords = [
            ast.keyword(arg="_source", value=ast.Constant(value=_source)),
        ]
        if watched_vars:
            keywords.append(
                ast.keyword(
                    arg="observed_vars",
                    value=ast.List(
                        elts=[ast.Constant(value=name) for name in sorted(watched_vars)],
                        ctx=ast.Load(),
                    ),
                )
            )

        trigger_node = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="trigger", ctx=ast.Load()),
                args=[ast.Constant(value=getattr(node, "lineno", None))],
                keywords=keywords,
            )
        )
        setattr(trigger_node, "_injected", True)
        return ast.copy_location(trigger_node, node)

    @staticmethod
    def _is_struct_target(target):
        return isinstance(target, (ast.Attribute, ast.Subscript))

    @staticmethod
    def _target_contains_name(target, names):
        if not names:
            return False
        if isinstance(target, ast.Name):
            return target.id in names
        if isinstance(target, ast.Starred):
            return InjectTrigger._target_contains_name(target.value, names)
        if isinstance(target, (ast.Tuple, ast.List)):
            return any(InjectTrigger._target_contains_name(elt, names) for elt in target.elts)
        return False

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
        watched_vars = self._watch_vars_stack[-1] if self._watch_vars_stack else set()

        if any(self._target_contains_name(t, watched_vars) for t in node.targets):
            return True

        if get_mode() == "fine":
            return bool(node.targets)
        if any(self._target_contains_struct(t) for t in node.targets):
            return True
        has_name_target = any(isinstance(t, ast.Name) for t in node.targets)
        return has_name_target and self._is_constructor_call(node.value)

    def _in_init(self):
        return bool(self._func_stack and self._func_stack[-1] == "__init__")

    def _inject_line_triggers(self, stmts):
        """Recursively inject a trigger() call after every statement in a body.

        Unlike the coarse/fine per-statement visitors, this method works on
        *all* nesting levels so that breakpoints can stop on any line — not
        just at the function top-level.
        """
        if not breakpoints_enabled():
            return stmts

        COMPOUND_BODIES = (ast.For, ast.AsyncFor, ast.While, ast.If,
                           ast.With, ast.AsyncWith, ast.Try)

        new_body = []
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            # Recurse into nested statement bodies
            for attr in ("body", "orelse", "finalbody"):
                child = getattr(stmt, attr, None)
                if isinstance(child, list):
                    setattr(stmt, attr, self._inject_line_triggers(child))
            if isinstance(stmt, ast.Try):
                for handler in getattr(stmt, "handlers", []) or []:
                    handler.body = self._inject_line_triggers(handler.body)

            is_injected = getattr(stmt, "_injected", False)
            new_body.append(stmt)
            if isinstance(stmt, ast.stmt) and not is_injected:
                # If the very next element is an already-injected mode trigger,
                # place the line trigger AFTER it so mode fires first.
                if i + 1 < len(stmts) and getattr(stmts[i + 1], "_injected", False):
                    new_body.append(stmts[i + 1])
                    new_body.append(self._make_trigger(stmt, _source="line"))
                    i += 1  # skip the mode trigger (already consumed)
                else:
                    new_body.append(self._make_trigger(stmt, _source="line"))
            i += 1
        return new_body

    def visit_FunctionDef(self, node):
        watched_vars = self._parse_watch_vars_from_decorators(node.decorator_list)
        self._func_stack.append(node.name)
        self._watch_vars_stack.append(watched_vars)
        try:
            node = self.generic_visit(node)
            node.body = self._inject_line_triggers(node.body)
            return node
        finally:
            self._watch_vars_stack.pop()
            self._func_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        watched_vars = self._parse_watch_vars_from_decorators(node.decorator_list)
        self._func_stack.append(node.name)
        self._watch_vars_stack.append(watched_vars)
        try:
            node = self.generic_visit(node)
            node.body = self._inject_line_triggers(node.body)
            return node
        finally:
            self._watch_vars_stack.pop()
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
        watched_vars = self._watch_vars_stack[-1] if self._watch_vars_stack else set()
        if node.target and self._target_contains_name(node.target, watched_vars):
            return [node, self._make_trigger(node)]
        if node.target and self._target_contains_struct(node.target):
            return [node, self._make_trigger(node)]
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if self._in_init():
            return node
        watched_vars = self._watch_vars_stack[-1] if self._watch_vars_stack else set()
        if self._target_contains_name(node.target, watched_vars):
            return [node, self._make_trigger(node)]
        if self._target_contains_struct(node.target):
            return [node, self._make_trigger(node)]
        return node

    def visit_Delete(self, node):
        self.generic_visit(node)
        if self._in_init():
            return node
        watched_vars = self._watch_vars_stack[-1] if self._watch_vars_stack else set()
        if any(self._target_contains_name(t, watched_vars) for t in node.targets):
            return [node, self._make_trigger(node)]
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
