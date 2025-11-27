#!/usr/bin/env python3
import argparse
import json
from mdparser.parser_service import ParserService
from mdparser.renderer import render
from mdparser.cache_service import CacheService, InMemoryCacheBackend, RedisCacheBackend
from mdparser.perf_monitor import PerfMonitor
from mdparser.exporters.json_exporter import JsonExporter

def main():
    ap = argparse.ArgumentParser(description="Markdown -> AST -> HTML (extended CLI)")
    ap.add_argument('-i','--input', required=True, help='Input markdown file or "-" for stdin')
    ap.add_argument('-o','--output', help='Output HTML file (default stdout)')
    ap.add_argument('--cache', choices=['inmemory','redis','off'], default='off', help='Cache backend')
    ap.add_argument('--redis-host', default='localhost')
    ap.add_argument('--redis-port', type=int, default=6379)
    ap.add_argument('--show-metrics', action='store_true', help='Show perf metrics after parse')
    ap.add_argument('--export-ast-json', action='store_true', help='Also print AST as JSON')
    args = ap.parse_args()

    if args.input == '-':
        import sys
        text = sys.stdin.read()
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()

    cache_backend = None
    if args.cache == 'inmemory':
        cache_backend = InMemoryCacheBackend()
    elif args.cache == 'redis':
        cache_backend = RedisCacheBackend(host=args.redis_host, port=args.redis_port)

    cache = CacheService(cache_backend) if cache_backend else None
    perf = PerfMonitor(enable_prom=False)
    service = ParserService(cache=cache, perf=perf)

    res = service.parse(text)
    ast = res['ast']
    html = render(ast)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html)
    else:
        print(html)

    if args.export_ast_json:
        exporter = JsonExporter()
        ast_json = exporter.visit(ast)
        print("\n--- AST JSON ---")
        print(json.dumps(ast_json, ensure_ascii=False, indent=2))

    if args.show_metrics:
        print("\n--- Metrics ---")
        print("Cached:", res['cached'])
        print("Metrics:", res['metrics'])

if __name__ == '__main__':
    main()