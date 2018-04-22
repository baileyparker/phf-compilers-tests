from asyncio import create_subprocess_exec, SelectorEventLoop, set_event_loop, TimeoutError, wait_for  # noqa  # pylint: disable=W0622,C0301
from asyncio.subprocess import DEVNULL, PIPE
from pathlib import Path
from signal import SIGKILL
import sys
from unittest import main, TestCase
from unittest.mock import Mock, patch

from simple_test.subprocess import ProgramInvocation, InteractiveProgram, \
    CompletedProgram


class EventLoopMixin:
    def setUp(self):
        self.loop = SelectorEventLoop()
        # NOTE: https://stackoverflow.com/q/49952817/568785
        set_event_loop(self.loop)

    def tearDown(self):
        try:
            self.loop.close()
        except RuntimeError:
            pass


class TestSubprocess(EventLoopMixin, TestCase):
    def test_noninteractive(self):
        args = ['-c',
                'import sys;'
                'sys.stdout.write(\'foo\\n\');'
                'sys.stderr.write(\'bar\\n\');'
                'sys.exit(42)']

        invocation = ProgramInvocation(self.loop, Path(sys.executable), args)
        completed = invocation.run()

        self.assertEqual('foo\n', completed.stdout)
        self.assertEqual('bar\n', completed.stderr)
        self.assertEqual(42, completed.returncode)

    def test_interactive(self):
        args = ['-c',
                'import sys;'
                'sys.stdout.write(\'foo\\n\');'
                'sys.stderr.write(\'bar\\n\');'
                'sys.stdout.write(input() + \'\\n\');'
                'sys.stdout.write(\'a\\n\');'
                'sys.stderr.write(\'b\\n\');'
                'sys.exit(42)']

        invocation = ProgramInvocation(self.loop, Path(sys.executable), args)
        program = invocation.start()

        self.assertEqual('foo\n', program.read_line())
        self.assertEqual('bar\n', program.read_error_line())

        program.write_line('baz\n')
        self.assertEqual('baz\n', program.read_line())

        completed = program.wait()
        self.assertEqual('a\n', completed.stdout)
        self.assertEqual('b\n', completed.stderr)
        self.assertEqual(42, completed.returncode)

    def test_interactive_timeout(self):
        invocation = ProgramInvocation(self.loop, Path('sleep'), ['10'],
                                       timeout=0.1)
        program = invocation.start()

        with self.assertRaises(TimeoutError):
            program.read_line()


class TestInteractiveProgram(EventLoopMixin, TestCase):
    @patch('simple_test.subprocess.CompletedProgram')
    def test_wait(self, CompletedProgram_):
        args = [sys.executable, '-c',
                'import sys;'
                'sys.stdout.write(\'foo\\n\');'
                'sys.stderr.write(\'bar\\n\');'
                'sys.exit(42)']

        program, _, cmd = self._mock_program(args, 10)

        completed_program = Mock(spec=CompletedProgram)
        CompletedProgram_.return_value = completed_program

        self.assertEqual(completed_program, program.wait())
        CompletedProgram_.assert_called_once_with(cmd, 'foo\n', 'bar\n', 42)

    def test_wait_timeout(self):
        self.assertTimesOut('wait')

    def test_write_line(self):
        args = [sys.executable, '-c', 'print(input())']
        program, process, _ = self._mock_program(args, 10, stdin=True)

        line = 'foo bar\n'
        program.write_line(line)

        stdout, _ = _run_async(self.loop, process.communicate(), 0.5)
        self.assertEqual(line, stdout.decode('utf-8'))

    def test_read_line(self):
        program, process, _ = self._mock_program(['printf', 'Abc\nDef\n'], 10)

        self.assertEqual('Abc\n', program.read_line())
        self.assertEqual('Def\n', program.read_line())

        process.kill()
        _wait_process(self.loop, process)

    def test_read_line_timeout(self):
        self.assertTimesOut('read_line')

    def test_read_error_line(self):
        args = [sys.executable, '-c',
                'import sys; print(\'Abc\\nDef\\n\', file=sys.stderr)']
        program, process, _ = self._mock_program(args, 10)

        self.assertEqual('Abc\n', program.read_error_line())
        self.assertEqual('Def\n', program.read_error_line())

        _wait_process(self.loop, process)

    def test_read_error_line_timeout(self):
        self.assertTimesOut('read_error_line')

    def assertTimesOut(self, f):
        program, process, _ = self._mock_program(['sleep', '10'], 0.001)

        with self.assertRaises(TimeoutError):
            getattr(program, f)()

        try:
            _run_async(self.loop, process.communicate(), 1)
        except TimeoutError:
            self.fail('process was not killed in time')

        self.assertEqual(-SIGKILL, process.returncode,
                         'process must be killed')

    def _mock_program(self, args, timeout, stdin=False):
        cmd = Mock()
        process = self._mock_process(args, stdin)
        program = InteractiveProgram(process, cmd, timeout, self.loop)

        return program, process, cmd

    def _mock_process(self, args, stdin=False):
        async_proc = create_subprocess_exec(*args,
                                            stdin=PIPE if stdin else DEVNULL,
                                            stdout=PIPE, stderr=PIPE,
                                            loop=self.loop)
        process = _run_async(self.loop, async_proc, 0.5)
        if stdin:
            process.stdin.transport.set_write_buffer_limits(0)
        return process


def _run_async(loop, awaitable, timeout: float):
    timed_awaitable = wait_for(awaitable, timeout=timeout, loop=loop)
    return loop.run_until_complete(timed_awaitable)


def _wait_process(loop, process):
    _run_async(loop, process.communicate(), 0.5)


class TestCompletedProgram(TestCase):
    def test_attributes(self):
        cmd, stdout, stderr, returncode = Mock(), Mock(), Mock(), Mock()
        program = CompletedProgram(cmd, stdout, stderr, returncode)

        self.assertEqual(cmd, program.cmd)
        self.assertEqual(stdout, program.stdout)
        self.assertEqual(stderr, program.stderr)
        self.assertEqual(returncode, program.returncode)

    def test_failed_zero_returncode(self):
        cmd, stdout = Mock(), Mock()
        program = CompletedProgram(cmd, stdout, '', 0)

        self.assertFalse(program.failed)

    def test_failed_zero_returncode_but_stderr(self):
        cmd, stdout = Mock(), Mock()
        program = CompletedProgram(cmd, stdout, 'error: stuff', 0)

        self.assertTrue(program.failed)

    def test_failed_nonzero_returncode(self):
        cmd, stdout = Mock(), Mock()
        program = CompletedProgram(cmd, stdout, '', 42)

        self.assertTrue(program.failed)

    def test_failed_nonzero_returncode_and_stderr(self):
        cmd, stdout = Mock(), Mock()
        program = CompletedProgram(cmd, stdout, 'error: stuff', 42)

        self.assertTrue(program.failed)


if __name__ == '__main__':
    main()
