import sys
import ast

from lobster.visitors.c import CVisitor


def add_imports(node):
    """Provide context of imports Module"""
    return ImportTransformer().visit(node)


def is_void_function(fun):
    finder = ReturnFinder()
    finder.visit(fun)
    return not finder.returns


if sys.version_info[0] >= 3:
    def get_id(var):
        if isinstance(var, ast.alias):
            return var.name
        elif isinstance(var, ast.Name):
            return var.id
        elif isinstance(var, ast.arg):
            return var.arg
else:
    def get_id(var):
        if isinstance(var, ast.alias):
            return var.name
        elif isinstance(var, ast.Name):
            return var.id


def is_mutable(scopes, target):
    for scope in scopes:
        if isinstance(scope, ast.FunctionDef):
            if target in scope.mutable_vars:
                return True
    return False


class ReturnFinder(ast.NodeVisitor):
    returns = False

    def visit_Return(self, node):
        if node.value != None:
            self.returns = True


class FunctionTransformer(ast.NodeTransformer):
    """Tracks defined functions in scope"""

    def visit_Module(self, node):
        node.defined_functions = []
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        node.defined_functions = []
        node.scopes[-2].defined_functions.append(node)
        self.generic_visit(node)
        return node

    def visit_ImportFrom(self, node):
        for name in node.names:
            node.scopes[-1].defined_functions.append(name)
        return node


class CalledWithTransformer(ast.NodeTransformer):
    """
    Tracks whether variables or functions get
    used as arguments of other functions
    """

    def visit_Assign(self, node):
        for target in node.targets:
            target.called_with = []
        return node

    def visit_FunctionDef(self, node):
        node.called_with = []
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        for arg in node.args:
            if isinstance(arg, ast.Name):
                var = node.scopes.find(arg.id)
                var.called_with.append(node)
        self.generic_visit(node)
        return node


class AttributeCallTransformer(ast.NodeTransformer):
    """Tracks attribute function calls on variables"""

    def visit_Assign(self, node):
        for target in node.targets:
            target.calls = []
        return node

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            var = node.scopes.find(node.func.value.id)
            var.calls.append(node)
        return node


class ImportTransformer(ast.NodeTransformer):
    """Adds imports to scope block"""

    def visit_ImportFrom(self, node):
        for name in node.names:
            name.imported_from = node
            scope = name.scopes[-1]
            if hasattr(scope, "imports"):
                scope.imports.append(name)
        return node

    def visit_Module(self, node):
        node.imports = []
        self.generic_visit(node)
        return node


def decltype(node):
    """Create C++ decltype statement"""
    # if is_list(node):
    #     return "std::vector<decltype({0})>".format(value_type(node))
    # else:
    #     return "decltype({0})".format(value_type(node))


def is_builtin_import(name):
    return name == "sys" or name == "math"


# is it slow? is it correct?
def is_class_or_module(name, scopes):
    for scope in scopes:
        for entry in scope.body:
            if isinstance(entry, ast.ClassDef):
                if entry.name == name:
                    return True
        if hasattr(scope, "imports"):
            for entry in scope.imports:
                if entry.name == name:
                    return True
    return False


def is_list(node):
    """Check if a node was assigned as a list"""
    if isinstance(node, ast.List):
        return True
    elif isinstance(node, ast.Assign):
        return is_list(node.value)
    elif isinstance(node, ast.Name):
        var = node.scopes.find(get_id(node))
        return (hasattr(var, "assigned_from") and not
        isinstance(var.assigned_from, ast.FunctionDef) and not
                isinstance(var.assigned_from, ast.For) and
                is_list(var.assigned_from.value))
    else:
        return False


def value_expr(node):
    """
    Follow all assignments down the rabbit hole in order to find
    the value expression of a name.
    The boundary is set to the current scope.
    """
    return ValueExpressionVisitor().visit(node)


def value_type(node):
    """
    Guess the value type of a node based on the manipulations or assignments
    in the current scope.
    Special case: If node is a container like a list the value type inside the
    list is returned not the list type itself.
    """
    return ValueTypeVisitor().visit(node)


class ValueExpressionVisitor(ast.NodeVisitor):
    def visit_Num(self, node):
        return str(node.n)

    def visit_Str(self, node):
        return node.s

    def visit_Name(self, node):
        var = node.scopes.find(get_id(node))

        if not var:  # TODO why no scopes found for node id?
            return get_id(node)

        # if isinstance(var, object):
        #     return "o_b_j_e_c_t"

        if isinstance(var.assigned_from, ast.For):
            it = var.assigned_from.iter
            return "std::declval<typename decltype({0})::value_type>()".format(
                self.visit(it))
        elif isinstance(var.assigned_from, ast.FunctionDef):
            return get_id(var)
        else:
            return self.visit(var.assigned_from.value)

    def visit_Call(self, node):
        arg_strings = [self.visit(arg) for arg in node.args]
        params = ",".join(arg_strings)
        return "{0}({1})".format(self.visit(node.func), params)

    def visit_Assign(self, node):
        return self.visit(node.value)

    def visit_BinOp(self, node):
        return "{0} {1} {2}".format(self.visit(node.left),
                                    CVisitor().visit(node.op),
                                    self.visit(node.right))


class ValueTypeVisitor(ast.NodeVisitor):
    def visit_Num(self, node):
        return value_expr(node)

    def visit_Str(self, node):
        return value_expr(node)

    def visit_Name(self, node):
        if node.id == 'True' or node.id == 'False':
            return CVisitor().visit(node)

        var = node.scopes.find(node.id)
        if defined_before(var, node):
            return node.id
        else:
            return self.visit(var.assigned_from.value)

    def visit_NameConstant(self, node):
        return CVisitor().visit(node)

    def visit_Call(self, node):
        params = ",".join([self.visit(arg) for arg in node.args])
        return "{0}({1})".format(node.func.id, params)

    def visit_Assign(self, node):
        if isinstance(node.value, ast.List):
            if len(node.value.elts) > 0:
                val = node.value.elts[0]
                return self.visit(val)
            else:
                target = node.targets[0]
                var = node.scopes.find(target.id)
                first_added_value = var.calls[0].args[0]
                return value_expr(first_added_value)
        else:
            return self.visit(node.value)


def defined_before(node1, node2):
    """Check if node a has been defined before an other node b"""
    return node1.lineno < node2.lineno


def is_list_assignment(node):
    return (isinstance(node.value, ast.List) and
            isinstance(node.targets[0].ctx, ast.Store))


def is_list_addition(node):
    """Check if operation is adding something to a list"""
    list_operations = ["append", "extend", "insert"]
    return (isinstance(node.func.ctx, ast.Load) and
            hasattr(node.func, "value") and
            isinstance(node.func.value, ast.Name) and
            node.func.attr in list_operations)


def is_recursive(fun):
    finder = RecursionFinder()
    finder.visit(fun)
    return finder.recursive


class RecursionFinder(ast.NodeVisitor):
    function_name = None
    recursive = False

    def visit_FunctionDef(self, node):
        self.function_name = node.name
        self.generic_visit(node)

    def visit_Call(self, node):
        self.recursive = (isinstance(node.func, ast.Name) and
                          node.func.id == self.function_name)
        self.generic_visit(node)


# TODO better type infering based on variable init
def type_by_initialization(init_str):
    if init_str == "vec![]":
        return "Vec<_>"
    elif init_str == "HashMap::new()":
        return "HashMap<_,_>"
    elif init_str == "None":
        return "Option<_>"
    elif init_str == "true" or init_str == "false":
        return "bool"
    else:
        return None


class DeclarationExtractor(ast.NodeVisitor):
    def __init__(self, transpiler):
        self.transpiler = transpiler
        self.already_annotated = {}
        self.class_assignments = {}
        self.typed_vars = {}

    def get_declarations(self):
        typed_members = self.already_annotated
        for member, var in self.class_assignments.items():
            if member in self.already_annotated:
                continue

            if var in self.typed_vars:
                typed_members[member] = self.typed_vars[var]

        for member, value in self.class_assignments.items():
            if member not in typed_members:
                typed_members[member] = type_by_initialization(value)

        return typed_members

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_FunctionDef(self, node):
        types, names = self.transpiler.visit(node.args)

        for i in range(len(names)):
            typename = types[i]
            if typename and typename != "T":
                if names[i] not in self.typed_vars:
                    self.typed_vars[names[i]] = typename

        for n in node.body:
            self.visit(n)

    def visit_AnnAssign(self, node):
        target = node.target
        if self.is_member(target):
            type_str = self.transpiler.visit(node.annotation)
            if target.attr not in self.already_annotated:
                self.already_annotated[target.attr] = type_str

    def visit_Assign(self, node):
        target = node.targets[0]
        if self.is_member(target):
            # target = self.transpiler.visit(target)
            value = self.transpiler.visit(node.value)
            if target.attr not in self.class_assignments:
                self.class_assignments[target.attr] = value

    def is_member(self, node):
        if hasattr(node, "value"):
            if self.transpiler.visit(node.value) == "self":
                return True
        return False
