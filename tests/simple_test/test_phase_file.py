from asyncio import TimeoutError  # pylint: disable=W0622
from functools import partial
from pathlib import Path
from unittest import main, TestCase
from unittest.mock import ANY, Mock, MagicMock, patch

from simple_test.phase_file import PhaseFile, OutputPhaseFile, RunPhaseFile, \
    Line, RunLine, RunLineParseError, RunLineAssertionError, \
    ExpectedOutputLine, InputLine, ExpectedErrorLine, BlankLine, \
    OutputLineExpectationError, OutputLineTimeoutError, \
    InputLineTimeoutError, ErrorLineExpectationError, ErrorLineTimeoutError
from simple_test.subprocess import ProgramInvocation, InteractiveProgram, \
    CompletedProgram


class TestPhaseFile(TestCase):
    def test_load_run_phase_file(self):
        self.assertLoadPhaseNameLoadsType('run', 'RunPhaseFile')

    def test_load_output_phase_file(self):
        self.assertLoadPhaseNameLoadsType('something_else', 'OutputPhaseFile')

    def assertLoadPhaseNameLoadsType(self, phase_name, type_class):
        with patch("simple_test.phase_file.{}".format(type_class)) as type_:
            phase_file = Mock()
            path = Mock(spec=Path)
            type_.load.return_value = phase_file

            self.assertEqual(phase_file, PhaseFile.load(phase_name, path))
            type_.load.assert_called_once_with(phase_name, path)


class TestOutputPhaseFile(TestCase):
    def test_load_no_errors(self):
        self.assertLoads("a\nb\nc\n", "a\nb\nc\n", has_error=False)

    def test_load_with_errors(self):
        self.assertLoads("a\nb\nerror: foo\nc\n", "a\nb\nc\n", has_error=True)

    def assertLoads(self, contents, stdout, has_error):
        PREFIX = 'simple_test.phase_file.'
        with patch(PREFIX + 'OutputPhaseFile') as OutputPhaseFile_:
            phase_file = Mock(spec=OutputPhaseFile)
            OutputPhaseFile_.return_value = phase_file

            path = Mock(autospec=Path)
            file_context = MagicMock()
            f = Mock()
            path.open.return_value = file_context
            file_context.__enter__.return_value = f
            f.read.return_value = contents

            load = partial(OutputPhaseFile.load.__func__, OutputPhaseFile_)
            self.assertEqual(phase_file, load('ext', path))

            path.open.assert_called_once_with()
            OutputPhaseFile_.assert_called_once_with(stdout, has_error)

    def test_assert_behavior(self):
        stdout = Mock()
        self.assert_behavior_with(expected_stdout=stdout, has_error=False,
                                  actual_stdout=stdout, actual_stderr='',
                                  returncode=0)

    def test_assert_behavior_has_error(self):
        stdout = Mock()
        self.assert_behavior_with(expected_stdout=stdout, has_error=True,
                                  actual_stdout=stdout,
                                  actual_stderr='error: something',
                                  returncode=1)

    @patch('simple_test.phase_file.sys.stdout.isatty')
    @patch('simple_test.phase_file.unified_diff')
    def test_assert_behavior_stdout_not_equal(self, unified_diff, isatty):
        expected_stdout, actual_stdout = Mock(), Mock()
        isatty.return_value = Mock()
        unified_diff.return_value = 'unified diff!'
        stderr = 'actual stderr'

        error = "wrong stdout:\n{}\n\nstderr was:\n\n{}" \
            .format(unified_diff.return_value, stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with(expected_stdout=expected_stdout,
                                      has_error=False,
                                      actual_stdout=actual_stdout,
                                      actual_stderr=stderr, returncode=0)

        unified_diff.assert_called_once_with(expected_stdout, actual_stdout,
                                             fromfile='expected_stdout',
                                             tofile='actual_stdout',
                                             color=isatty.return_value)

    def test_assert_behavior_stderr_non_empty(self):
        stdout = 'actual stdout'
        stderr = 'error: something bad'

        error = 'expected no error.*\n\nstdout.*:\n\n{}\n\nstderr.*:\n\n{}' \
            .format(stdout, stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with(expected_stdout=stdout, has_error=False,
                                      actual_stdout=stdout,
                                      actual_stderr=stderr, returncode=1)

    def test_assert_behavior_has_error_but_stderr_empty(self):
        stdout = 'actual stdout'
        stderr = ''

        error = 'at least one error.*\n\nstdout.*:\n\n{}\n\nstderr.*:\n\n{}' \
            .format(stdout, stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with(expected_stdout=stdout, has_error=True,
                                      actual_stdout=stdout,
                                      actual_stderr=stderr, returncode=1)

    def test_assert_behavior_has_error_but_zero_returncode(self):
        stdout = 'actual stdout'
        stderr = 'error: something'

        error = \
            "non-zero returncode\n\nstdout was:\n\n{}\n\nstderr was:\n\n{}" \
            .format(stdout, stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with(expected_stdout=stdout, has_error=True,
                                      actual_stdout=stdout,
                                      actual_stderr=stderr, returncode=0)

    def test_assert_behavior_no_error_but_nonzero_returncode(self):
        stdout = 'actual stdout'
        stderr = ''
        returncode = 1

        error = r"returncode 0 \(got: {}\)\n\n" \
                "stdout was:\n\n{}\n\nstderr was:\n\n{}" \
                .format(returncode, stdout, stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with(expected_stdout=stdout, has_error=False,
                                      actual_stdout=stdout,
                                      actual_stderr=stderr,
                                      returncode=returncode)

    def assert_behavior_with(self, expected_stdout, has_error, actual_stdout,
                             actual_stderr, returncode):
        phase_file = OutputPhaseFile(expected_stdout, has_error)
        invocation = Mock(spec=ProgramInvocation)
        completed_program = Mock(spec=CompletedProgram)
        completed_program.stdout = actual_stdout
        completed_program.stderr = actual_stderr
        completed_program.returncode = returncode

        invocation.run.return_value = completed_program

        phase_file.assert_behavior(self, invocation)


class TestLine(TestCase):
    def setUp(self):
        self.path = Path('some/path')
        self.line_num = 123
        self.line = Line('abc', self.path, self.line_num)

    def test_slice_behavior(self):
        sliced = self.line[1:]

        self.assertEqual('bc', sliced)
        self.assertEqual(sliced, 'bc')
        self.assertTrue(sliced.startswith('b'))
        self.assertEqual(self.path, sliced.path)
        self.assertEqual(self.line_num, sliced.line_num)

    def test_split_behavior(self):
        split = self.line.split('b')[1]

        self.assertEqual('c', split)
        self.assertEqual(split, 'c')
        self.assertTrue(split.startswith('c'))
        self.assertEqual(self.path, split.path)
        self.assertEqual(self.line_num, split.line_num)

    def test_rstrip_behavior(self):
        line = Line('abc  ', self.path, self.line_num)
        split = line.rstrip()

        self.assertEqual('abc', split)
        self.assertEqual(split, 'abc')
        self.assertTrue(split.startswith('ab'))
        self.assertEqual(self.path, split.path)
        self.assertEqual(self.line_num, split.line_num)

    def test_plus_behavior(self):
        line = Line('abc', self.path, self.line_num)
        added = line + 'd'

        self.assertEqual('abcd', added)
        self.assertEqual(added, 'abcd')
        self.assertTrue(added.endswith('cd'))
        self.assertEqual(self.path, added.path)
        self.assertEqual(self.line_num, added.line_num)

    def test_context(self):
        self.assertEqual('some/path:123', self.line.context)

    def test_str(self):
        self.assertEqual('abc', str(self.line))
        self.assertIs(type(str(self.line)), str)


class TestRunLine(TestCase):
    @patch('simple_test.phase_file.InputLine')
    def test_parse_input(self, InputLine_):
        line = '> 123\n'
        parsed = Mock(spec=InputLine)

        InputLine_.parse.return_value = parsed

        self.assertEqual(parsed, RunLine.parse(line))
        InputLine_.parse.assert_called_once_with(line)

    @patch('simple_test.phase_file.ExpectedOutputLine')
    def test_parse_output(self, ExpectedOutputLine_):
        line = '123\n'
        parsed = Mock(spec=ExpectedOutputLine)

        ExpectedOutputLine_.parse.return_value = parsed

        self.assertEqual(parsed, RunLine.parse(line))
        ExpectedOutputLine_.parse.assert_called_once_with(line)

    @patch('simple_test.phase_file.ExpectedErrorLine')
    def test_parse_error(self, ExpectedErrorLine_):
        line = 'error: foo\n'
        parsed = Mock(spec=ExpectedErrorLine)

        ExpectedErrorLine_.parse.return_value = parsed

        self.assertEqual(parsed, RunLine.parse(line))
        ExpectedErrorLine_.parse.assert_called_once_with(line)

    @patch('simple_test.phase_file.BlankLine')
    def test_parse_blank(self, BlankLine_):
        line = '  \n'
        parsed = Mock(spec=BlankLine)

        BlankLine_.parse.return_value = parsed

        self.assertEqual(parsed, RunLine.parse(line))
        BlankLine_.parse.assert_called_once_with(line)

    @patch('simple_test.phase_file.BlankLine')
    def test_parse_comment(self, BlankLine_):
        line = '  # this is a comment\n'
        parsed = Mock(spec=BlankLine)

        BlankLine_.parse.return_value = parsed

        self.assertEqual(parsed, RunLine.parse(line))
        BlankLine_.parse.assert_called_once_with(line)


class TestExpectedOutputLine(TestCase):
    def setUp(self):
        self.RunLineType = ExpectedOutputLine
        self.run_line_name = 'ExpectedOutputLine'
        self.line_format = "{}\n"

    def test_parse(self):
        numbers = [123, -2**31, 2**31-1]
        for number in numbers:
            with self.subTest(number):
                self.assertParsesNumber(number)

    def test_parse_with_comments(self):
        self.assertParsesNumber(123, line='123 # foo')
        self.assertParsesNumber(123, line='123#456')

    def assertParsesNumber(self, number, line=None):
        PREFIX = 'simple_test.phase_file.'
        line = "{}\n".format(number if line is None else line)

        with patch(PREFIX + 'ExpectedOutputLine') as ExpectedOutputLine_:
            run_line = Mock(spec=ExpectedOutputLine)
            ExpectedOutputLine_.return_value = run_line

            parse = partial(ExpectedOutputLine.parse.__func__,
                            ExpectedOutputLine_)
            self.assertEqual(run_line, parse(Line(line, None, None)))

            ExpectedOutputLine_.assert_called_once_with(number, line)

    def test_parse_not_number(self):
        with self.assertRaisesRegex(RunLineParseError, 'contain a number'):
            ExpectedOutputLine.parse(Line(self.line_format.format('abc\n'),
                                          None, None))

    def test_parse_not_int32(self):
        with self.assertRaisesRegex(RunLineParseError, 'int32'):
            ExpectedOutputLine.parse(Line(self.line_format.format(-2**31 - 1),
                                        None, None))

        with self.assertRaisesRegex(RunLineParseError, 'int32'):
            ExpectedOutputLine.parse(Line(self.line_format.format(2**31), None,
                                        None))

    def test_expect(self):
        line = ExpectedOutputLine(123, None)
        program = Mock(spec=InteractiveProgram)
        program.read_line.return_value = '123\n'

        line.expect(program)
        program.read_line.assert_called_once_with()

    def test_expect_unexpected(self):
        line = ExpectedOutputLine(123, 'expected line\n')
        program = Mock(spec=InteractiveProgram)
        program.read_line.return_value = '456\n'

        with self.assertRaises(OutputLineExpectationError) as cm:
            line.expect(program)

        program.read_line.assert_called_once_with()

        e = cm.exception
        self.assertEqual(['expected line\n'], e.expected_lines)
        self.assertEqual(['456\n'], e.actual_lines)

    def test_expect_timeout(self):
        line = ExpectedOutputLine(123, 'expected line\n')
        program = Mock(spec=InteractiveProgram)
        program.read_line.side_effect = TimeoutError()

        with self.assertRaises(OutputLineTimeoutError) as cm:
            line.expect(program)

        program.read_line.assert_called_once_with()

        e = cm.exception
        self.assertEqual(['expected line\n'], e.expected_lines)
        self.assertEqual([], e.actual_lines)

    def test_str(self):
        line = ExpectedOutputLine(123, 'actual line')
        self.assertEqual('actual line', str(line))


class TestInputLine(TestCase):
    def test_parse(self):
        self.assertParses('123\n', '> 123\n')
        self.assertParses('a\n', '> a\n')

    def test_parse_with_comments(self):
        self.assertParses('123\n', '> 123 # foo\n')
        self.assertParses('123\n', '> 123#456\n')
        self.assertParses('abc\n', '> abc # foo\n')
        self.assertParses('abc\n', '> abc#456\n')

    @patch('simple_test.phase_file.InputLine')
    def assertParses(self, line, phase_line, InputLine_):
        run_line = Mock(spec=InputLine)

        InputLine_.return_value = run_line

        parse = partial(InputLine.parse.__func__, InputLine_)
        self.assertEqual(run_line, parse(phase_line))

        InputLine_.assert_called_once_with(line, phase_line)

    def test_parse_no_gt(self):
        with self.assertRaises(AssertionError):
            InputLine.parse(Line('abc\n', None, None))

    def test_expect(self):
        line = InputLine('123\n', '> 123\n')
        program = Mock(spec=InteractiveProgram)

        line.expect(program)
        program.write_line.assert_called_once_with('123\n')

    def test_expect_timeout(self):
        line = InputLine('123\n', '> expected line\n')
        program = Mock(spec=InteractiveProgram)
        program.write_line.side_effect = TimeoutError

        with self.assertRaises(InputLineTimeoutError) as cm:
            line.expect(program)

        program.write_line.assert_called_once_with('123\n')

        e = cm.exception
        self.assertEqual(['> expected line\n'], e.expected_lines)
        self.assertEqual([], e.actual_lines)

    def test_str(self):
        line = InputLine('123\n', '> actual line')
        self.assertEqual('> actual line', str(line))


class TestExpectedErrorLine(TestCase):
    @patch('simple_test.phase_file.ExpectedErrorLine')
    def test_parse(self, ExpectedErrorLine_):
        line = Mock(spec=ExpectedErrorLine)
        ExpectedErrorLine_.return_value = line

        parse = partial(ExpectedErrorLine.parse.__func__, ExpectedErrorLine_)
        self.assertEqual(line, parse(Line("error: abc", None, None)))

        ExpectedErrorLine_.assert_called_once_with("error: abc")

    def test_parse_no_prefix(self):
        with self.assertRaises(AssertionError):
            ExpectedErrorLine.parse(Line('abc\n', None, None))

    def test_expect(self):
        line = ExpectedErrorLine('error: foo\n')
        program = Mock(spec=InteractiveProgram)
        program.read_error_line.return_value = 'error: bar\n'

        line.expect(program)
        program.read_error_line.assert_called_once_with()

    def test_expect_unexpected(self):
        line = ExpectedErrorLine('error: foo\n')
        program = Mock(spec=InteractiveProgram)
        program.read_error_line.return_value = 'foo\n'

        with self.assertRaises(ErrorLineExpectationError) as cm:
            line.expect(program)

        program.read_error_line.assert_called_once_with()

        e = cm.exception
        self.assertEqual(['error: foo\n'], e.expected_lines)
        self.assertEqual(['foo\n'], e.actual_lines)

    def test_expect_timeout(self):
        line = ExpectedErrorLine('error: foo\n')
        program = Mock(spec=InteractiveProgram)
        program.read_error_line.side_effect = TimeoutError()

        with self.assertRaises(ErrorLineTimeoutError) as cm:
            line.expect(program)

        program.read_error_line.assert_called_once_with()

        e = cm.exception
        self.assertEqual(['error: foo\n'], e.expected_lines)
        self.assertEqual([], e.actual_lines)

    def test_str(self):
        error = 'error: foo\n'
        line = ExpectedErrorLine(error)
        self.assertEqual(error, str(line))


class TestBlankLine(TestCase):
    def setUp(self):
        self.line = 'line'
        self.blank_line = BlankLine(self.line)

    @patch('simple_test.phase_file.BlankLine')
    def test_parse(self, BlankLine_):
        line = Mock(spec=BlankLine)
        BlankLine_.return_value = line

        parse = partial(BlankLine.parse.__func__, BlankLine_)
        self.assertEqual(line, parse(Line("line", None, None)))

        BlankLine_.assert_called_once_with("line")

    def test_expect(self):
        program = Mock(spec=ProgramInvocation)
        self.blank_line.expect(program)

    def test_str(self):
        self.assertEqual(self.line, str(self.blank_line))


class TestRunPhaseFile(TestCase):
    @patch('simple_test.phase_file.catch_map')
    @patch('simple_test.phase_file.relative_to_cwd')
    @patch('simple_test.phase_file.RunPhaseFile')
    @patch('simple_test.phase_file.Line')
    def test_load(self, Line_, RunPhaseFile_, relative_to_cwd, catch_map):
        # Setup mocks
        path = Mock(autospec=Path)
        file_context = MagicMock()
        f = Mock()

        contents = 'a\nb\nc\n'
        contents_lines = contents.splitlines(keepends=True)

        lines = [Mock(spec=Line) for _ in contents_lines]
        run_lines = Mock()
        phase_file = Mock(spec=RunPhaseFile)
        relative_path = 'path/to/file'

        # Setup return values
        path.open.return_value = file_context
        file_context.__enter__.return_value = f
        f.read.return_value = contents

        calls_to_line = \
            {(line, Path(relative_path), i): mock
             for (i, line), mock in zip(enumerate(contents_lines), lines)}
        Line_.side_effect = lambda l, p, i: calls_to_line[(l, p, i)]

        relative_to_cwd.return_value = relative_path
        catch_map.return_value = run_lines
        RunPhaseFile_.return_value = phase_file

        # Assert behavior
        load = partial(RunPhaseFile.load.__func__, RunPhaseFile_)
        self.assertEqual(phase_file, load('run', path))

        relative_to_cwd.assert_called_once_with(path)
        path.open.assert_called_once_with()
        f.read.assert_called_once_with()
        catch_map.assert_called_once_with(RunLine.parse, ANY)
        self.assertEqual(lines, list(catch_map.call_args[0][1]))
        RunPhaseFile_.assert_called_once_with(run_lines)

    def test_assert_behavior_no_lines(self):
        program = Mock(spec=InteractiveProgram)
        self.assert_behavior_with([], program)

    def test_assert_behavior(self):
        lines = [MagicMock(spec=RunLine) for _ in range(5)]
        program = Mock(spec=InteractiveProgram)

        call_order = []
        for x, line in enumerate(lines):
            line.expect.side_effect = \
                (lambda x: lambda _: call_order.append(x))(x)  # noqa  # pylint: disable=E0602

        self.assert_behavior_with(lines, program)

        for line in lines:
            line.expect.assert_called_once_with(program)

        self.assertEqual(list(range(len(lines))), call_order,
                         'lines must be called in order')

    def test_assert_behavior_has_error(self):
        lines = [MagicMock(spec=ExpectedErrorLine)]
        program = Mock(spec=InteractiveProgram)

        self.assert_behavior_with(lines, program, returncode=1)

        lines[0].expect.assert_called_once_with(program)

    @patch('simple_test.phase_file.sys.stdout.isatty')
    @patch('simple_test.phase_file.unified_diff')
    def test_assert_behavior_bad_line(self, unified_diff, isatty):
        lines = [MagicMock(spec=RunLine) for _ in range(2)]

        lines[0].__str__.return_value = 'some context\n'

        lines[1].expect.side_effect = \
            RunLineAssertionError('msg', ['expected'], ['actual'])

        program = Mock(spec=InteractiveProgram)

        unified_diff.return_value = 'unified diff!'
        isatty.return_value = Mock()

        with self.assertRaisesRegex(AssertionError, 'msg:\n\nunified diff!'):
            program = self.assert_behavior_with(lines, program)

        for line in lines:
            line.expect.assert_called_once_with(program)

        expected = 'some context\nexpected'
        actual = 'some context\nactual'
        unified_diff.assert_called_once_with(expected, actual,
                                             fromfile='expected_run',
                                             tofile='actual_run',
                                             all_lines=True,
                                             color=isatty.return_value)

    def test_assert_behavior_wait_timeout(self):
        error = 'timed out.*\n\ncontext:\n\ncontext a\ncontext b\n'

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with_context(wait_raises=True)

    def test_assert_behavior_extra_stdout(self):
        stdout = 'extra stdout'
        stderr = 'some stderr'

        error = "no more stdout\n\ncontext:\n\ncontext a\ncontext b\n" \
                "\n\nextra stdout:\n\n{}\n\nstderr:\n\n{}" \
                .format(stdout, stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with_context(stdout=stdout, stderr=stderr)

    def test_assert_behavior_has_error_but_zero_returncode(self):
        error = "non-zero returncode\n\ncontext:\n\ncontext a\ncontext b\n"

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with_context(has_error=True)

    def test_assert_behavior_input_no_error_but_nonzero_returncode(self):
        returncode = 1

        error = r"returncode 0 \(got: {}\)\n\n" \
                "context:\n\ncontext a\ncontext b\n".format(returncode)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with_context(returncode=returncode)

    def test_assert_behavior_input_no_error_but_extra_stderr(self):
        stderr = 'extra stderr'

        error = "no more stderr\n\ncontext:\n\ncontext a\ncontext b\n" \
                "\n\nextra stderr:\n\n{}".format(stderr)

        with self.assertRaisesRegex(AssertionError, error):
            self.assert_behavior_with_context(stderr=stderr)

    def assert_behavior_with_context(self, stdout='', stderr='', returncode=0,
                                     wait_raises=False, has_error=False):
        line_type = ExpectedErrorLine if has_error else RunLine
        lines = [MagicMock(spec=line_type) for _ in range(2)]
        lines[0].__str__.return_value = 'context a\n'
        lines[1].__str__.return_value = 'context b\n'

        program = Mock(spec=InteractiveProgram)

        self.assert_behavior_with(lines, program, stdout=stdout, stderr=stderr,
                                  returncode=returncode,
                                  wait_raises=wait_raises)

    def assert_behavior_with(self, run_lines, program, stdout='', stderr='',
                             returncode=0, wait_raises=False):
        phase_file = RunPhaseFile(run_lines)
        invocation = Mock(spec=ProgramInvocation)
        completed_program = CompletedProgram('cmd', stdout, stderr, returncode)

        invocation.start.return_value = program
        if not wait_raises:
            program.wait.return_value = completed_program
        else:
            program.wait.side_effect = TimeoutError()

        phase_file.assert_behavior(self, invocation)

        invocation.start.assert_called_once_with()
        program.wait.assert_called_once_with()


if __name__ == '__main__':
    main()
