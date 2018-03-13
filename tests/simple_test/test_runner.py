from collections import OrderedDict
from pathlib import Path
from subprocess import CompletedProcess, DEVNULL, PIPE
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from simple_test.runner import Runner, BinaryNotFoundError, \
    BinaryNotExecutableError


PREFIX = 'simple_test.runner'


class TestRunner(TestCase):
    def setUp(self):
        self.sc_path = Path('path/to/sc')
        self.runner = Runner(self.sc_path)

    @patch('simple_test.runner.os')
    def test_create(self, os):
        path = 'good/path'
        sc_path = MagicMock(Path)
        sc_path.__str__.return_value = path
        sc_path.exists.return_value = True
        os.access.return_value = True

        self.assertEqual(sc_path, Runner.create(sc_path)._sc_path)  # noqa  # pylint: disable=W0212

        sc_path.exists.assert_called_once_with()
        os.access.assert_called_once_with(path, os.X_OK)

    def test_create_fails_if_not_exist(self):
        path = 'good/path'
        sc_path = MagicMock(Path)
        sc_path.__str__.return_value = path
        sc_path.exists.return_value = False

        with self.assertRaises(BinaryNotFoundError) as cm:
            Runner.create(sc_path)

        self.assertEqual(sc_path, cm.exception.filename)

    @patch('simple_test.runner.os')
    def test_create_fails_if_not_executable(self, os):
        path = 'good/path'
        sc_path = MagicMock(Path)
        sc_path.__str__.return_value = path
        sc_path.exists.return_value = True
        os.access.return_value = False

        with self.assertRaises(BinaryNotExecutableError) as cm:
            Runner.create(sc_path)

        self.assertEqual(sc_path, cm.exception.filename)

        sc_path.exists.assert_called_once_with()
        os.access.assert_called_once_with(path, os.X_OK)

    def test_run_simple_scanner(self):
        self.assertRunsSimple(self.runner.run_scanner, ['-s'])

    def test_run_simple_cst(self):
        self.assertRunsSimple(self.runner.run_cst, ['-c'])

    def test_run_simple_symbol_table(self):
        self.assertRunsSimple(self.runner.run_symbol_table, ['-t'])

    def assertRunsSimple(self, runner, args):
        with patch("{}.run".format(PREFIX)) as self.subprocess_run, \
             patch("{}.shell_quote".format(PREFIX)) as self.shell_quote:

            for raises in (False, True):
                self.assertRunsSimpleWithArgument(runner, args,
                                                  relative_to_raises=raises)
                self.assertRunsSimpleAsStdin(runner, args,
                                             relative_to_raises=raises)

    def setup_subprocess(self, relative_to_raises=False):
        sim_file = MagicMock()
        sim_file.__str__.return_value = 'non_relative_path.sim'
        relative_sim_file = MagicMock()
        relative_sim_file.__str__.return_value = 'foo/bar.sim'

        if not relative_to_raises:
            cwd = Path('.').resolve()

            sim_file.relative_to.side_effect = \
                lambda p: relative_sim_file if p == cwd else None
        else:
            sim_file.relative_to.side_effect = ValueError('relative_to')

        stdout, stderr = Mock(), Mock()
        fake_args = ('a', 'b')
        quoted_args = OrderedDict([('a', 'c'), ('b', 'd')])
        completed_process = Mock(CompletedProcess, args=fake_args,
                                 stdout=stdout, stderr=stderr)

        self.subprocess_run.reset_mock()
        self.shell_quote.reset_mock()
        self.subprocess_run.return_value = completed_process
        self.shell_quote.side_effect = lambda x: quoted_args[x]

        cmd = ' '.join(quoted_args.values())

        return sim_file, relative_sim_file, cmd, stdout, stderr

    def assertRunsSimpleWithArgument(self, runner, args,
                                     relative_to_raises=False):
        sim_file, relative_sim_file, cmd, stdout, stderr = \
            self.setup_subprocess(relative_to_raises)
        last_arg = sim_file if relative_to_raises else relative_sim_file

        result = runner(sim_file)

        self.subprocess_run \
            .assert_called_once_with([str(self.sc_path), *args, str(last_arg)],
                                     stdout=PIPE, stderr=PIPE, stdin=DEVNULL)
        self.assertEqual(cmd, result.cmd)
        self.assertEqual(stdout, result.stdout)
        self.assertEqual(stderr, result.stderr)

    def assertRunsSimpleAsStdin(self, runner, args, relative_to_raises=False):
        sim_file, relative_sim_file, cmd, stdout, stderr = \
            self.setup_subprocess(relative_to_raises)
        redirected_file = sim_file if relative_to_raises else relative_sim_file

        # Wire up relative_sim_file so we can call .open() on it
        fake_file = MagicMock()
        fake_file_context = MagicMock()
        fake_file_context.__enter__.return_value = fake_file
        redirected_file.open.return_value = fake_file_context

        result = runner(sim_file, as_stdin=True)

        redirected_file.open.assert_called_once_with()
        self.subprocess_run \
            .assert_called_once_with([str(self.sc_path), *args], stdout=PIPE,
                                     stderr=PIPE, stdin=fake_file)
        self.assertEqual("{} < {}".format(cmd, redirected_file), result.cmd)
        self.assertEqual(stdout, result.stdout)
        self.assertEqual(stderr, result.stderr)


if __name__ == '__main__':
    main()
