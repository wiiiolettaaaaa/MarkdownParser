import argparse
import sys
import os
from typing import Optional

from markdown_parser.lexer import Lexer
from markdown_parser.parser import Parser
from markdown_parser.renderer import HTMLRenderer
from markdown_parser.cache import (
    CacheManager,
    LRUCache,
    LFUCache,
    NoCache,
    CacheEfficiencyMeter
)


# -------------------------------------------------------------
# Global cache (can be configured via CLI)
# -------------------------------------------------------------

CACHE_STRATEGIES = {
    "none": NoCache(),
    "lru": LRUCache(capacity=256),
    "lfu": LFUCache(capacity=256)
}

cache_manager: CacheManager = CacheManager(CACHE_STRATEGIES["lru"])


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def read_file(path: str) -> str:
    if not os.path.exists(path):
        print(f"[ERROR] File does not exist: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_stdout(text: str):
    sys.stdout.write(text)
    sys.stdout.flush()


def parse_markdown(text: str):
    # Try cached AST
    cached = cache_manager.get_ast(text)
    if cached is not None:
        return cached

    lexer = Lexer(text)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    cache_manager.set_ast(text, ast)
    return ast


def render_html(ast):
    renderer = HTMLRenderer()
    return renderer.render(ast)


# -------------------------------------------------------------
# Command handlers
# -------------------------------------------------------------

def cmd_tokens(args):
    text = read_file(args.file)
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    for t in tokens:
        print(t)


def cmd_parse(args):
    text = read_file(args.file)
    ast = parse_markdown(text)
    print(ast.pretty())


def cmd_ast(args):
    # Alias for parse
    return cmd_parse(args)


def cmd_html(args):
    text = read_file(args.file)

    cached = cache_manager.get_html(text)
    if cached:
        print(cached)
        return

    ast = parse_markdown(text)
    html = render_html(ast)

    cache_manager.set_html(text, html)
    print(html)


def cmd_render(args):
    # Alias for html
    return cmd_html(args)


def cmd_cache_stats(args):
    stats = cache_manager.stats()
    print("--- CACHE STATS ---")
    for k, v in stats.items():
        print(f"{k}: {v}")


def cmd_cache_clear(args):
    cache_manager.clear()
    print("Cache cleared.")


def cmd_bench(args):
    text = read_file(args.file)

    meter = CacheEfficiencyMeter(
        parse_func=parse_markdown,
        render_func=render_html,
        cache_manager=cache_manager
    )

    results = meter.measure(text, repeat=args.repeat)

    print("=== BENCHMARK RESULTS ===")
    print(f"Avg time (no cache):   {results['avg_no_cache']:.6f}s")
    print(f"Avg time (with cache): {results['avg_with_cache']:.6f}s")
    print(f"Speedup:               {results['speedup']:.3f}x")
    print(f"Cache hit ratio:       {results['hit_ratio']:.2%}")
    print("--- CACHE RAW STATS ---")
    for k, v in results["cache_stats"].items():
        print(f"{k}: {v}")


# -------------------------------------------------------------
# Interactive REPL mode
# -------------------------------------------------------------

def interactive_repl():
    print("Markdown Parser Interactive Mode")
    print("Commands:")
    print("  :q                  exit")
    print("  :html TEXT          parse and render html")
    print("  :ast TEXT           parse and print AST")
    print("  :tokens TEXT        show tokens")
    print("------------------------------------------")

    while True:
        try:
            line = input("md> ")
        except EOFError:
            break

        if line.strip() == ":q":
            break

        if line.startswith(":html "):
            text = line[6:]
            ast = parse_markdown(text)
            html = render_html(ast)
            print(html)
            continue

        if line.startswith(":ast "):
            text = line[5:]
            ast = parse_markdown(text)
            print(ast.pretty())
            continue

        if line.startswith(":tokens "):
            text = line[8:]
            lexer = Lexer(text)
            for t in lexer.tokenize():
                print(t)
            continue

        print("[unknown command]")


# -------------------------------------------------------------
# Main parser builder
# -------------------------------------------------------------

def build_cli():
    parser = argparse.ArgumentParser(
        prog="markdown_parser",
        description="Markdown → AST → HTML Parser CLI"
    )

    parser.add_argument(
        "--cache",
        choices=["none", "lru", "lfu"],
        default="lru",
        help="Cache strategy (default: lru)"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive REPL mode"
    )

    subparsers = parser.add_subparsers(dest="command")

    # tokens
    p = subparsers.add_parser("tokens", help="Display tokens")
    p.add_argument("file")
    p.set_defaults(func=cmd_tokens)

    # parse
    p = subparsers.add_parser("parse", help="Parse and show AST")
    p.add_argument("file")
    p.set_defaults(func=cmd_parse)

    # ast
    p = subparsers.add_parser("ast", help="Alias for parse")
    p.add_argument("file")
    p.set_defaults(func=cmd_ast)

    # html
    p = subparsers.add_parser("html", help="Render HTML")
    p.add_argument("file")
    p.set_defaults(func=cmd_html)

    # render
    p = subparsers.add_parser("render", help="Alias for html")
    p.add_argument("file")
    p.set_defaults(func=cmd_render)

    # bench
    p = subparsers.add_parser("bench", help="Benchmark with/without cache")
    p.add_argument("file")
    p.add_argument("--repeat", type=int, default=20)
    p.set_defaults(func=cmd_bench)

    # cache group
    cache_parser = subparsers.add_parser("cache", help="Cache operations")
    cache_parser.add_argument("--stats", action="store_true")
    cache_parser.add_argument("--clear", action="store_true")

    # special handler
    cache_parser.set_defaults(func=lambda args: (
        cmd_cache_stats(args) if args.stats else cmd_cache_clear(args)
    ))

    return parser


# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------

def main():
    global cache_manager

    parser = build_cli()
    args = parser.parse_args()

    # Handle interactive mode
    if args.interactive:
        interactive_repl()
        return

    # Configure cache strategy
    cache_manager = CacheManager(CACHE_STRATEGIES[args.cache])

    # Run command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()