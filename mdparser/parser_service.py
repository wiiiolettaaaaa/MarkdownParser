from .lexer import Lexer
from .parser import Parser
from .factory import NodeFactory
from .cache_service import CacheService
from .perf_monitor import PerfMonitor

class ParserService:
    def __init__(self, factory: NodeFactory = None, cache: CacheService = None, perf: PerfMonitor = None):
        self.factory = factory or NodeFactory()
        self.cache = cache or CacheService()
        self.perf = perf or PerfMonitor()

    def parse(self, text: str):
        ast = self.cache.get_ast(text)
        if ast is not None:
            return {'ast': ast, 'cached': True, 'metrics': None}

        self.perf.start()
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens, factory=self.factory)
        ast = parser.parse()
        self.perf.stop()
        metrics = self.perf.report()
        self.cache.set_ast(text, ast)
        return {'ast': ast, 'cached': False, 'metrics': metrics}