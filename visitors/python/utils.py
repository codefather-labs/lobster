import ast
from types import NoneType
from typing import Union, Optional

from visitors.base import BaseModuleVisitor

add_indent_level = lambda x: x + 1
remove_indent_level = lambda x: x - 1

const_node_type_names = {
    bool: 'NameConstant',  # should be before int
    type(None): 'NameConstant',
    int: 'Num',
    float: 'Num',
    complex: 'Num',
    str: 'Str',
    bytes: 'Bytes',
    type(...): 'Ellipsis',
}


def get_tab(tab: str, level: int, inner=False):
    calc_tab = tab * level
    return "{tabulation}".format(
        tabulation=calc_tab
    )


def get_constant_type(node: ast.Constant) -> type:
    value = node.value
    type_name = const_node_type_names.get(type(value))
    if type_name is None:
        for cls, name in const_node_type_names.items():
            if isinstance(value, cls):
                type_name = name
                break

    return value


def parse_decorators_list(node: ast.FunctionDef, level: int):
    result = []
    if node.decorator_list:

        for decorator in node.decorator_list:
            decorator: Union[ast.Call, ast.Name]
            if isinstance(decorator, ast.Name):
                decorator: ast.Name
                result_buf = f'@%s' % decorator.id
                result.append(result_buf)
                continue

            r_args = ""
            r_kwargs = {}

            args, kwargs = decorator.args, decorator.keywords
            wrapper: ast.Name = decorator.func
            wrapper_name = wrapper.id

            for arg in args:
                arg: Union[ast.Constant, str]

                arg_type = get_constant_type(arg)
                arg_literal = arg.value

                if isinstance(arg_type, str):
                    arg_literal = f'"{arg.value}"'
                    r_args += arg_literal

                else:
                    r_args = f"{r_args}, {arg_literal}"

            for kwarg in kwargs:
                kwarg: ast.keyword

                name = kwarg.arg
                constant: ast.Constant = kwarg.value
                r_kwargs.update({name: constant.value})

            r_kwargs = ", ".join([f"{k}={v}" for k, v in r_kwargs.items()])
            result_buf = f'@%s({r_args}, {r_kwargs})' % wrapper_name

            result.append(result_buf)

    return result, level


def parse_func_body(visitor: BaseModuleVisitor, node: ast.FunctionDef, level: int = 0):
    body = ""
    for element in node.body:

        element: Union[ast.Expr, ast.Pass, ast.FunctionDef]

        # TODO remake for visit_Expr
        if isinstance(element, ast.Expr):
            element: ast.Expr

            # TODO remake for visit_Ellipsis
            if isinstance(element.value, ast.Ellipsis):
                element: ast.Ellipsis
                body = "%s..." % get_tab(visitor.TAB, level, inner=True)

        # TODO remake for visit_Pass
        elif isinstance(element, ast.Pass):
            element: ast.Pass
            body += "%spass" % get_tab(visitor.TAB, level, inner=True)

        # TODO remake for visit_FunctionDef
        elif isinstance(element, ast.FunctionDef):
            deeper_indent_level = add_indent_level(level)
            body += visitor.visit_FunctionDef(
                element, deeper_indent_level
            )

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

    level = remove_indent_level(level)
    return body, level


def parse_func_args(visitor: BaseModuleVisitor, node: ast.FunctionDef):
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

        # TODO remake for visit_DefaultValue
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

    return ", ".join(list(reversed(result_args)))
