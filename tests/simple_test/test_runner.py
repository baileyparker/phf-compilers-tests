from collections import OrderedDict
from pathlib import Path
from subprocess import CompletedProcess, DEVNULL, PIPE
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from simple_test.runner import run_simple_scanner, run_simple_cst


PREFIX = 'simple_test.runner'


class TestRunner(TestCase):
    def test_run_simple_scanner(self):
        self.assertRunsSimple(run_simple_scanner, ['-s'])

    def test_run_simple_cst(self):
        self.assertRunsSimple(run_simple_cst, ['-c'])

    def assertRunsSimple(self, runner, args):
        with patch("{}.run".format(PREFIX)) as self.subprocess_run, \
             patch("{}.shell_quote".format(PREFIX)) as self.shell_quote, \
             patch("{}.environ".format(PREFIX), new={}) as self.environ:

            # TODO: test relative_to raises ValueError  # pylint: disable=W0511
            self.assertRunsSimpleWithArgument(runner, args)
            self.assertRunsSimpleWithArgument(runner, args, sc_path='./foo')
            self.assertRunsSimpleAsStdin(runner, args)
            self.assertRunsSimpleAsStdin(runner, args, sc_path='./foo')

    def setup_subprocess(self, sc_path=None):
        sim_file = MagicMock()
        relative_sim_file = MagicMock()
        relative_sim_file.__str__.return_value = 'foo/bar.sim'
        sim_file.relative_to.side_effect = \
            lambda p: relative_sim_file if p == Path('.').resolve() else None

        stdout, stderr = Mock(), Mock()
        fake_args = ('a', 'b')
        quoted_args = OrderedDict([('a', 'c'), ('b', 'd')])
        completed_process = Mock(CompletedProcess, args=fake_args,
                                 stdout=stdout, stderr=stderr)

        if sc_path:
            self.environ['SC'] = sc_path
        elif 'SC' in self.environ:
            del self.environ['SC']

        self.subprocess_run.reset_mock()
        self.shell_quote.reset_mock()
        self.subprocess_run.return_value = completed_process
        self.shell_quote.side_effect = lambda x: quoted_args[x]

        cmd = ' '.join(quoted_args.values())

        return sim_file, relative_sim_file, cmd, stdout, stderr

    def assertRunsSimpleWithArgument(self, runner, args, sc_path=None):
        sim_file, relative_sim_file, cmd, stdout, stderr = \
            self.setup_subprocess(sc_path)

        result = runner(sim_file)

        self.subprocess_run \
            .assert_called_once_with([sc_path if sc_path else './sc', *args,
                                      str(relative_sim_file)], stdout=PIPE,
                                     stderr=PIPE, stdin=DEVNULL)
        self.assertEqual(cmd, result.cmd)
        self.assertEqual(stdout, result.stdout)
        self.assertEqual(stderr, result.stderr)

    def assertRunsSimpleAsStdin(self, runner, args, sc_path=None):
        sim_file, relative_sim_file, cmd, stdout, stderr = \
            self.setup_subprocess(sc_path)

        # Wire up relative_sim_file so we can call .open() on it
        fake_file = MagicMock()
        fake_file_context = MagicMock()
        fake_file_context.__enter__.return_value = fake_file
        relative_sim_file.open.return_value = fake_file_context

        result = runner(sim_file, as_stdin=True)

        relative_sim_file.open.assert_called_once_with()
        self.subprocess_run \
            .assert_called_once_with([sc_path if sc_path else './sc', *args],
                                     stdout=PIPE, stderr=PIPE, stdin=fake_file)
        self.assertEqual("{} < {}".format(cmd, relative_sim_file), result.cmd)
        self.assertEqual(stdout, result.stdout)
        self.assertEqual(stderr, result.stderr)


if __name__ == '__main__':
    main()
