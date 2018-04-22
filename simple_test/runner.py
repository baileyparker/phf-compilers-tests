"""Runners invoke a phase of the simple compiler and capture its output."""

from asyncio import AbstractEventLoop, SelectorEventLoop, set_event_loop, \
    TimeoutError
import os
from pathlib import Path
import shutil
from types import TracebackType
from typing import Dict, List, Optional, Tuple, Union

from simple_test.fixtures import FIXTURES
from simple_test.subprocess import ProgramInvocation, CompletedProgram
from simple_test.typing_extensions import BaseExceptionType, ContextManager
from simple_test.utils import relative_to_cwd


RemoteTempDir = Optional[Union[Path, 'BinaryCacheError']]
CompilationCache = Dict[Tuple[Path, bool, bool],
                        Union[ProgramInvocation, Exception]]


class Runner(ContextManager['Runner']):
    """Runs a phase of a simple compiler under test and collects its output."""

    def __init__(self, loop: AbstractEventLoop, sc_path: Path,
                 timeout: float = 5.0, remote: Optional[str] = None) -> None:
        self._loop = loop
        self._sc_path = sc_path
        self._timeout = timeout
        self._remote = remote
        self._remote_temp_dir_ = None  # type: RemoteTempDir
        self._compilation_cache = {}  # type: CompilationCache

    @classmethod
    def create(cls, sc_path: Path, timeout: float = 5.0,
               remote: Optional[str] = None) -> 'Runner':
        """Creates a new runner for a compiler at sc_path."""
        if not sc_path.exists():
            raise BinaryNotFoundError(sc_path)
        if not os.access(str(sc_path), os.X_OK):
            raise BinaryNotExecutableError(sc_path)

        loop = SelectorEventLoop()
        # NOTE: https://stackoverflow.com/q/49952817/568785
        set_event_loop(loop)

        return cls(loop, sc_path, timeout=timeout, remote=remote)

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

    # TODO: handle compile time errors
    def run_compiler(self, sim_file: Path,
                     as_stdin: bool = False,
                     advanced: bool = False) -> ProgramInvocation:
        """
        Invoke the silly compiler of the simple compiler. If `as_stdin` is
        True, then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise `sim_file`s path wil be passed as the final argument to the
        compiler. Returns a ProgramInvocation that can be run with run(). This
        will run the produced binary (after running the simple compiler and
        assembling its output assembly with gcc). For interactive simple
        programs call start() to get an InteractiveProgram on which you can
        write_line(), read_line(), and read_error_line(). Call wait() to get
        the CompletedProgram with returncode.
        """
        key = (sim_file, as_stdin, advanced)

        try:
            invocation = self._compilation_cache[key]
        except KeyError:
            try:
                # Fail early...
                remote_temp_dir = self._remote_temp_dir

                # Compile with simple compiler
                sc_args = ['-x'] if advanced else []
                compiler = self._run(sc_args, sim_file, as_stdin)
                if compiler.failed:
                    raise CompilationError(compiler) from None

                if as_stdin:
                    stdin = compiler
                else:
                    stdin = sim_file.with_suffix('.s')
                    if not stdin.exists():
                        raise AssemblyFileNotFoundError(compiler) from None
                    # TODO: clean up file creation

                # Assemble with gcc (remote)
                name = str(sim_file.relative_to(FIXTURES)).replace('/', '_')
                if as_stdin:
                    name += '-stdin'

                binary = remote_temp_dir / name
                gcc = self._run_remote(['gcc', '-x', 'assembler', '-o',
                                        str(binary), '-'], stdin=stdin)
                if gcc.failed:
                    # TODO: include generated assembly
                    # TODO: add context to gcc errors
                    raise AssemblyError(gcc) from None

                # Cache invocation of remote compiled simple program binary
                invocation = self._make_remote_invocation([str(binary)],
                                                          interactive=True)
            except (ToolchainError, TimeoutError) as e:
                invocation = e
            finally:
                self._compilation_cache[key] = invocation

        if isinstance(invocation, ToolchainError):
            raise invocation
        else:
            return invocation

    # TODO: advanced codegen

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

    def _run(self, args: List[str], sim_file: Path,
             as_stdin: bool = False) -> CompletedProgram:
        """
        Run the simple compiler with the given arguments. If `as_stdin` is
        True, then the `sim_file` will be fed into the stdin of the compiler.
        Otherwise, `sim_file`'s path will be passed as the final argument to
        the compiler. Returns a CompletedProgram.
        """
        return self._make_invocation(args, sim_file, as_stdin).run()

    # TODO: interactive=False returns different object that raises on
    #       write_line (to catch issue early)
    def _make_remote_invocation(self, args: List[str],
                                stdin: Optional[CompletedProgram] = None,
                                interactive: bool = False) -> ProgramInvocation:  # noqa
        """
        Run the command specified by args on the remote device whose arch
        matches the target of the assembly output by the simple compiler. The
        'remote' (user@host) can be passed into the Runner at initialization.
        If stdin is a CompletedProgram, its output is piped into the remote
        process as if the following pseudo-shell had been run
        'stdin | ssh *args'. If you want to call start() on the returned
        ProgramInvocation (and use write_line()), you must pass
        interactive=True.
        """
        assert self._remote is not None, 'must specify --remote'

        # TODO: Ideally, ProgramInvocation wouldn't always './' the binary so
        #       we wouldn't have to do this.
        ssh_abs_path = shutil.which('ssh')
        assert ssh_abs_path is not None, 'unable to find ssh'

        ssh = Path(ssh_abs_path)
        prefix = ['-t'] if interactive else []
        ssh_args = [*prefix, '-o', 'LogLevel=QUIET', self._remote, *args]

        return ProgramInvocation(self._loop, ssh, ssh_args, stdin=stdin,
                                 timeout=self._timeout)

    def _run_remote(self, args: List[str],
                    stdin: Optional[CompletedProgram] = None,
                    interactive: bool = False) -> CompletedProgram:
        return self._make_remote_invocation(args, stdin, interactive).run()

    @property
    def _remote_temp_dir(self) -> Path:
        if self._remote_temp_dir_ is None:
            result = self._run_remote(['mktemp', '-d'])
            self._remote_temp_dir_ = \
                BinaryCacheError(result) if result.failed \
                else Path(result.stdout.strip())

        if isinstance(self._remote_temp_dir_, BinaryCacheError):
            raise self._remote_temp_dir_
        else:
            return self._remote_temp_dir_

    def __enter__(self) -> 'Runner':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> bool:
        if self._remote_temp_dir_ is not None:
            self._run_remote(['rm', '-r', str(self._remote_temp_dir_)])

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


class ToolchainError(Exception):
    pass


class BinaryCacheError(ToolchainError):
    def __init__(self, result: CompletedProgram) -> None:
        msg = "Unable to create tmp dir for binary cache " \
              "with '{}' (returned {}):\n\n{}".format(result.cmd,
                                                      result.returncode,
                                                      result.stderr)
        super().__init__(msg)

        self.result = result


class ToolchainPhaseError(ToolchainError):
    """Base for errors caused by the compilation toolchain."""
    def __init__(self, subject: str, result: CompletedProgram) -> None:
        msg = "Error ({}) while {} '{}':\n\n{}".format(result.returncode,
                                                       subject,
                                                       result.cmd,
                                                       result.stderr)
        super().__init__(msg)

        self.result = result


class CompilationError(ToolchainPhaseError):
    """Failed to compile the simple script with ./sc or ./sc -x."""
    def __init__(self, result: CompletedProgram) -> None:
        super().__init__('compiling', result)


class AssemblyFileNotFoundError(ToolchainError):
    """The expected *.s file was not created by the compiler."""
    def __init__(self, result: CompletedProgram) -> None:
        msg = "could not find *.s file produced by: {}".format(result, cmd)
        super().__init__(self, msg)

        self.result = result


class AssemblyError(ToolchainPhaseError):
    """Failed to compile the output assembly with gcc."""
    def __init__(self, result: CompletedProgram) -> None:
        # TODO: add context to gcc errors
        super().__init__('assembling', result)
