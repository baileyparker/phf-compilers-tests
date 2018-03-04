"""Runners invoke a phase of the simple compiler and capture its output."""

from os import environ
from pathlib import Path
from shlex import quote as shell_quote
from subprocess import DEVNULL, PIPE, run
from typing import Callable, List, NamedTuple


Result = NamedTuple('Result', [('cmd', str),
                               ('stdout', bytes),
                               ('stderr', bytes)])

# NOTE: Mypy's callable doesn't allow for the as_stdin optional kwarg
SimpleRunner = Callable[[Path], Result]  # pylint: disable=C0103


def _run_simple(args: List[str], sim_file: Path,
                as_stdin: bool = False) -> Result:
    """
    Runs the simple compiler (at ./sc or in the SC env var, if provided)
    with the given arguments. If `as_stdin` is True, then the `sim_file` will
    be fed into the stdin of the compiler. Otherwise, `sim_file`'s path will be
    passed as the final argument to the compiler. Returns a result containing
    the stdout and stderr.
    """
    simple_compiler = environ.get('SC', './sc')

    # Make path relative to CWD so if we have to print out the full command
    # we ran (in a failed test assertion, for example), we don't have to
    # barf out the entire absolute path
    cwd = Path('.').resolve()
    try:
        sim_file = sim_file.relative_to(cwd)
    except ValueError:
        # Suppress if sim_file can't be made relative to cwd
        pass

    if not as_stdin:
        result = run([simple_compiler, *args, str(sim_file)], stdout=PIPE,
                     stderr=PIPE, stdin=DEVNULL)
    else:
        with sim_file.open() as f:
            result = run([simple_compiler, *args], stdin=f, stdout=PIPE,
                         stderr=PIPE)

    cmd = ' '.join(map(shell_quote, result.args))
    if as_stdin:
        cmd += " < {}".format(str(sim_file))

    return Result(cmd, result.stdout, result.stderr)


def run_simple_scanner(sim_file: Path, as_stdin: bool = False) -> Result:
    """
    Run the scanner phase of the simple compiler (at ./sc or in the SC env var,
    if provided). If `as_stdin` is True, then the `sim_file` will be fed into
    the stdin of the compiler. Otherwise, `sim_file`'s path will be passed as
    the final argument to the compiler. Returns a result containing the stdout
    and stderr.
    """
    return _run_simple(['-s'], sim_file, as_stdin)


def run_simple_cst(sim_file: Path, as_stdin: bool = False) -> Result:
    """
    Run the CST phase of the simple compiler (at ./sc or in the SC env var,
    if provided). If `as_stdin` is True, then the `sim_file` will be fed into
    the stdin of the compiler. Otherwise, `sim_file`'s path will be passed as
    the final argument to the compiler. Returns a result containing the stdout
    and stderr.
    """
    return _run_simple(['-c'], sim_file, as_stdin)


def run_simple_symbol_table(sim_file: Path, as_stdin: bool = False) -> Result:
    """
    Run the symbol table phase of the simple compiler (at ./sc or in the SC env
    var, if provided). If `as_stdin` is True, then the `sim_file` will be fed
    into the stdin of the compiler. Otherwise, `sim_file`'s path will be passed
    as the final argument to the compiler. Returns a result containing the
    stdout and stderr.
    """
    return _run_simple(['-t'], sim_file, as_stdin)
