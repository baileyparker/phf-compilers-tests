"""
Wrapper around async subprocess that abstracts away ProgramInvocation, which
when started produce an InteractiveProgram, which upon completion return a
CompletedProgram.
"""

from asyncio import AbstractEventLoop, create_subprocess_exec, WriteTransport, TimeoutError, wait_for  # noqa  # pylint: disable=W0622,C0301
from asyncio.subprocess import PIPE, Process
from io import StringIO
from pathlib import Path
from typing import Awaitable, cast, List, NamedTuple, Optional, TypeVar, Union

from simple_test.utils import join_cmd, relative_to_cwd


class ProgramInvocation:
    """Represents an invocation of some program."""

    def __init__(self, loop: AbstractEventLoop, binary: Path, args: List[str],  # noqa  # pylint: disable=R0913
                 stdin: Optional[Union[Path, 'CompletedProgram']] = None,
                 timeout: float = 5.0) -> None:
        self._loop = loop
        self._binary = binary
        self._args = args
        self._stdin = stdin
        self._timeout = timeout

    def run(self) -> 'CompletedProgram':
        """Invoke the program and return its result upon completion."""
        return self.start().wait()

    def start(self) -> 'InteractiveProgram':
        """Start the invocation to allow for interaction with the program."""
        if isinstance(self._stdin, Path):
            with self._stdin.open() as f:
                async_process = \
                    create_subprocess_exec(str(self._binary), *self._args,
                                           stdin=f, stdout=PIPE, stderr=PIPE,
                                           loop=self._loop)

                process = _run_async(self._loop, async_process,
                                     timeout=self._timeout)
        else:
            async_process = \
                create_subprocess_exec(str(self._binary), *self._args,
                                       stdin=PIPE, stdout=PIPE, stderr=PIPE,
                                       loop=self._loop)

            process = _run_async(self._loop, async_process,
                                 timeout=self._timeout)

        # Force writes to be sent immediately
        if self._stdin is None:
            assert process.stdin is not None
            transport = cast(WriteTransport, process.stdin.transport)
            transport.set_write_buffer_limits(0)

        # Pipe output from previous command if given as stdin
        if isinstance(self._stdin, CompletedProgram):
            assert process.stdin is not None
            process.stdin.write(self._stdin.stdout.encode('utf-8'))
            process.stdin.write_eof()

        return InteractiveProgram(process, self.cmd, self._timeout, self._loop)

    @property
    def cmd(self) -> str:
        """The equivalent bash command of the invocation."""
        cmd = join_cmd([relative_to_cwd(self._binary, binary=True),
                        *self._args])

        if self._stdin is not None:
            if isinstance(self._stdin, Path):
                cmd += " < {}".format(str(self._stdin))
            elif isinstance(self._stdin, CompletedProgram):
                cmd = "{} | {}".format(self._stdin.cmd, cmd)

        return cmd


R = TypeVar('R')


class InteractiveProgram:
    """A running program that can be interacted with via stdin."""

    def __init__(self, process: Process, cmd: str, timeout: float,
                 loop: AbstractEventLoop) -> None:
        self._process = process
        self._cmd = cmd
        self._timeout = timeout
        self._loop = loop

    def wait(self) -> 'CompletedProgram':
        """
        Wait (up to a timeout) for the program to finish and return its result.
        """
        stdout, stderr = self._run_async_timeout(self._process.communicate())

        return CompletedProgram(self._cmd, stdout.decode('utf8'),
                                stderr.decode('utf8'),
                                self._process.returncode)

    def write_line(self, line: str) -> None:
        """Write a line to the program's stdin (may timeout)."""
        assert line.endswith('\n'), 'line should end with newline'
        assert self._process.stdin is not None

        self._process.stdin.write(line.encode('utf-8'))
        self._run_async_timeout(self._process.stdin.drain())

    def read_line(self) -> str:
        """Read a line from the program's stdout (may timeout)."""
        assert self._process.stdout is not None

        line = self._run_async_timeout(self._process.stdout.readline())
        return line.decode('utf-8')

    def read_error_line(self) -> str:
        "Read a line from the program's stderr (may timeout)."""
        assert self._process.stderr is not None

        line = self._run_async_timeout(self._process.stderr.readline())
        return line.decode('utf-8')

    def _run_async_timeout(self, awaitable: Awaitable[R]) -> R:
        try:
            return _run_async(self._loop, awaitable, timeout=self._timeout)
        except TimeoutError:
            # Kill process then wait for it to actually die
            self._process.kill()
            self._loop.run_until_complete(self._process.communicate())

            raise


class CompletedProgram(NamedTuple('CompletedProgram', [('cmd', str),
                                                       ('stdout', str),
                                                       ('stderr', str),
                                                       ('returncode', int)])):
    """Represents the result of a program terminating."""
    @property
    def failed(self) -> bool:
        """Indicates if the program returned a failure."""
        return len(self.stderr) != 0 or self.returncode != 0


T = TypeVar('T')


def _run_async(loop: AbstractEventLoop, awaitable: Awaitable[T],
               timeout: float) -> T:
    timed_awaitable = wait_for(awaitable, timeout=timeout, loop=loop)
    value = loop.run_until_complete(timed_awaitable)

    return value
