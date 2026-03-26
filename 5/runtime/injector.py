import ast


class InjectTrigger(ast.NodeTransformer):
    def _make_trigger(self, node):
        trigger_node = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="trigger", ctx=ast.Load()),
                args=[],
                keywords=[],
            )
        )
        setattr(trigger_node, "_injected", True)
        return ast.copy_location(trigger_node, node)

    @staticmethod
    def _is_struct_target(target):
        return isinstance(target, (ast.Attribute, ast.Subscript))

    def _should_trigger_assign(self, node):
        return any(self._is_struct_target(t) for t in node.targets)

    def visit_Assign(self, node):
        self.generic_visit(node)
        if self._should_trigger_assign(node):
            return [node, self._make_trigger(node)]
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if node.target and self._is_struct_target(node.target):
            return [node, self._make_trigger(node)]
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if self._is_struct_target(node.target):
            return [node, self._make_trigger(node)]
        return node

    def visit_Delete(self, node):
        self.generic_visit(node)
        if any(self._is_struct_target(t) for t in node.targets):
            return [node, self._make_trigger(node)]
        return node

    def visit_Expr(self, node):
        """捕捉对象方法调用；是否真的变化交给 scheduler 的结构对比决定。"""
        self.generic_visit(node)

        if not isinstance(node.value, ast.Call) or getattr(node, "_injected", False):
            return node

        fn = node.value.func
        if isinstance(fn, ast.Attribute):
            return [node, self._make_trigger(node)]

        return node
