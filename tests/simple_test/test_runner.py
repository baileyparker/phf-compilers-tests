from asyncio import SelectorEventLoop
from functools import partial
from pathlib import Path
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from simple_test.runner import Runner, BinaryNotFoundError, \
    BinaryNotExecutableError


PREFIX = 'simple_test.runner'


class TestRunner(TestCase):
    def setUp(self):
        self.loop = Mock()
        self.sc_path = Mock(spec=Path)
        self.timeout = 6.0
        self.remote = 'user@host'

        self.runner = Runner(self.loop, self.sc_path, timeout=self.timeout,
                             remote=self.remote)

    @patch('simple_test.runner.set_event_loop')
    @patch('simple_test.runner.SelectorEventLoop')
    @patch('simple_test.runner.Runner')
    @patch('simple_test.runner.os')
    def test_create(self, os, Runner_, SelectorEventLoop_, set_event_loop):
        path = 'good/path'
        sc_path = MagicMock(spec=Path)
        sc_path.__str__.return_value = path
        sc_path.exists.return_value = True
        os.access.return_value = True

        runner = Mock(spec=Runner)
        loop = Mock(spec=SelectorEventLoop)
        timeout, remote = Mock(), Mock()

        SelectorEventLoop_.return_value = loop
        Runner_.return_value = runner

        create = partial(Runner.create.__func__, Runner_)
        self.assertEqual(runner, create(sc_path, timeout, remote))

        sc_path.exists.assert_called_once_with()
        os.access.assert_called_once_with(path, os.X_OK)

        SelectorEventLoop_.assert_called_once_with()
        set_event_loop.assert_called_once_with(loop)
        Runner_.assert_called_once_with(loop, sc_path, timeout=timeout,
                                        remote=remote)

    def test_create_fails_if_not_exist(self):
        path = 'bad/path'
        sc_path = MagicMock(Path)
        sc_path.__str__.return_value = path
        sc_path.exists.return_value = False

        with self.assertRaises(BinaryNotFoundError) as cm:
            Runner.create(sc_path)

        self.assertEqual(sc_path, cm.exception.filename)

    @patch('simple_test.runner.os')
    def test_create_fails_if_not_executable(self, os):
        path = 'bad/path'
        sc_path = MagicMock(Path)
        sc_path.__str__.return_value = path
        sc_path.exists.return_value = True
        os.access.return_value = False

        with self.assertRaises(BinaryNotExecutableError) as cm:
            Runner.create(sc_path)

        self.assertEqual(sc_path, cm.exception.filename)

        sc_path.exists.assert_called_once_with()
        os.access.assert_called_once_with(path, os.X_OK)

    def test_context_manager(self):
        with self.runner:
            pass

        self.loop.close.expect_called_once_with()

    def test_context_manager_raises(self):
        self.loop.close.side_effect = RuntimeError('loop already closed')

        with self.runner:
            pass

        self.loop.close.expect_called_once_with()

    def test_run_simple_scanner(self):
        self.assertInvokesSimple(self.runner.run_scanner, ['-s'])

    def test_run_simple_cst(self):
        self.assertInvokesSimple(self.runner.run_cst, ['-c'])

    def test_run_simple_symbol_table(self):
        self.assertInvokesSimple(self.runner.run_symbol_table, ['-t'])

    def test_run_simple_ast(self):
        self.assertInvokesSimple(self.runner.run_ast, ['-a'])

    def test_run_simple_interpreter(self):
        self.assertInvokesSimple(self.runner.run_interpreter, ['-i'])

    def assertInvokesSimple(self, runner, args):
        self.assertInvokesSimpleAsStdin(runner, args)
        self.assertInvokesSimpleAsArgument(runner, args)  # noqa  # pylint: disable=E1120

    def assertInvokesSimpleAsStdin(self, runner, args):
        sim_file = Mock()
        self.assertInvokesSimpleWith(runner, args, sim_file, stdin=sim_file,  # noqa  # pylint: disable=E1120
                                     as_stdin=True)

    @patch('simple_test.runner.relative_to_cwd')
    def assertInvokesSimpleAsArgument(self, runner, args, relative_to_cwd):
        sim_file = Mock()
        sim_file_path = Mock()
        relative_to_cwd.return_value = sim_file_path

        self.assertInvokesSimpleWith(runner, [*args, sim_file_path], sim_file)  # noqa  # pylint: disable=E1120
        relative_to_cwd.assert_called_once_with(sim_file)

    @patch('simple_test.runner.ProgramInvocation')
    def assertInvokesSimpleWith(self, runner, args, sim_file,
                                ProgramInvocation, stdin=None, as_stdin=False):
        invocation = Mock()
        ProgramInvocation.return_value = invocation

        self.assertEqual(invocation, runner(sim_file, as_stdin))
        ProgramInvocation.assert_called_once_with(self.loop, self.sc_path,
                                                  args, stdin=stdin,
                                                  timeout=self.timeout)


if __name__ == '__main__':
    main()
