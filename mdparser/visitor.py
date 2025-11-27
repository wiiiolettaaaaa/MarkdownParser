from abc import ABC, abstractmethod

class Visitor(ABC):
    @abstractmethod
    def visit(self, node):
        pass

class BaseVisitor(Visitor):
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        fn = getattr(self, method, self.generic_visit)
        return fn(node)

    def generic_visit(self, node):
        results = {}
        for name, attr in getattr(node, '__dict__', {}).items():
            if isinstance(attr, list):
                results[name] = [self.visit(child) if hasattr(child, '__class__') else child for child in attr]
            elif hasattr(attr, '__class__'):
                results[name] = self.visit(attr)
            else:
                results[name] = attr
        return {node.__class__.__name__: results}