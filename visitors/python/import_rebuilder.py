import os
import sys
import ast
from typing import Set

from visitors.python.utils import get_tab


class ImportTreeRebuilder:
    def __init__(self, result_root: str, visitor_cls, source_base_dir: str):
        self.result_root = os.path.abspath(result_root)
        self.visitor_cls = visitor_cls
        self.source_base_dir = os.path.abspath(source_base_dir)
        self.cache: Set[str] = set()

    def rebuild_import(self, module_path: str, alias_name: str = None):
        parts = module_path.split(".")
        current_path = self.result_root

        for part in parts:
            current_path = os.path.join(current_path, part)
            os.makedirs(current_path, exist_ok=True)
            init_path = os.path.join(current_path, "__init__.py")
            if not os.path.exists(init_path):
                open(init_path, 'a').close()

        mod_file = module_path.replace('.', os.sep) + ".py"
        for path in sys.path:
            candidate = os.path.join(path, mod_file)
            if os.path.exists(candidate):
                if candidate not in self.cache:
                    self.cache.add(candidate)
                    self.transpile_module(candidate)
                break

    def transpile_module(self, abs_path):
        with open(abs_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=abs_path)
        visitor = self.visitor_cls(abs_path, result_dir_path=self.result_root, rebuild_imports_tree=True)
        visitor.source_base_dir = self.source_base_dir  # ensure correct base path
        visitor.transpile(tree)
        visitor.save_result_source()

    def rewrite_import_from(self, node: ast.ImportFrom, level: int = 0) -> str:
        module = node.module
        if module:
            self.rebuild_import(module)
            names = ", ".join([alias.name for alias in node.names])
            return f"{get_tab('    ', level)}from {module} import {names}"
        return ""

    def rewrite_import(self, node: ast.Import, level: int = 0) -> str:
        rewritten = []
        for alias in node.names:
            self.rebuild_import(alias.name)
            rewritten.append(alias.name)
        return f"{get_tab('    ', level)}import {', '.join(rewritten)}"