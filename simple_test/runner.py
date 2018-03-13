"""Runners invoke a phase of the simple compiler and capture its output."""

import os
from pathlib import Path
from shlex import quote as shell_quote
from subprocess import DEVNULL, PIPE, run
from typing import List, NamedTuple


Result = NamedTuple('Result', [('cmd', str),
                               ('stdout', bytes),
                               ('stderr', bytes)])


class Runner:
    """Runs a phase of a simple compiler under test and collects its output."""

    def __init__(self, sc_path: Path) -> None:
        self._sc_path = sc_path

    @classmethod
    def create(cls, sc_path: Path) -> 'Runner':
        """Creates a new runner for a compiler at sc_path."""
        if not sc_path.exists():
            raise BinaryNotFoundError(sc_path)
        if not os.access(str(sc_path), os.X_OK):
            raise BinaryNotExecutableError(sc_path)

        return cls(sc_path)

    def run_scanner(self, sim_file: Path, as_stdin: bool = False) -> Result:
        """
        Run the scanner phase of the simple compiler. If `as_stdin` is True,
        then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a result containing the stdout and stderr.
        """
        return self._run(['-s'], sim_file, as_stdin)

    def run_cst(self, sim_file: Path, as_stdin: bool = False) -> Result:
        """
        Run the CST phase of the simple compiler. If `as_stdin` is True, then
        the `sim_file` will be fed into the stdin of the compiler. Otherwise,
        `sim_file`'s path will be passed as the final argument to the compiler.
        Returns a result containing the stdout and stderr.
        """
        return self._run(['-c'], sim_file, as_stdin)

    def run_symbol_table(self, sim_file: Path,
                         as_stdin: bool = False) -> Result:
        """
        Run the symbol table phase of the simple compiler. If `as_stdin` is
        True, then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a result containing the stdout and stderr.
        """
        return self._run(['-t'], sim_file, as_stdin)

    def run_ast(self, sim_file: Path, as_stdin: bool = False) -> Result:
        """
        Run the AST phase of the simple compiler. If `as_stdin` is True, then
        the `sim_file` will be fed into the stdin of the compiler. Otherwise,
        `sim_file`'s path will be passed as the final argument to the compiler.
        Returns a result containing the stdout and stderr.
        """
        return self._run(['-a'], sim_file, as_stdin)

    def _run(self, args: List[str], sim_file: Path,
             as_stdin: bool = False) -> Result:
        """
        Runs the simple compiler with the given arguments. If `as_stdin` is
        True, then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a result containing the stdout and stderr.
        """

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
            result = run([str(self._sc_path), *args, str(sim_file)],
                         stdout=PIPE, stderr=PIPE, stdin=DEVNULL)
        else:
            with sim_file.open() as f:
                result = run([str(self._sc_path), *args], stdin=f, stdout=PIPE,
                             stderr=PIPE)

        cmd = ' '.join(map(shell_quote, result.args))
        if as_stdin:
            cmd += " < {}".format(str(sim_file))

        return Result(cmd, result.stdout, result.stderr)


class BinaryNotFoundError(FileNotFoundError):
    """The provided path to the simple binary does not exist."""
    def __init__(self, sc_path: Path) -> None:
        super().__init__(None, None, sc_path)


class BinaryNotExecutableError(Exception):
    """The provided simple binary is not executable."""
    def __init__(self, sc_path: Path) -> None:
        super().__init__("simple compiler not executable: {}".format(sc_path))
        self.filename = sc_path
