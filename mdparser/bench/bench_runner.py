# bench/bench_runner.py
import time
from mdparser.markdown_parser.parser import Parser
from mdparser.markdown_parser.renderer import HTMLRenderer
from mdparser.markdown_parser.cache import CacheManager
from  mdparser.markdown_parser.monitor import PerformanceMonitor
import glob
import os

def run_bench(samples_dir: str, cache_enabled: bool=False, iterations: int=1):
    files = glob.glob(os.path.join(samples_dir, '*.md'))
    cache = CacheManager(enabled=cache_enabled)
    renderer = HTMLRenderer()
    monitor = PerformanceMonitor()
    times = []
    for it in range(iterations):
        for f in files:
            with open(f, 'r', encoding='utf-8') as fh:
                txt = fh.read()
            doc = None
            if cache_enabled:
                doc = cache.get(txt)
            if doc is None:
                monitor.start_snapshot()
                t0 = time.time()
                parser = Parser(txt)
                doc = parser.parse()
                t = time.time() - t0
                monitor.stop_snapshot()
                times.append(t)
                if cache_enabled:
                    cache.set(txt, doc)
            html = renderer.render(doc)
    print("runs:", len(times))
    print("avg:", sum(times)/len(times) if times else 0.0)
    print("cache stats:", cache.stats() if cache_enabled else {})
    print("monitor agg:", monitor.aggregate())

if __name__ == '__main__':
    run_bench('../samples', cache_enabled=True, iterations=2)