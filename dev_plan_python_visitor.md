# 📘 План завершения реализации `PythonVisitor` для проекта Lobster

> За дополнительной помощью или для запуска других нейросетей на русском, заходи на [GPTOnline.ai/ru](https://gptonline.ai/ru/)

---

## 🎯 Цель

Создать полноценный `PythonVisitor`, который:

- Корректно парсит Python-код в AST
- Восстанавливает его обратно в Python-код с сохранением структуры, типов и стиля
- Поддерживает все ключевые фичи языка: классы, декораторы, наследование, async, property, etc.
- Реализует AOT-компиляцию функций с динамической заменой на компилированную версию

---

## 📦 Базовая поддержка AST-узлов (must have)

### Структурные элементы:
- [x] `Module`
- [x] `FunctionDef`
- [x] `AsyncFunctionDef`
- [x] `ClassDef`
- [x] `If`, `Else`, `Elif`
- [x] `For`, `While`, `Break`, `Continue`, `Pass`
- [x] `Try`, `Except`, `Finally`, `Raise`

### Работа с переменными:
- [x] `Assign`, `AnnAssign`
- [x] `AugAssign`
- [x] `Global`, `Nonlocal`
- [x] `Delete`

### Выражения:
- [x] `Expr`, `Call`
- [x] `BinOp`, `BoolOp`, `UnaryOp`
- [x] `Compare`, `IfExp`
- [x] `Lambda`, `Yield`, `Await`
- [x] `Subscript`, `Attribute`, `Name`, `Constant`, `List`, `Dict`, `Set`, `Tuple`

### Импорты:
- [x] `Import`, `ImportFrom`
- [x] Восстановление вложенной структуры дерева импортов (опция `--rebuild_imports_tree`)
- [x] Создание `__init__.py` в подпапках

---

## 🧠 Расширенные возможности

### 🎯 1. Декораторы
- [x] Простые (`@decorator`)
- [x] Вложенные (`@outer(arg)(@inner)`)
- [ ] Обработка аргументов декоратора
- [ ] Учитывать порядок декораторов

### 🎯 2. Аргументы функций
- [x] Позиционные с аннотациями
- [ ] `*args`, `**kwargs`
- [ ] Значения по умолчанию разных типов
- [ ] Аннотации с `Optional`, `List[str]`, и др.

### 🎯 3. Поддержка async/await
- [x] `AsyncFunctionDef`
- [x] `Await`, `AsyncWith`, `AsyncFor`

### 🎯 4. Объекты
- [x] Поддержка `@property`
- [ ] Вложенные классы
- [x] Множественное наследование
- [ ] `super()`, `__init__`, `__str__`, `__repr__` и др.

### 🎯 5. Комментарии и docstring
- [x] Восстановление docstring через `get_docstring()`
- [ ] Поддержка встроенных/inline комментариев

---

### 🎯 6. AOT-компиляция с динамической заменой

#### 📌 Описание:
Создать декоратор `@compile_and_replace(lang='cython')`, который:
- При первом вызове функции:
  1. Собирает её AST и стек вызовов
  2. Транспайлит через Lobster в указанный язык
  3. Компилирует полученный код
  4. Импортирует и заменяет оригинальную функцию
- Поведение аналогично JIT, но корректнее назвать его:
  - **AOT (Ahead-Of-Time) Compilation with Dynamic Dispatch**

#### 🛠️ Шаги реализации:
1. **Создание декоратора**
2. **Анализ AST и зависимости**
3. **Формирование изолированного мини-модуля**
4. **Запуск Lobster с нужным visitor**
5. **Компиляция через `pyximport`/`ctypes`/`maturin`**
6. **Импорт и `functools.wraps` для подмены**
7. **Поддержка кэширования результата компиляции**

---

## 🔧 Архитектура и утилиты

### 💡 Использовать:
- `BaseModuleVisitor.visit_*`
- `get_tab()` — форматирование отступов
- `parse_func_args()` — разбор аргументов
- `parse_func_body()` — разбор тела функции
- `parse_decorators_list()` — декораторы

### 🛠️ Расширить:
- `visit_Expr`, `visit_Call`, `visit_Assign`, `visit_ImportFrom`
- Добавить парсинг вложенных блоков

---

## 🧪 Тестирование

### 📂 Примеры:
- `sources/func.py`, `sources/decorator.py`, `sources/multiple_inheritance.py`

### ✔️ Проверка:
- Точность трансформации AST → Python → AST
- Сохранение семантики (функциональности)
- Проверка всех ветвей кода (try/except/finally)
- Проверка декоратора AOT: вызов → компиляция → подмена → повторный вызов

---

## ✅ Финал

- [ ] Убедиться, что `visitor.transpile()` обходит все узлы
- [ ] Результат `visitor.save_result_source()` = валидный `.py`-файл
- [ ] Документировать `README.md`

---
