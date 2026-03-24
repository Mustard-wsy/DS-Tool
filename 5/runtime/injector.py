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

    def visit_Assign(self, node):
        self.generic_visit(node)
        return [node, self._make_trigger(node)]

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        return [node, self._make_trigger(node)]

    def visit_Expr(self, node):
        """捕捉函数调用，例如: lst.append(x)"""
        self.generic_visit(node)

        if isinstance(node.value, ast.Call) and not getattr(node, "_injected", False):
            return [node, self._make_trigger(node)]

        return node
