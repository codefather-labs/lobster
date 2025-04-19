import ast
import os
from typing import List

from visitors.base import BaseModuleVisitor
from visitors.python.import_rebuilder import ImportTreeRebuilder
from visitors.python.utils import (
    get_tab,
    parse_func_body,
    parse_func_args,
    remove_indent_level,
    parse_decorators_list,
    const_node_type_names
)


def add_indent_level(level):
    return level + 1


class PythonModuleSaver:

    def __init__(self,
                 module_path: str,
                 source_base_dir: str,
                 result_dir_name: str,
                 instructions: List[str]):
        self.module = module_path
        self.source_base_dir = source_base_dir
        self.result_dir_path = os.path.abspath(result_dir_name)
        self.instructions: List[str] = instructions

    def save(self):
        os.system(f"mkdir result")
        rel_path = os.path.relpath(self.module, start=self.source_base_dir)
        target_path = os.path.join(self.result_dir_path, rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        print(f"Saving results to {target_path}")
        with open(target_path, 'w', encoding='utf-8') as source_file:
            try:
                source_file.write("\n\n".join(self.instructions))
            except TypeError as e:
                exit(e)


class PythonVisitor(BaseModuleVisitor):
    def __init__(self, module: str, result_dir_path: str = None, rebuild_imports_tree: bool = False):
        module_name = module.split("/")[-1]
        self.source_base_dir = os.path.abspath("sources")
        self.module = module
        self.module_name = module_name
        self.source_module_dir = "/".join(module.split("/")[:-1])
        self.result_dir_name = 'result' \
            if not result_dir_path else result_dir_path
        self.rebuild_imports_tree = rebuild_imports_tree
        self.import_tree_rebuilder = ImportTreeRebuilder(self.result_dir_name, self.__class__, self.source_base_dir)

    def save_result_source(self, saver: PythonModuleSaver = None):
        saver: PythonModuleSaver = PythonModuleSaver(
            module_path=self.module,
            source_base_dir=self.source_module_dir,
            result_dir_name=self.result_dir_name,
            instructions=self._BaseModuleVisitor__instructions
        )
        saver.save()

    def visit_Module(self, node: ast.Module, level: int = 0):
        lines = []
        for stmt in node.body:
            result = self.visit(stmt, level)
            if result:
                lines.append(result)
        return "\n\n".join(lines)

    def visit_Ellipsis(self, node: ast.Ellipsis, level: int):
        return f"{get_tab(self.TAB, level)}..."

    def visit_FunctionDef(self, node: ast.FunctionDef, level: int = 0):
        decorators, _ = parse_decorators_list(node, level)
        decorators_str = "\n".join([f"{get_tab(self.TAB, level)}{d}" for d in decorators])

        args_str = parse_func_args(self, node, level)
        returns = f" -> {self.visit(node.returns, level)}" if node.returns else ""

        body_indent = add_indent_level(level)
        body_str, _ = parse_func_body(self, node, body_indent)

        func_def_line = f"{get_tab(self.TAB, level)}def {node.name}({args_str}){returns}:"
        full_body = f"{func_def_line}\n{body_str}"

        return f"{decorators_str}\n{full_body}" if decorators else full_body

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef, level: int = 0):
        decorators, _ = parse_decorators_list(node, level)
        decorators_str = "\n".join([f"{get_tab(self.TAB, level)}{d}" for d in decorators])

        args_str = parse_func_args(self, node, level)
        returns = f" -> {self.visit(node.returns, level)}" if node.returns else ""

        body_indent = add_indent_level(level)
        body_str, _ = parse_func_body(self, node, body_indent)

        func_def_line = f"{get_tab(self.TAB, level)}async def {node.name}({args_str}){returns}:"
        full_body = f"{func_def_line}\n{body_str}"

        return f"{decorators_str}\n{full_body}" if decorators else full_body

    def visit_ClassDef(self, node: ast.ClassDef, level: int = 0):
        bases = ", ".join([self.visit(base, level) for base in node.bases])
        class_header = f"{get_tab(self.TAB, level)}class {node.name}({bases}):" if bases else f"{get_tab(self.TAB, level)}class {node.name}:"

        body_level = add_indent_level(level)
        body = "\n".join([self.visit(stmt, body_level) for stmt in node.body])
        if not body.strip():
            body = f"{get_tab(self.TAB, body_level)}pass"

        return f"{class_header}\n{body}"

    def visit_Expr(self, node: ast.Expr, level: int):
        value = node.value
        if isinstance(value, ast.Constant) and value.value is Ellipsis:
            return f"{get_tab(self.TAB, level)}..."
        return f"{get_tab(self.TAB, level)}{self.visit(value, level)}"

    def visit_Call(self, node: ast.Call, level: int):
        func = self.visit(node.func, level)
        args = ", ".join([self.visit(arg, level) for arg in node.args])
        return f"{func}({args})"

    def visit_Name(self, node: ast.Name, level: int):
        return node.id

    def visit_Constant(self, node: ast.Constant, level: int):
        return repr(node.value)

    def visit_Return(self, node: ast.Return, level: int):
        value = self.visit(node.value, level) if node.value else ""
        return f"{get_tab(self.TAB, level)}return {value}"

    def visit_Assign(self, node: ast.Assign, level: int):
        targets = " = ".join([self.visit(t, level) for t in node.targets])
        value = self.visit(node.value, level)
        return f"{get_tab(self.TAB, level)}{targets} = {value}"

    def visit_Import(self, node: ast.Import, level: int):
        if self.rebuild_imports_tree:
            return self.import_tree_rebuilder.rewrite_import(node, level)
        names = ", ".join([alias.name for alias in node.names])
        return f"{get_tab(self.TAB, level)}import {names}"

    def visit_ImportFrom(self, node: ast.ImportFrom, level: int):
        if self.rebuild_imports_tree and node.module:
            return self.import_tree_rebuilder.rewrite_import_from(node, level)
        module = node.module or ""
        names = ", ".join([alias.name for alias in node.names])
        return f"{get_tab(self.TAB, level)}from {module} import {names}"

    def visit_If(self, node: ast.If, level: int):
        test = self.visit(node.test, level)
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        result = f"{get_tab(self.TAB, level)}if {test}:\n{body}"
        if node.orelse:
            orelse = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.orelse])
            result += f"\n{get_tab(self.TAB, level)}else:\n{orelse}"
        return result

    def visit_While(self, node: ast.While, level: int):
        test = self.visit(node.test, level)
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}while {test}:\n{body}"

    def visit_For(self, node: ast.For, level: int):
        target = self.visit(node.target, level)
        iter_ = self.visit(node.iter, level)
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}for {target} in {iter_}:\n{body}"

    def visit_Break(self, node: ast.Break, level: int):
        return f"{get_tab(self.TAB, level)}break"

    def visit_Continue(self, node: ast.Continue, level: int):
        return f"{get_tab(self.TAB, level)}continue"

    def visit_Pass(self, node: ast.Pass, level: int):
        return f"{get_tab(self.TAB, level)}pass"

    def visit_Try(self, node: ast.Try, level: int):
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        result = f"{get_tab(self.TAB, level)}try:\n{body}"
        for handler in node.handlers:
            result += f"\n{self.visit(handler, level)}"
        if node.orelse:
            orelse = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.orelse])
            result += f"\n{get_tab(self.TAB, level)}else:\n{orelse}"
        if node.finalbody:
            finalbody = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.finalbody])
            result += f"\n{get_tab(self.TAB, level)}finally:\n{finalbody}"
        return result

    def visit_ExceptHandler(self, node: ast.ExceptHandler, level: int):
        type_ = self.visit(node.type, level) if node.type else ""
        name = f" as {node.name}" if node.name else ""
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}except {type_}{name}:\n{body}"

    def visit_With(self, node: ast.With, level: int):
        items = ", ".join([
            f"{self.visit(item.context_expr, level)} as {self.visit(item.optional_vars, level)}"
            if item.optional_vars else self.visit(item.context_expr, level)
            for item in node.items
        ])
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}with {items}:\n{body}"

    def visit_BinOp(self, node: ast.BinOp, level: int):
        left = self.visit(node.left, level)
        op = self.visit(node.op, level)
        right = self.visit(node.right, level)
        return f"({left} {op} {right})"

    def visit_BoolOp(self, node: ast.BoolOp, level: int):
        op = self.visit(node.op, level)
        values = [self.visit(value, level) for value in node.values]
        return f" {op} ".join(values)

    def visit_Compare(self, node: ast.Compare, level: int):
        left = self.visit(node.left, level)
        comparisons = " ".join(
            f"{self.visit(op, level)} {self.visit(comp, level)}"
            for op, comp in zip(node.ops, node.comparators)
        )
        return f"{left} {comparisons}"

    def visit_Subscript(self, node: ast.Subscript, level: int):
        value = self.visit(node.value, level)
        slice_ = self.visit(node.slice, level)
        return f"{value}[{slice_}]"

    def visit_Attribute(self, node: ast.Attribute, level: int):
        value = self.visit(node.value, level)
        return f"{value}.{node.attr}"

    def visit_Lambda(self, node: ast.Lambda, level: int):
        args = ", ".join([arg.arg for arg in node.args.args])
        body = self.visit(node.body, level)
        return f"lambda {args}: {body}"

    def visit_ListComp(self, node: ast.ListComp, level: int):
        elt = self.visit(node.elt, level)
        gens = []
        for gen in node.generators:
            target = self.visit(gen.target, level)
            iter_ = self.visit(gen.iter, level)
            conds = " ".join([f"if {self.visit(if_, level)}" for if_ in gen.ifs])
            gens.append(f"for {target} in {iter_} {conds}".strip())
        return f"[{elt} {' '.join(gens)}]"

    def visit_Add(self, node, level):
        return "+"

    def visit_And(self, node, level):
        return "and"

    def visit_Load(self, node, level):
        return ""

    def visit_Store(self, node, level):
        return ""

    def visit_Del(self, node, level):
        return "del"

    def visit_AugLoad(self, node, level):
        return ""

    def visit_AugStore(self, node, level):
        return ""

    def visit_AugAssign(self, node: ast.AugAssign, level: int):
        target = self.visit(node.target, level)
        op = self.visit(node.op, level)
        value = self.visit(node.value, level)
        return f"{get_tab(self.TAB, level)}{target} {op}= {value}"

    def visit_AnnAssign(self, node: ast.AnnAssign, level: int):
        target = self.visit(node.target, level)
        annotation = self.visit(node.annotation, level)
        value = f" = {self.visit(node.value, level)}" if node.value else ""
        return f"{get_tab(self.TAB, level)}{target}: {annotation}{value}"

    def visit_Await(self, node: ast.Await, level: int):
        value = self.visit(node.value, level)
        return f"await {value}"

    def visit_Assert(self, node: ast.Assert, level: int):
        test = self.visit(node.test, level)
        msg = f", {self.visit(node.msg, level)}" if node.msg else ""
        return f"{get_tab(self.TAB, level)}assert {test}{msg}"

    def visit_AsyncFor(self, node: ast.AsyncFor, level: int):
        target = self.visit(node.target, level)
        iter_ = self.visit(node.iter, level)
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}async for {target} in {iter_}:{body}"

    def visit_AsyncWith(self, node: ast.AsyncWith, level: int):
        items = ", ".join([
            f"{self.visit(item.context_expr, level)} as {self.visit(item.optional_vars, level)}"
            if item.optional_vars else self.visit(item.context_expr, level)
            for item in node.items
        ])
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}async with {items}:{body}"

    def visit_DictComp(self, node: ast.DictComp, level: int):
        key = self.visit(node.key, level)
        value = self.visit(node.value, level)
        gens = " ".join(
            [f"for {self.visit(gen.target, level)} in {self.visit(gen.iter, level)}" for gen in node.generators])
        return f"{{{key}: {value} {gens}}}"

    def visit_SetComp(self, node: ast.SetComp, level: int):
        elt = self.visit(node.elt, level)
        gens = " ".join(
            [f"for {self.visit(gen.target, level)} in {self.visit(gen.iter, level)}" for gen in node.generators])
        return f"{{{elt} {gens}}}"

    def visit_GeneratorExp(self, node: ast.GeneratorExp, level: int):
        elt = self.visit(node.elt, level)
        gens = " ".join(
            [f"for {self.visit(gen.target, level)} in {self.visit(gen.iter, level)}" for gen in node.generators])
        return f"({elt} {gens})"

    def visit_FormattedValue(self, node: ast.FormattedValue, level: int):
        value = self.visit(node.value, level)
        return f"{{{value}}}"

    def visit_JoinedStr(self, node: ast.JoinedStr, level: int):
        values = "".join([self.visit(v, level) for v in node.values])
        return f"f\"{values}\""

    def visit_Sub(self, node, level):
        return "-"

    def visit_Mult(self, node, level):
        return "*"

    def visit_Div(self, node, level):
        return "/"

    def visit_FloorDiv(self, node, level):
        return "//"

    def visit_Mod(self, node, level):
        return "%"

    def visit_Pow(self, node, level):
        return "**"

    def visit_LShift(self, node, level):
        return "<<"

    def visit_RShift(self, node, level):
        return ">>"

    def visit_BitAnd(self, node, level):
        return "&"

    def visit_BitOr(self, node, level):
        return "|"

    def visit_BitXor(self, node, level):
        return "^"

    def visit_MatMult(self, node, level):
        return "@"

    def visit_Eq(self, node, level):
        return "=="

    def visit_NotEq(self, node, level):
        return "!="

    def visit_Lt(self, node, level):
        return "<"

    def visit_LtE(self, node, level):
        return "<="

    def visit_Gt(self, node, level):
        return ">"

    def visit_GtE(self, node, level):
        return ">="

    def visit_Is(self, node, level):
        return "is"

    def visit_IsNot(self, node, level):
        return "is not"

    def visit_In(self, node, level):
        return "in"

    def visit_NotIn(self, node, level):
        return "not in"

    def visit_IfExp(self, node: ast.IfExp, level: int):
        body = self.visit(node.body, level)
        test = self.visit(node.test, level)
        orelse = self.visit(node.orelse, level)
        return f"{body} if {test} else {orelse}"

    def visit_NamedExpr(self, node: ast.NamedExpr, level: int):
        target = self.visit(node.target, level)
        value = self.visit(node.value, level)
        return f"({target} := {value})"

    def visit_Starred(self, node: ast.Starred, level: int):
        value = self.visit(node.value, level)
        return f"*{value}"

    def visit_Yield(self, node: ast.Yield, level: int):
        value = self.visit(node.value, level) if node.value else ""
        return f"yield {value}"

    def visit_YieldFrom(self, node: ast.YieldFrom, level: int):
        value = self.visit(node.value, level)
        return f"yield from {value}"

    def visit_Raise(self, node: ast.Raise, level: int):
        exc = self.visit(node.exc, level) if node.exc else ""
        cause = f" from {self.visit(node.cause, level)}" if node.cause else ""
        return f"{get_tab(self.TAB, level)}raise {exc}{cause}"

    def visit_Global(self, node: ast.Global, level: int):
        names = ", ".join(node.names)
        return f"{get_tab(self.TAB, level)}global {names}"

    def visit_Nonlocal(self, node: ast.Nonlocal, level: int):
        names = ", ".join(node.names)
        return f"{get_tab(self.TAB, level)}nonlocal {names}"

    def visit_List(self, node: ast.List, level: int):
        elts = ", ".join([self.visit(e, level) for e in node.elts])
        return f"[{elts}]"

    def visit_Tuple(self, node: ast.Tuple, level: int):
        elts = ", ".join([self.visit(e, level) for e in node.elts])
        return f"({elts})"

    def visit_Dict(self, node: ast.Dict, level: int):
        items = ", ".join([
            f"{self.visit(k, level)}: {self.visit(v, level)}"
            for k, v in zip(node.keys, node.values)
        ])
        return f"{{{items}}}"

    def visit_UnaryOp(self, node: ast.UnaryOp, level: int):
        op = self.visit(node.op, level)
        operand = self.visit(node.operand, level)
        return f"{op}{operand}"

    def visit_UAdd(self, node, level):
        return "+"

    def visit_USub(self, node, level):
        return "-"

    def visit_Not(self, node, level):
        return "not "

    def visit_Invert(self, node, level):
        return "~"

    def visit_Match(self, node: ast.Match, level: int):
        subject = self.visit(node.subject, level)
        cases = "\n".join([self.visit(c, level) for c in node.cases])
        return f"{get_tab(self.TAB, level)}match {subject}:{cases}"

    def visit_match_case(self, node: ast.match_case, level: int):
        pattern = self.visit(node.pattern, level)
        guard = f" if {self.visit(node.guard, level)}" if node.guard else ""
        body = "\n".join([self.visit(stmt, add_indent_level(level)) for stmt in node.body])
        return f"{get_tab(self.TAB, level)}case {pattern}{guard}:{body}"

    def visit_MatchValue(self, node: ast.MatchValue, level: int):
        return self.visit(node.value, level)

    def visit_MatchOr(self, node: ast.MatchOr, level: int):
        return " | ".join([self.visit(p, level) for p in node.patterns])

    def visit_MatchAs(self, node: ast.MatchAs, level: int):
        if node.pattern:
            pattern = self.visit(node.pattern, level)
            name = node.name or "_"
            return f"{pattern} as {name}"
        return node.name or "_"

    def visit_MatchStar(self, node: ast.MatchStar, level: int):
        return f"*{node.name or '_'}"

    def visit_MatchSingleton(self, node: ast.MatchSingleton, level: int):
        return repr(node.value)

    def visit_MatchClass(self, node: ast.MatchClass, level: int):
        cls = self.visit(node.cls, level)
        patterns = ", ".join([self.visit(p, level) for p in node.patterns])
        return f"{cls}({patterns})"

    def visit_MatchMapping(self, node: ast.MatchMapping, level: int):
        keys = ", ".join([self.visit(k, level) for k in node.keys])
        patterns = ", ".join([self.visit(p, level) for p in node.patterns])
        return f"{{{keys}: {patterns}}}"

    def visit_MatchSequence(self, node: ast.MatchSequence, level: int):
        return f"[{', '.join(self.visit(p, level) for p in node.patterns)}]"

    def visit_Set(self, node: ast.Set, level: int):
        elts = ", ".join([self.visit(e, level) for e in node.elts])
        return f"{{{elts}}}"

    def visit_arguments(self, node: ast.arguments, level: int):
        args = [self.visit(arg, level) for arg in node.args]
        return ", ".join(args)

    def visit_arg(self, node: ast.arg, level: int):
        annotation = f": {self.visit(node.annotation, level)}" if node.annotation else ""
        return f"{node.arg}{annotation}"

    def visit_keyword(self, node: ast.keyword, level: int):
        value = self.visit(node.value, level)
        if node.arg is None:  # **kwargs
            return f"**{value}"
        return f"{node.arg}={value}"

    def visit_alias(self, node: ast.alias, level: int):
        return f"{node.name} as {node.asname}" if node.asname else node.name

    def visit_comprehension(self, node: ast.comprehension, level: int):
        target = self.visit(node.target, level)
        iter_ = self.visit(node.iter, level)
        ifs = " ".join([f"if {self.visit(cond, level)}" for cond in node.ifs])
        return f"for {target} in {iter_} {ifs}"

    def visit_expr(self, node: ast.expr, level: int):
        return self.visit(node, level)

    def visit_stmt(self, node: ast.stmt, level: int):
        return self.visit(node, level)

    def visit_expr_context(self, node: ast.expr_context, level: int):
        return ""

    def visit_slice(self, node: ast.slice, level: int):
        return self.visit(node, level)

    def visit_mod(self, node: ast.mod, level: int):
        return self.visit(node, level)

    def visit_operator(self, node: ast.operator, level: int):
        return self.visit(node, level)

    def visit_unaryop(self, node: ast.unaryop, level: int):
        return self.visit(node, level)

    def visit_cmpop(self, node: ast.cmpop, level: int):
        return self.visit(node, level)

    def visit_boolop(self, node: ast.boolop, level: int):
        return self.visit(node, level)

    def visit_pattern(self, node: ast.pattern, level: int):
        return self.visit(node, level)

    def visit_withitem(self, node: ast.withitem, level: int):
        context_expr = self.visit(node.context_expr, level)
        if node.optional_vars:
            optional_vars = self.visit(node.optional_vars, level)
            return f"{context_expr} as {optional_vars}"
        return context_expr
