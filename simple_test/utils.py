"""Utilities for the test harness."""

from contextlib import contextmanager
from difflib import unified_diff as _unified_diff
from pathlib import Path
import re
from shlex import quote as shell_quote
from typing import Callable, Generator, Iterable, List, TypeVar


@contextmanager
def assertion_context(context: str) -> Generator:
    """
    Helper context that prepends all AssertionErrors encountered within the
    context with some prefix string. Useful in tests to add the same context
    information to many assertions.
    """
    try:
        yield
    except AssertionError as e:
        e.args = ("{}{}".format(context, e.args[0]),)
        raise


def unified_diff(a: str, b: str,  # pylint: disable=C0103
                 fromfile: str = '', tofile: str = '', all_lines: bool = False,
                 color: bool = False) -> str:
    """
    Performs a unified diff of a and b (with optional filenames fromfile and
    tofile, respectively). If `color` is True, the returned diff is colored
    using ANSI terminal colors.
    """
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)

    n = max(len(a_lines), len(b_lines)) if all_lines else 3
    diff = _unified_diff(a_lines, b_lines, fromfile=fromfile, tofile=tofile,
                         n=n)

    if color:
        diff = map(_color_diff_line, diff)

    return ''.join(diff)


def _color_diff_line(line: str) -> str:
    if line[0] == '+':
        return _green(line)
    elif line[0] == '-':
        return _red(line)
    elif line[0] == '@':
        return _blue(line)

    return line


def _green(text: str) -> str:
    return "\033[1;32m{}\033[0;0m".format(text)


def _red(text: str) -> str:
    return "\033[1;31m{}\033[0;0m".format(text)


def _blue(text: str) -> str:
    return "\033[1;34m{}\033[0;0m".format(text)


def replace_values_with_fives(symbol_table_output: str) -> str:
    """Replaces all INTEGER values in symbol table output with 5's."""
    return re.sub(r'^(( *)(value|length):)$\n\2  (\d+)', r'\1\n\2  5',
                  symbol_table_output, flags=re.MULTILINE)


def relative_to_cwd(path: Path, binary: bool = False) -> str:
    """
    Returns a path relative to the CWD. Preserves the leading './' if the path
    points to a binary.
    """

    try:
        path = path.relative_to(Path.cwd())
    except ValueError:
        pass

    if binary and path.parent == Path('.'):
        return "./{}".format(path)

    return str(path)


def join_cmd(args: List[str]) -> str:
    """Joins a list of command line args into a well-formed command."""
    return ' '.join(map(shell_quote, args))


U = TypeVar('U')
V = TypeVar('V')


def catch_map(f: Callable[[U], V], iterable: Iterable[U]) -> List[V]:
    """
    Maps f over every item in iterable (even after exceptions). If no
    exceptions are raised, returns a list of the results. Otherwise, raises
    a MultiException containing all exceptions raised.
    """
    results = []  # List[V]
    exceptions = []  # List[Exception]

    for x in iterable:
        try:
            results.append(f(x))
        except Exception as e:  # pylint: disable=W0703
            exceptions.append(e)

    if exceptions:
        raise MultiException(exceptions)

    return results


class MultiException(Exception):
    """An exception that encapsulates many exceptions."""

    def __init__(self, exceptions: List[Exception]) -> None:
        super().__init__('\n'.join(map(str, exceptions)))
        self.exceptions = exceptions
