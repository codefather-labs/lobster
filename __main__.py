import ast

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
    args = parser.parse_args()

    with args.infile as infile:
        source = infile.read()

    visitor = PythonVisitor(
        module_name=str(infile.name).split("/")[-1]
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
