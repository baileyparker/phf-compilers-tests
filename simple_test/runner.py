"""Runners invoke a phase of the simple compiler and capture its output."""

from asyncio import AbstractEventLoop, SelectorEventLoop, set_event_loop
import os
from pathlib import Path
import shutil
from types import TracebackType
from typing import List, Optional

from simple_test.subprocess import ProgramInvocation, CompletedProgram
from simple_test.typing_extensions import BaseExceptionType, ContextManager
from simple_test.utils import relative_to_cwd


class Runner(ContextManager['Runner']):
    """Runs a phase of a simple compiler under test and collects its output."""

    def __init__(self, loop: AbstractEventLoop, sc_path: Path,
                 timeout: float = 5.0) -> None:
        self._loop = loop
        self._sc_path = sc_path
        self._timeout = timeout

    @classmethod
    def create(cls, sc_path: Path, timeout: float = 5.0) -> 'Runner':
        """Creates a new runner for a compiler at sc_path."""
        if not sc_path.exists():
            raise BinaryNotFoundError(sc_path)
        if not os.access(str(sc_path), os.X_OK):
            raise BinaryNotExecutableError(sc_path)

        loop = SelectorEventLoop()
        # NOTE: https://stackoverflow.com/q/49952817/568785
        set_event_loop(loop)

        return cls(loop, sc_path, timeout=timeout)

    def run_scanner(self, sim_file: Path,
                    as_stdin: bool = False) -> ProgramInvocation:
        """
        Invoke the scanner phase of the simple compiler. If `as_stdin` is True,
        then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a ProgramInvocation that can be run with run() to
        obtain a CompletedProgram.
        """
        return self._make_invocation(['-s'], sim_file, as_stdin)

    def run_cst(self, sim_file: Path,
                as_stdin: bool = False) -> ProgramInvocation:
        """
        Invoke the CST phase of the simple compiler. If `as_stdin` is True,
        then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a ProgramInvocation that can be run with run() to
        obtain a CompletedProgram.
        """
        return self._make_invocation(['-c'], sim_file, as_stdin)

    def run_symbol_table(self, sim_file: Path,
                         as_stdin: bool = False) -> ProgramInvocation:
        """
        Invoke the symbol table phase of the simple compiler. If `as_stdin` is
        True, then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a ProgramInvocation that can be run with run() to
        obtain a CompletedProgram.
        """
        return self._make_invocation(['-t'], sim_file, as_stdin)

    def run_ast(self, sim_file: Path,
                as_stdin: bool = False) -> ProgramInvocation:
        """
        Invoke the AST phase of the simple compiler. If `as_stdin` is True,
        then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a ProgramInvocation that can be run with run() to
        obtain a CompletedProgram.
        """
        return self._make_invocation(['-a'], sim_file, as_stdin)

    def run_interpreter(self, sim_file: Path,
                        as_stdin: bool = False) -> ProgramInvocation:
        """
        Invoke the interpreter of the simple compiler. If `as_stdin` is True,
        then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a ProgramInvocation that can be run with run().
        For interactive simple programs call start() to get an
        InteractiveProgram on which you can write_line(), read_line(), and
        read_error_line(). Call wait() to get the CompletedProgram with
        returncode.

        Note that as mentioned on Piazza, the interpreter should be able to
        handle a sim file as stdin and then still allow READs (more stdin
        after stdin has been "closed"). Although this is simple in C/C++, it is
        often tricky in other languages that express stdin as a close-once
        stream. As such, this behavior is not required. So, it is undefined
        behavior to call write_line if the sim_file was passed as_stdin.
        """
        return self._make_invocation(['-i'], sim_file, as_stdin)

    def _make_invocation(self, args: List[str], sim_file: Path,
                         as_stdin: bool = False) -> ProgramInvocation:
        """
        Invoke the simple compiler with the given arguments. If `as_stdin` is
        True, then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a ProgramInvocation that can be run with run() to
        obtain a CompletedProgram.
        """

        if as_stdin:
            stdin = sim_file  # type: Optional[Path]
        else:
            args += [relative_to_cwd(sim_file)]
            stdin = None

        return ProgramInvocation(self._loop, self._sc_path, args, stdin=stdin,
                                 timeout=self._timeout)

    def __enter__(self) -> 'Runner':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> bool:
        try:
            self._loop.close()
        except RuntimeError:
            pass

        return False


class BinaryNotFoundError(FileNotFoundError):
    """The provided path to the simple binary does not exist."""
    def __init__(self, sc_path: Path) -> None:
        super().__init__(None, None, sc_path)


class BinaryNotExecutableError(Exception):
    """The provided simple binary is not executable."""
    def __init__(self, sc_path: Path) -> None:
        super().__init__("simple compiler not executable: {}".format(sc_path))
        self.filename = sc_path
