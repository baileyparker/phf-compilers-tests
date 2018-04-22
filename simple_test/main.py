"""Main entry point for the simple compiler test harness."""

from argparse import ArgumentParser, ArgumentTypeError, Namespace
from enum import Enum
from os import environ
from pathlib import Path
from shlex import quote as shell_quote
from sys import argv
from typing import Any, cast, List, Type
from unittest import defaultTestLoader, TestSuite, TextTestRunner
from warnings import warn


from simple_test.runner import Runner, BinaryNotFoundError, \
    BinaryNotExecutableError
from simple_test.test_case import TestCase
from simple_test.test_scanner import TestScanner
from simple_test.test_cst import TestCST
from simple_test.test_symbol_table import TestSymbolTable
from simple_test.test_ast import TestAST
from simple_test.test_interpreter import TestInterpreter


class Phase(Enum):
    """Enum representing the phases of the compiler that can be tested."""
    SCANNER = TestScanner
    CST = TestCST
    ST = TestSymbolTable
    AST = TestAST
    INTERPRETER = TestInterpreter

    def __call__(self, *args: Any, **kwargs: Any) -> TestCase:
        return cast(TestCase, self.value(*args, **kwargs))

    def __str__(self) -> str:
        return self.name.lower()  # pylint: disable=E1101


def main() -> None:
    """Main entry point for the simple compiler test harness."""

    if 'SC' in environ:
        cmd = "{} --sc {}".format(argv[0], shell_quote(environ['SC']))
        warn("The SC environment variable is deprecated. Use: {}".format(cmd),
             DeprecationWarning)

        argv[1:1] = ['--sc', environ['SC']]

    args = _get_args()

    with args.runner:
        test_runner = TextTestRunner(verbosity=args.verbosity)
        test_suite = TestSuite([p(name=method, **args.__dict__)
                                for p in args.phases
                                for method in _get_test_case_names(p)])

        test_runner.run(test_suite)


def _get_test_case_names(test_case: Type[TestCase]) -> List[str]:
    fake_case = test_case(name='runTest', runner=None)  # type: ignore
    return list(defaultTestLoader.getTestCaseNames(fake_case))  # type: ignore


def _get_args() -> Namespace:
    parser = ArgumentParser(description='a test harness for PHF\'s '
                                        'compilers course',
                            epilog='Made with love by Bailey Parker.\n\n'
                                   'Special thanks to test contributors: '
                                   'Nick Hale, Sam Beckley, '
                                   'Peter Lazorchak, Rachel Kinney, and '
                                   'Andrew Rojas')

    parser.add_argument('--sc', dest='runner', type=_make_runner,
                        default='./sc', help='path to the sc binary')

    parser.add_argument('--st-all-fives', action='store_const', const=True,
                        help='Expect all numeric constants to be 5 in the '
                             'symbol table tests (useful for ST assignment '
                             'before the AST, when constant folding is added)')

    parser.add_argument('--skip-cst-passes', action='store_const', const=True,
                        help='If you have implemented your Symbol Table and '
                             'AST assignments such that the symbol table and '
                             'AST parts still run for -c, then some of the '
                             'CST tests (which are syntactically but not '
                             'semantically valid) will fail. This flag skips '
                             'these potentially misleading tests.')

    # We are unable to use choices here due to a longstanding bug in the
    # interaction between type, choices, nargs='*', and default=[]:
    # https://bugs.python.org/issue9625
    parser.add_argument('phases', type=_parse_phase, nargs='*',
                        default=list(Phase), metavar=','.join(map(str, Phase)),
                        help='phases of the compiler to test (default: all)')

    parser.add_argument('-v', dest='verbosity', action='store_const', const=2,
                        default=1, help='verbose test output')

    return parser.parse_args()


def _make_runner(path: str) -> Runner:
    try:
        return Runner.create(Path(Path.cwd(), path))
    except BinaryNotFoundError as e:
        cmd = "{} --sc path/to/sc".format(argv[0])
        msg = "simple compiler does not exist: {} (try: {})" \
            .format(e.filename, cmd)

        raise ArgumentTypeError(msg)
    except BinaryNotExecutableError as e:
        cmd = "chmod +x {}".format(e.filename)
        msg = "simple compiler is not executable: {} (try: {})" \
            .format(e.filename, cmd)

        raise ArgumentTypeError(msg)


def _parse_phase(name: str) -> Phase:
    try:
        return Phase[name.upper()]
    except KeyError:
        choices = ', '.join(map(repr, map(str, Phase)))
        raise ArgumentTypeError("invalid choice: {} (choose from {})"
                                .format(repr(name), choices))


if __name__ == '__main__':
    main()
