📦 Цель
При вызове скрипта с указанием директории результата:


python3 main.py sources/multiply_import.py --output result/
все импорты внутри multiply_import.py и всех его зависимостей будут перестроены в дерево, и переписаны так, чтобы:

корнем был result/

импорты указывали на другие .py-файлы, расположенные внутри result/

📌 План реализации
1. Расширить аргументы CLI (main.py)
Добавить:


parser.add_argument('--output', type=str, required=True, help='Output directory')
2. Передавать result_dir_path в PythonVisitor

visitor = PythonVisitor(module=os.path.abspath(infile.name),
                        result_dir_path=args.output,
                        rebuild_imports_tree=True)
3. Обновить visit_ImportFrom и visit_Import
В visit_ImportFrom():

Разбить node.module на части: sources.first_level_package...

Восстановить путь:


path = os.path.join(self.result_dir_name, *node.module.split("."))
Создать подпапки и __init__.py файлы (если rebuild_imports_tree=True)

Вернуть строку:


from result.sources.first_level_package... import X
4. Автоматически копировать тела импортированных модулей
Найти соответствующий .py-файл из sys.path или PYTHONPATH

Распарсить его ast.parse

Рекурсивно применить visitor.transpile() на него

Сохранить его в result_dir_path

5. Включать __init__.py
В каждой папке, созданной в result_dir_path, создать __init__.py

Для корректной структуры пакета Python

6. Дополнительно
Добавить кеш уже обработанных модулей, чтобы не обрабатывать повторно

