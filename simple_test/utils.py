"""Utilities for the test harness."""

from contextlib import contextmanager
from difflib import unified_diff as _unified_diff
from typing import Generator


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
                 fromfile: str = '', tofile: str = '',
                 color: bool = False) -> str:
    """
    Performs a unified diff of a and b (with optional filenames fromfile and
    tofile, respectively). If `color` is True, the returned diff is colored
    using ANSI terminal colors.
    """
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)

    diff = _unified_diff(a_lines, b_lines, fromfile=fromfile, tofile=tofile)

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
