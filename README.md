# MarkdownParser

### Запуск програми:
- Встановіть залежності:
```shell
pip install -r requirements.txt
```

- Переходимо в папку з CLI
```shell
cd mdparser
```

```shell
python cli.py tokens samples/sample_medium.md
```
-	Виконує лексичний аналіз Markdown-файлу.
-	Розбиває текст на токени (найменші смислові одиниці: #, *, текст, [, ], (, ) і т.д.).
-	Виводить список токенів з їхніми типами і позиціями у файлі.
-	Корисно для debug або перевірки правильності токенізації.
```shell
python cli.py html samples/sample_medium.md
```
- Перетворює Markdown у HTML.
- Наприклад, `# Заголовок` → `<h1>Заголовок</h1>`, `*жирний*` → `<strong>жирний</strong>`.
- Використовується для рендерингу Markdown у веб-формат.
```shell
python cli.py parse samples/sample_medium.md
```
- Виконує синтаксичний аналіз (парсинг) Markdown.
- Створює внутрішнє дерево блоків (наприклад, заголовки, списки, абзаци).
- Виводить структуру документа у більш “людиноподібному” вигляді, ніж просто токени.
```shell
python cli.py ast samples/sample_medium.md
```
- Створює AST (Abstract Syntax Tree) Markdown-документа.
- AST — це формалізоване дерево, де кожен вузол описує тип елементу (Heading, Paragraph, List, Text) та його вміст.
- Дуже корисно для додаткової обробки документа або для генерації різних форматів (HTML, PDF, LaTeX).

### Запуск тестів:
```shell
pytest -q
```

#### Також можна подивитись на скільки тести покривають код

1. Встановлення coverage
```shell
pip install coverage
```
2. Запуск тестів із вимірюванням покриття
```shell
coverage run -m pytest
```
3. Перегляд звіту в терміналі
```shell
coverage report -m
```