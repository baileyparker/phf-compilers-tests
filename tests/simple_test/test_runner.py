from collections import OrderedDict
from itertools import product
from pathlib import Path
from subprocess import CompletedProcess, DEVNULL, PIPE
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from simple_test.runner import Runner, BinaryNotFoundError, \
    BinaryNotExecutableError


PREFIX = 'simple_test.runner'


class TestRunner(TestCase):
    def setUp(self):
        path = 'path/to/sc'
        self.sc_path = MagicMock(spec=Path)
        self.sc_path.__str__.return_value = path

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

    def test_run_simple_ast(self):
        self.assertRunsSimple(self.runner.run_ast, ['-a'])

    def assertRunsSimple(self, runner, args):
        with patch("{}.run".format(PREFIX)) as self.subprocess_run, \
             patch("{}.shell_quote".format(PREFIX)) as self.shell_quote:

            for raises, sc_raises in product((False, True), repeat=2):
                self.assertRunsSimpleBothWays(runner, args, raises, sc_raises)

    def assertRunsSimpleBothWays(self, runner, args, raises, sc_raises):
        name = "raises={}, sc_raises={}".format(raises, sc_raises)
        with self.subTest("with argument, {}".format(name)):
            self.assertRunsSimpleWithArgument(runner, args,
                                              relative_to_raises=raises,
                                              sc_raises=sc_raises)

        with self.subTest("as stdin, {}".format(name)):
            self.assertRunsSimpleAsStdin(runner, args,
                                         relative_to_raises=raises,
                                         sc_raises=sc_raises)

    def setup_subprocess(self, relative_to_raises=False,
                         sc_relative_to_raises=False):
        cwd = Path.cwd()

        sim_file = MagicMock()
        sim_file.__str__.return_value = 'non_relative_path.sim'
        relative_sim_file = MagicMock()
        relative_sim_file.__str__.return_value = 'foo/bar.sim'

        if not relative_to_raises:
            sim_file.relative_to.side_effect = \
                lambda p: relative_sim_file if p == cwd else None
        else:
            sim_file.relative_to.side_effect = ValueError('relative_to')

        stdout, stderr = Mock(), Mock()
        quoted_args = OrderedDict([('a', 'c'), ('b', 'd')])
        fake_args = tuple(['full/path/to/sc', *quoted_args.keys()])
        completed_process = Mock(CompletedProcess, args=fake_args,
                                 stdout=stdout, stderr=stderr)

        self.sc_path.reset_mock()
        self.subprocess_run.reset_mock()
        self.shell_quote.reset_mock()

        quoted_sc_path = 'quoted/sc/path'

        if not sc_relative_to_raises:
            unquoted_sc_path = Path('relative/path/to/sc')
            self.sc_path.relative_to.side_effect = \
                lambda p: unquoted_sc_path if p == cwd else None
        else:
            unquoted_sc_path = str(self.sc_path)
            self.sc_path.relative_to.side_effect = ValueError('relative_to')

        self.subprocess_run.return_value = completed_process
        self.shell_quote.side_effect = \
            lambda x: quoted_sc_path if x == str(unquoted_sc_path) \
            else quoted_args[x]

        cmd = ' '.join([quoted_sc_path, *quoted_args.values()])

        return sim_file, relative_sim_file, cmd, stdout, stderr

    def assertRunsSimpleWithArgument(self, runner, args,
                                     relative_to_raises=False,
                                     sc_raises=False):
        sim_file, relative_sim_file, cmd, stdout, stderr = \
            self.setup_subprocess(relative_to_raises, sc_raises)
        last_arg = sim_file if relative_to_raises else relative_sim_file

        result = runner(sim_file)

        self.subprocess_run \
            .assert_called_once_with([str(self.sc_path), *args, str(last_arg)],
                                     stdout=PIPE, stderr=PIPE, stdin=DEVNULL)
        self.assertEqual(cmd, result.cmd)
        self.assertEqual(stdout, result.stdout)
        self.assertEqual(stderr, result.stderr)

    def assertRunsSimpleAsStdin(self, runner, args, relative_to_raises=False,
                                sc_raises=False):
        sim_file, relative_sim_file, cmd, stdout, stderr = \
            self.setup_subprocess(relative_to_raises, sc_raises)
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
