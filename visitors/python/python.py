import ast
import os
from typing import List
from visitors.base import BaseModuleVisitor
from visitors.python.utils import get_tab, parse_func_body, parse_func_args, remove_indent_level, parse_decorators_list, \
    const_node_type_names


class PythonModuleSaver:

    def __init__(self, module_name: str, instructions: List[str]):
        self.module_name = module_name
        self.instructions: List[str] = instructions

    def save(self):
        os.system(f"mkdir result")
        with open(
                f"result/{self.module_name}", 'w', encoding='utf-8'
        ) as source_file:
            source_file.write("\n\n".join(self.instructions))


class PythonVisitor(BaseModuleVisitor):
    def __init__(self, module_name: str = None):
        if not module_name:
            module_name = '__main__.py'
        self.module_name = module_name

    def save_result_source(self, saver: PythonModuleSaver = None):
        saver: PythonModuleSaver = PythonModuleSaver(
            module_name=self.module_name,
            instructions=self._BaseModuleVisitor__instructions
        )
        saver.save()

    def visit_Module(self, node: ast.Module, level):
        return str(node.__module__)

    def visit_Constant(self, node, level):
        value = node.value
        type_name = const_node_type_names.get(type(value))
        if type_name is None:
            for cls, name in const_node_type_names.items():
                if isinstance(value, cls):
                    type_name = name
                    break
        if type_name is not None:
            method = 'visit_' + type_name
            try:
                visitor = getattr(self, method)
            except AttributeError:
                pass
            else:
                import warnings
                warnings.warn(f"{method} is deprecated; add visit_Constant",
                              DeprecationWarning, 2)
                return visitor(node)
        return self.generic_visit(node, level)

    def visit_FunctionDef(self, node: ast.FunctionDef, level: int = 0):
        """
        name
        args
        body
        decorator_list
        returns
        type_comment
        """

        # parsing decorators list
        decorators_formatted_str = None

        def format_decorators():
            return f"{get_tab(self.TAB, level)}\n".join(decorators)

        decorators, level = parse_decorators_list(node, level)
        if decorators:
            decorators_formatted_str = format_decorators()

        # parsing args
        result_args = parse_func_args(self, node)

        # parsing body
        body, level = parse_func_body(self, node, level)

        result = f"{get_tab(self.TAB, level)}" \
                 f"def {node.name}({result_args}):\n{body}"

        if decorators_formatted_str:
            result = f"{decorators_formatted_str}\n{result}"

        return result
