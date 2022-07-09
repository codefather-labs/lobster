import ast
import os
from types import NoneType
from typing import Optional, Union, List

from lobster.visitors.base import BaseModuleVisitor
from lobster.visitors.python.utils import get_tab


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
            module_name = 'main.py'
        self.module_name = module_name

    def save_result_source(self, saver: PythonModuleSaver = None):
        saver: PythonModuleSaver = PythonModuleSaver(
            module_name=self.module_name,
            instructions=self._BaseModuleVisitor__instructions
        )
        saver.save()

    def visit_Module(self, node: ast.Module, level):
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef, level: int = 0):
        """
        name
        args
        body
        decorator_list
        returns
        type_comment
        """

        # parsing args
        args: ast.arguments = node.args
        result_args = []
        for arg in reversed(args.args):
            arg: ast.arg
            name: str = arg.arg

            annotation: Optional[str] = None
            if arg.annotation:
                annotation: str = arg.annotation.id

            default_value = ''

            if args.defaults:
                # TODO remake for visit_Constant
                if isinstance(args.defaults[-1], ast.Constant):
                    default_value = args.defaults.pop(-1).value

                # TODO remake for visit_List
                elif isinstance(args.defaults[-1], ast.List):
                    i: ast.List = args.defaults.pop(-1)
                    default_value = list()

                # TODO remake for visit_Dict
                elif isinstance(args.defaults[-1], ast.Dict):
                    i: ast.Dict = args.defaults.pop(-1)
                    default_value = dict()

                # TODO remake for visit_Tuple
                elif isinstance(args.defaults[-1], ast.Tuple):
                    i: ast.Tuple = args.defaults.pop(-1)
                    default_value = tuple()

                # TODO remake for visit_Set
                elif isinstance(args.defaults[-1], ast.Set):
                    i: ast.Set = args.defaults.pop(-1)
                    default_value = set()

                # TODO remake for visit_FunctionDef
                elif isinstance(args.defaults[-1], ast.FunctionDef):
                    i: ast.FunctionDef = args.defaults.pop(-1)
                    # default_value = render_python_func(i)

                elif isinstance(args.defaults[-1], ast.AsyncFunctionDef):
                    ...

            # # TODO remake for visit_DefaultValue
            if default_value:
                if isinstance(default_value, str):
                    result_args.append(f'{name}: {annotation} = "{default_value}"')
                else:
                    result_args.append(f'{name}: {annotation} = {default_value}')

            elif isinstance(default_value, NoneType):
                result_args.append(f"{name}: {annotation} = None")

            elif isinstance(default_value, list):
                result_args.append("%s: %s = []" % (name, annotation))

            elif isinstance(default_value, dict):
                result_args.append("%s: %s = {}" % (name, annotation))

            elif isinstance(default_value, tuple):
                result_args.append("%s: %s = ()" % (name, annotation))

            else:
                result_args.append(f"{name}: {annotation}")

        result_args = ", ".join(list(reversed(result_args)))

        # parsing body
        body = ""
        for element in node.body:
            level = 1 if not level else level

            element: Union[ast.Expr, ast.Pass, ast.FunctionDef]

            # TODO remake for visit_Expr
            if isinstance(element, ast.Expr):
                element: ast.Expr

                # TODO remake for visit_Ellipsis
                if isinstance(element.value, ast.Ellipsis):
                    element: ast.Ellipsis
                    body = "%s..." % get_tab(self.TAB, level, inner=True)

            # TODO remake for visit_Pass
            elif isinstance(element, ast.Pass):
                element: ast.Pass
                body += "%spass" % get_tab(self.TAB, level, inner=True)

            # TODO remake for visit_FunctionDef
            elif isinstance(element, ast.FunctionDef):
                body += self.visit_FunctionDef(element, level + 2)

            # TODO remake for visit_Assign
            # elif isinstance(element, ast.Assign):
            #     ...
            #
            # TODO remake for visit_AsyncFunctionDef
            # elif isinstance(element, ast.AsyncFunctionDef):
            #     ...
            #
            # TODO remake for visit_For
            # elif isinstance(element, ast.For):
            #     ...
            #
            # TODO remake for visit_While
            # elif isinstance(element, ast.While):
            #     ...
            #
            # TODO remake for visit_Import
            # elif isinstance(element, ast.Import):
            #     ...
            #
            # TODO remake for visit_ImportFrom
            # elif isinstance(element, ast.ImportFrom):
            #     ...

            # expr_value: ast.Constant = expr.value
            # el: ast.Ellipsis = expr_value.value
            # print(el)
            body += "\n"

        level = 0 if not level else level - 2
        return f"{get_tab(self.TAB, level)}" \
               f"def {node.name}({result_args}):\n{body}"
