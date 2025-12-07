# Medium Sample
Paragraph 1

> This is a blockquote with `inline code`.

```python
def f():
    return "hello"
```

*	list a
*	list b

## samples/sample_large.md
(створіть шляхом дублювання medium багато разів; bench runner очікує .md файли)

---

# README коротко
```md
# Markdown Parser Project

Запуск:
- Встановіть залежності: pytest, hypothesis, pytest-benchmark, psutil, locust (опціонально)
- Запуск CLI: `python cli.py --input samples --cache on --benchmark --stats`
- Запуск тестів: `pytest -q`
- Benchmark локально: `python bench/bench_runner.py`
```