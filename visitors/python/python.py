import ast
import os
from typing import List, Union, Any
from visitors.base import BaseModuleVisitor
from visitors.python.utils import get_tab, parse_func_body, parse_func_args, remove_indent_level, parse_decorators_list, \
    const_node_type_names


class PythonModuleSaver:

    def __init__(self, module_name: str,
                 result_dir_name: str,
                 instructions: List[str]):
        self.module_name = module_name
        self.result_dir_path = os.path.abspath(result_dir_name)
        self.instructions: List[str] = instructions

    def save(self):
        os.system(f"mkdir result")
        with open(
                f"{self.result_dir_path}/{self.module_name}", 'w', encoding='utf-8'
        ) as source_file:
            try:
                source_file.write("\n\n".join(self.instructions))
            except TypeError as e:
                exit(e)


class PythonVisitor(BaseModuleVisitor):
    def __init__(self,
                 module: str,
                 result_dir_path: str = None,
                 rebuild_imports_tree: bool = False):

        module_name = module.split("/")[-1]
        self.module_name = module_name
        self.source_module_dir = "/".join(module.split("/")[:-1])
        self.result_dir_name = 'result' \
            if not result_dir_path else result_dir_path
        self.rebuild_imports_tree = rebuild_imports_tree

    def save_result_source(self, saver: PythonModuleSaver = None):
        saver: PythonModuleSaver = PythonModuleSaver(
            module_name=self.module_name,
            result_dir_name=self.result_dir_name,
            instructions=self._BaseModuleVisitor__instructions
        )
        saver.save()

    def visit_Module(self, node: ast.Module, level: int):
        return str(node.__module__)

    def visit_Import(self, node: ast.Import, level: int):
        ...

    def visit_ImportFrom(self, node: ast.ImportFrom, level: int):
        result_dir_name = node.module
        names = ", ".join([n.name for n in node.names])

        pattern = "from %s import %s"
        if self.rebuild_imports_tree:
            pattern = f"from {self.result_dir_name}.%s import %s"
            module_path = f'{os.path.abspath(self.result_dir_name)}/' \
                          f'{"/".join(result_dir_name.split("."))}'

            append_path = []
            for dir in result_dir_name.split("."):
                path_dir = os.path.join(os.path.abspath(self.result_dir_name),
                                        "/".join(append_path),
                                        dir)
                append_path.append(dir)

                if os.path.isdir(os.path.abspath("/".join(append_path))):
                    if not os.path.exists(path_dir):
                        os.mkdir(path_dir)

                    if not os.path.exists(f'{path_dir}/__init__.py'):
                        os.system(f'touch {path_dir}/__init__.py')
                else:
                    if not os.path.exists(f"{path_dir}.py"):
                        os.system(f'touch {path_dir}.py')

            # TODO ADD {names} VISIT MODULE CODE
        else:
            # TODO
            #  BUILD ALL NODES FOR CODE TREE INSIDE OF ONE SCRIPT FILE
            #  WITHOUT IMPORT SIGNATURES (making C-like code style)
            ...

        result = pattern % (
            result_dir_name, names
        )

        return result

    def visit_Expr(self, node: ast.Expr, level: int):
        value: Any = node.value
        match type(value):
            case ast.Call:
                value: ast.Call
                return self.visit_Call(value, level)

            case ast.Load:
                value: ast.Load
                return self.visit_Load(value, level)

            case ast.Name:
                value: ast.Name
                return self.visit_Name(value, level)

            case ast.keyword:
                value: ast.keyword
                return self.visit_keyword(value, level)

            case ast.Constant:
                value: ast.Constant
                return self.visit_Constant(value, level)

            case _:
                print(f"Unknown Expr: {value}")

    def visit_Call(self, node: ast.Call, level: int):
        func: ast.Name = node.func
        pattern = "%s(%s)"
        args = ""
        result = pattern % (
            func.id, args
        )
        print(result)

    def visit_Name(self, node: ast.Name, level: int):
        print(node)

    def visit_Load(self, node: ast.Load, level: int):
        print(node)

    def visit_keyword(self, node: ast.keyword, level: int):
        print(node)

    def visit_Constant(self, node: ast.Constant, level: int):
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
        declaring a function
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
