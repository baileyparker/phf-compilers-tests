"""
Files describing the expected behavior/output of certain compiler phases that
are capable of asserting (in the context of a TestCase) whether the program
under test behaved as expected.
"""

from asyncio import TimeoutError  # pylint: disable=W0622
from pathlib import Path
import sys
from typing import Any, cast, List, Optional, Union
from unittest import TestCase

from simple_test.subprocess import ProgramInvocation, InteractiveProgram
from simple_test.utils import unified_diff, relative_to_cwd, catch_map


class PhaseFile:
    """
    Describes the expected behavior of a running a certain phase (or the
    product of a certain phase) of the simple compiler under test against some
    sime file (see `Fixture`).
    """

    @classmethod
    def load(cls, phase_name: str, path: Path) -> 'PhaseFile':
        """Loads a PhaseFile with a given phase_name from a path."""
        if phase_name == 'run':
            return RunPhaseFile.load(phase_name, path)

        return OutputPhaseFile.load(phase_name, path)

    def assert_behavior(self, test_case: TestCase,
                        invocation: ProgramInvocation) -> None:
        """
        Asserts the behavior described by the PhaseFile is exhibited by the
        simple compiler under test. This behavior is tested against a specific
        invocation of the simple compiler. If it is not, a test failure is
        raised against test_case.
        """
        raise NotImplementedError


class OutputPhaseFile(PhaseFile):
    """
    The expected output of running a certain phase of the simple compiler under
    test against some sim file (see `Fixture`).
    """

    def __init__(self, stdout: str, has_error: bool) -> None:
        self.stdout = stdout
        self.has_error = has_error

    @classmethod
    def load(cls, _: str, path: Path) -> 'OutputPhaseFile':
        """Load and return an OutputPhaseFile from the filesystem."""

        with path.open() as f:
            stage_output = f.read()
            output_lines = stage_output.splitlines(keepends=True)
            stdout = ''.join(filter(lambda l: not l.startswith('error: '),
                                    output_lines))
            has_errors = any(l.startswith('error: ') for l in output_lines)

            return cls(stdout, has_errors)

    def assert_behavior(self, test_case: TestCase,
                        invocation: ProgramInvocation) -> None:
        """
        Assert running the simple compiler with the given invocation produces
        the expected output to stdout and stderr. If is does not, a test
        failure is raised against test_case.
        """
        result = invocation.run()

        if self.stdout != result.stdout:
            diff = unified_diff(self.stdout, result.stdout,
                                fromfile='expected_stdout',
                                tofile='actual_stdout',
                                color=sys.stdout.isatty())

            test_case.fail("wrong stdout:\n{}\n\nstderr was:\n\n{}"
                           .format(diff, result.stderr))

        if self.has_error:
            if not result.stderr.startswith('error: '):
                test_case.fail("expected stderr to have at least one error\n\n"
                               "stdout was:\n\n{}\n\nstderr was:\n\n{}"
                               .format(result.stdout, result.stderr))

            test_case.assertNotEqual(0, result.returncode,
                                     "expected non-zero returncode\n\n"
                                     "stdout was:\n\n{}\n\nstderr was:\n\n{}"
                                     .format(result.stdout, result.stderr))
        else:
            if result.stderr != '':
                test_case.fail("expected no errors to be reported\n\n"
                               "stdout was:\n\n{}\n\nstderr was:\n\n{}"
                               .format(result.stdout, result.stderr))

            test_case.assertEqual(0, result.returncode,
                                  "expected returncode 0 (got: {})\n\n"
                                  "stdout was:\n\n{}\n\nstderr was:\n\n{}"
                                  .format(result.returncode, result.stdout,
                                          result.stderr))


class Line(str):
    """Represents a line from a .run file."""

    def __new__(cls, *args: Any) -> 'Line':
        assert len(args) == 3
        value = cast(str, args[0])

        # Overridden to allow extra args not passed to str
        return cast(Line, super().__new__(cls, value))  # type: ignore

    def __init__(self, _: str, path: Path, line_num: int) -> None:
        super().__init__()

        self.path = path
        self.line_num = line_num

    def split(self, sep: Optional[str] = None,  # type: ignore
              maxsplit: int = -1) -> List['Line']:
        """
        Split a line (string) by a separator (default: whitespace) up to
        maxsplit times (default: unlimited).
        """
        return [Line(part, self.path, self.line_num)
                for part in super().split(sep, maxsplit)]

    def rstrip(self, chars: Optional[str] = None) -> 'Line':
        return Line(super().rstrip(chars), self.path, self.line_num)

    def __getitem__(self, index: Union[int, slice]) -> 'Line':
        """Get a slice or character from the Line."""
        return Line(super().__getitem__(index), self.path, self.line_num)

    def __add__(self, other: str) -> 'Line':
        return Line(super().__add__(other), self.path, self.line_num)

    @property
    def context(self) -> str:
        """The line's context (filename path and line number)."""
        return "{}:{}".format(self.path, self.line_num)


class RunLine:
    """Represents a line from a RunFile."""

    @classmethod
    def parse(cls, line: Line) -> 'RunLine':
        """Parse a RunLine from a line from a run file."""
        if line.startswith('> '):
            return InputLine.parse(line)
        elif line.startswith('error: '):
            return ExpectedErrorLine.parse(line)
        elif line.lstrip() == '' or line.lstrip().startswith('#'):
            return BlankLine.parse(line)

        return ExpectedOutputLine.parse(line)

    def expect(self, program: InteractiveProgram) -> None:
        """Expect the program to exhibit the RunLine's behavior."""
        raise NotImplementedError

    def __str__(self) -> str:
        """A representation of the expected line for error messages."""
        raise NotImplementedError


class RunLineParseError(Exception):
    """Raised when a line from a RunFile cannot be parsed."""
    def __init__(self, msg: str, line: Line) -> None:
        super().__init__("{}: {}".format(line.context, msg))
        self.msg = msg
        self.line = line


class RunLineAssertionError(Exception):
    """Raised the expectation of a RunLine is not met."""
    def __init__(self, msg: str, expected: List[str],
                 actual: List[str]) -> None:
        super().__init__(msg)

        self.msg = msg
        self.expected_lines = expected
        self.actual_lines = actual


class ExpectedOutputLine(RunLine):
    """Expects a certain number to be output by the program under test."""

    def __init__(self, expected_number: int, line: Line) -> None:
        self._expected_number = expected_number
        self._line = line

    @classmethod
    def parse(cls, line: Line) -> 'ExpectedOutputLine':
        """Parse an ExpectedOutputLine from a line from a run file."""
        return cls(_parse_int32(line), line)

    def expect(self, program: InteractiveProgram) -> None:
        """
        Expect the program to output self.expected_number. Otherwise, raises a
        OutputLineExpectationError. Raises a OutputLineTimeoutError on timeout.
        """
        try:
            line = program.read_line()
        except TimeoutError:
            raise OutputLineTimeoutError(self._line)

        if line != "{}\n".format(self._expected_number):
            raise OutputLineExpectationError(self._line, line)

    def __str__(self) -> str:
        """A representation of the expected line for error messages."""
        return str(self._line)


def _parse_int32(line: Line) -> int:
    try:
        value = int(_remove_comment(line)[:-1])
        if not -2**31 <= value <= 2**31-1:
            raise RunLineParseError('number must be an int32', line)

        return value
    except ValueError:
        raise RunLineParseError('line must contain a number', line)


class OutputLineExpectationError(RunLineAssertionError):
    """Raised when the program did not output the expected line."""
    def __init__(self, expected: str, actual: str) -> None:
        super().__init__('unexpected stdout line', [expected], [actual])


class OutputLineTimeoutError(RunLineAssertionError):
    """
    Raised when waiting for the program to output a line results in a timeout.
    """
    def __init__(self, expected: str) -> None:
        super().__init__('timeout while waiting for stdout line', [expected],
                         [])


class InputLine(RunLine):
    """Writes a certain number to the program under test's stdin."""

    def __init__(self, line: Line, phase_line: Line) -> None:
        assert line.endswith('\n'), 'line must be newline terminated'
        assert phase_line.startswith('> '), 'phase line must begin with "> "'

        self._line = line
        self._phase_line = phase_line

    @classmethod
    def parse(cls, line: Line) -> 'InputLine':
        """Parse an InputLine from a line from a run file."""

        assert line.startswith('> '), 'line must begin with "> "'
        return cls(_remove_comment(line[2:]), line)

    def expect(self, program: InteractiveProgram) -> None:
        """
        Expect the program to receive a number from stdin. Raises an
        InputLineTimeoutError if the write times out.
        """
        try:
            program.write_line(self._line)
        except TimeoutError:
            raise InputLineTimeoutError(self._phase_line)

    def __str__(self) -> str:
        """A representation of the expected line for error messages."""
        return str(self._phase_line)


class InputLineTimeoutError(RunLineAssertionError):
    """Raised when writing to the program's stdin results in a timeout."""
    def __init__(self, input_line: str) -> None:
        super().__init__('timeout while writing line to stdin', [input_line],
                         [])


def _remove_comment(line: Line) -> Line:
    return line.split('#')[0].rstrip() + '\n'


class ExpectedErrorLine(RunLine):
    """Expects the program under test to produce an error next."""

    def __init__(self, description: Line) -> None:
        self._description = description

    @classmethod
    def parse(cls, line: Line) -> 'ExpectedErrorLine':
        """Parse an ExpectedErrorLine from a line from a run file."""
        assert line.startswith('error: ')
        return cls(line)

    def expect(self, program: InteractiveProgram) -> None:
        """
        Expect the program write an error to stderr. If it doesn't, raises an
        ErrorLineExpectationError. Raises an InputLineTimeoutError if the
        expectation times out.
        """
        try:
            error = program.read_error_line()
        except TimeoutError:
            raise ErrorLineTimeoutError(self._description)

        if not error.startswith('error: '):
            raise ErrorLineExpectationError(self._description, error)

    def __str__(self) -> str:
        """A representation of the expected line for error messages."""
        return str(self._description)


class ErrorLineExpectationError(RunLineAssertionError):
    """Raised when stderr line does not match the expected stderr line."""
    def __init__(self, expected: str, actual: str) -> None:
        super().__init__('unexpected error line', [expected], [actual])


class ErrorLineTimeoutError(RunLineAssertionError):
    """Raised when waiting for a line from the program's stderr times out."""
    def __init__(self, expected: str) -> None:
        super().__init__('timeout while waiting for stderr line', [expected],
                         [])


class BlankLine(RunLine):
    """Represents a blank line or comment in a run file."""

    def __init__(self, line: Line) -> None:
        self._line = line

    @classmethod
    def parse(cls, line: Line) -> 'BlankLine':
        """Parse a BlankLine from a line from a run file."""
        return cls(line)

    def expect(self, program: InteractiveProgram) -> None:
        """Expect nothing from the program."""
        pass

    def __str__(self) -> str:
        """A representation of the expected line for error messages."""
        return str(self._line)


class RunPhaseFile(PhaseFile):
    """
    Represents the expected result of running a simple program (either via the
    interpreter or compiler). Encapsulates the inputs and expected
    outputs/errors in order.
    """

    def __init__(self, lines: List[RunLine]) -> None:
        self._lines = lines

    @classmethod
    def load(cls, phase_name: str, path: Path) -> 'RunPhaseFile':
        """Load and return an RunPhaseFile from the filesystem."""
        assert phase_name == 'run'

        with path.open() as f:
            relative_path = relative_to_cwd(path)
            raw_lines = f.read().splitlines(keepends=True)
            lines = (Line(l, Path(relative_path), i)
                     for i, l in enumerate(raw_lines))
            run_lines = catch_map(RunLine.parse, lines)

            return cls(run_lines)

    @property
    def _has_error(self) -> bool:
        return any(isinstance(line, ExpectedErrorLine) for line in self._lines)

    def assert_behavior(self, test_case: TestCase,
                        invocation: ProgramInvocation) -> None:
        """
        Asserts that when the invocation of the simple program is run with
        the run files inputs, the expected outputs and errors are produced in
        order (relative to eachother and relative to the inputs). If not, a
        test failure will be raised on test_case.
        """

        program = invocation.start()
        context = []

        try:
            for line in self._lines:
                line.expect(program)
                context.append(str(line))
        except RunLineAssertionError as e:
            expected = ''.join(context + e.expected_lines)
            actual = ''.join(context + e.actual_lines)
            diff = unified_diff(expected, actual, fromfile='expected_run',
                                tofile='actual_run', all_lines=True,
                                color=sys.stdout.isatty())

            # Wrapped to remove the "during the handling of" exception
            try:
                test_case.fail("{}:\n\n{}".format(e.msg, diff))
            except AssertionError as e:
                raise e from None

        try:
            completed = program.wait()
        except TimeoutError:
            test_case.fail("timed out waiting for program to finish\n\n"
                           "context:\n\n{}".format(''.join(context)))

        test_case.assertEqual('', completed.stdout,
                              "expected no more stdout\n\n"
                              "context:\n\n{}\n\nextra stdout:\n\n{}\n\n"
                              "stderr:\n\n{}"
                              .format(''.join(context), completed.stdout,
                                      completed.stderr))

        if self._has_error:
            test_case.assertNotEqual(0, completed.returncode,
                                     "expected non-zero returncode\n\n"
                                     "context:\n\n{}".format(''.join(context)))
        else:
            test_case.assertEqual('', completed.stderr,
                                  "expected no more stderr\n\n"
                                  "context:\n\n{}\n\nextra stderr:\n\n{}"
                                  .format(''.join(context), completed.stderr))

            test_case.assertEqual(0, completed.returncode,
                                  "expected returncode 0 (got: {})\n\n"
                                  "context:\n\n{}".format(completed.returncode,
                                                          ''.join(context)))
