import ast
import os.path
from io import BufferedReader, FileIO

from visitors.python import PythonVisitor


# https://greentreesnakes.readthedocs.io/en/latest/tofrom.html
# https://python-ast-explorer.com

def main():
    import argparse

    parser = argparse.ArgumentParser(prog='python -m ast')
    parser.add_argument('infile', type=argparse.FileType(mode='rb'), nargs='?',
                        default='-',
                        help='the file to parse; defaults to stdin')
    parser.add_argument('-m', '--mode', default='exec',
                        choices=('exec', 'single', 'eval', 'func_type'),
                        help='specify what kind of code must be parsed')
    parser.add_argument('--no-type-comments', default=True, action='store_false',
                        help="don't add information about type comments")
    parser.add_argument('-a', '--include-attributes', action='store_true',
                        help='include attributes such as line numbers and '
                             'column offsets')
    parser.add_argument('-i', '--indent', type=int, default=4,
                        help='indentation of nodes (number of spaces)')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    args = parser.parse_args()

    with args.infile as infile:
        source = infile.read()

    visitor = PythonVisitor(
        module=os.path.abspath(infile.name),
        result_dir_path=args.output,
        rebuild_imports_tree=True
    )

    tree: ast.Module = \
        visitor.parse(source, args.infile.name, args.mode,
                      type_comments=args.no_type_comments)

    visitor.transpile(
        tree,
        indent=args.indent,
    )
    visitor.save_result_source()


if __name__ == '__main__':
    main()
