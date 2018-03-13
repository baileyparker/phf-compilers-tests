# pylint: disable=W0613
from collections import namedtuple
from importlib import import_module
import json
from pathlib import Path
import re
from shutil import copyfile, rmtree
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import call

from simple_test.fixtures import discover_fixtures
from simple_test.runner import Runner


class PhaseTestBase(TestCase):
    """A base class that can integration test a FixturedTestCases.

    This provides the functionality of running a dummy compiler
    (see tests.simple_test.dummy_compiler), which effectively behaves as a mock
    (has stdout and stderr that are mocked and reports the arguments and stdin
    it receives) against a TestCase.
    """
    def test_tests_pass_for_dummy_compiler(self):
        # unittest discover will pick up this base class, so we skip it when it
        # is run to prevent any errors from uninitialized properties
        if type(self) == PhaseTestBase:  # pylint: disable=C0123
            return

        assert hasattr(self, 'cases_under_test'), \
            'specify cases_under_test in the PhaseTestBase child'
        assert hasattr(self, 'phase_name'), \
            'specify phase_name in the PhaseTestBase child'
        assert hasattr(self, 'sc_args'), \
            'specify sc_args in the PhaseTestBase child'

        with FakeCompilerContext() as fake_compiler:
            phase_name = self.phase_name  # noqa  # pylint: disable=E1101
            fixtures = [f for f in discover_fixtures()
                        if f.phase_name == phase_name]
            if not fixtures:
                self.fail("{} will not assert anything because there are no "
                          "*.{} phase files in fixtures/"
                          .format(self.__class__.__name__, phase_name))

            test_case_args = [{}] + getattr(self, 'extra_test_case_args', [])
            cases_under_test = self.cases_under_test  # noqa  # pylint: disable=E1101
            test_case_name = cases_under_test.split('.')[-1]

            for args in test_case_args:
                test_case_call = re.sub(r'^call', test_case_name,
                                        repr(call(**args)))
                for fixture in fixtures:
                    subtest_name = "{} - {}".format(test_case_call,
                                                    fixture.name)

                    with self.subTest(subtest_name):
                        self.assertTestCaseWithArgsPassesFixture(fake_compiler,
                                                                 fixture, args)

    def assertTestCaseWithArgsPassesFixture(self, fake_compiler, fixture,
                                            test_case_args):
        self.assertGoodFakeCompilerPasses(fake_compiler, fixture,
                                          test_case_args)

        if fixture.phase_file.has_error:
            self.assertMultipleErrorsPasses(fake_compiler, fixture,
                                            test_case_args)

        for for_stdin in (False, True):
            self.assertBadStdoutFakeCompilerFails(fake_compiler, fixture,
                                                  for_stdin, test_case_args)
            self.assertBadStderrFakeCompilerFails(fake_compiler, fixture,
                                                  for_stdin, test_case_args)

    def assertGoodFakeCompilerPasses(self, fake_compiler, fixture,
                                     test_case_args):
        phase_file = fixture.phase_file

        stderr = 'error: blah blah\n' if phase_file.has_error else ''
        output = (phase_file.stdout, stderr)
        self.run_fake_compiler(fake_compiler, fixture, output,
                               test_case_args=test_case_args)

        self.assertFakeCompilerHasCalls(fake_compiler, fixture, test_case_args)

    def assertMultipleErrorsPasses(self, fake_compiler, fixture,
                                   test_case_args):
        phase_file = fixture.phase_file
        assert phase_file.has_error, 'should only be called for error fixtures'

        stderr = 'error: foo bar\nerror: baz blah'
        output = (phase_file.stdout, stderr)
        self.run_fake_compiler(fake_compiler, fixture, output,
                               test_case_args=test_case_args)

        self.assertFakeCompilerHasCalls(fake_compiler, fixture,
                                        test_case_args)

    def assertBadStdoutFakeCompilerFails(self, fake_compiler, fixture,
                                         for_stdin, test_case_args):
        with self.assertRaises(AssertionError):
            phase_file = fixture.phase_file
            stdout = phase_file.stdout
            try:
                bad_stdout = chr((ord(stdout[0]) + 1) % 128) + stdout[1:]
            except IndexError:
                bad_stdout = 'a'

            stderr = 'error: \n' if phase_file.has_error else ''

            if not for_stdin:
                self.run_fake_compiler(fake_compiler, fixture,
                                       arg_output=(bad_stdout, stderr),
                                       stdin_output=(stdout, stderr),
                                       test_case_args=test_case_args)
            else:
                self.run_fake_compiler(fake_compiler, fixture,
                                       arg_output=(stdout, stderr),
                                       stdin_output=(bad_stdout, stderr),
                                       test_case_args=test_case_args)

        if not for_stdin:
            self.assertFakeCompilerHasArgumentCall(fake_compiler, fixture,
                                                   test_case_args)
        else:
            self.assertFakeCompilerHasStdinCall(fake_compiler, fixture,
                                                test_case_args)

    def assertBadStderrFakeCompilerFails(self, fake_compiler, fixture,
                                         for_stdin, test_case_args):
        with self.assertRaises(AssertionError):
            phase_file = fixture.phase_file
            stdout = phase_file.stdout
            stderr = 'error: \n' if phase_file.has_error else ''
            bad_stderr = 'error: \n' if not phase_file.has_error else ''

            if not for_stdin:
                self.run_fake_compiler(fake_compiler, fixture,
                                       arg_output=(stdout, bad_stderr),
                                       stdin_output=(stdout, stderr),
                                       test_case_args=test_case_args)
            else:
                self.run_fake_compiler(fake_compiler, fixture,
                                       arg_output=(stdout, stderr),
                                       stdin_output=(stdout, bad_stderr),
                                       test_case_args=test_case_args)

        if not for_stdin:
            self.assertFakeCompilerHasArgumentCall(fake_compiler, fixture,
                                                   test_case_args)
        else:
            self.assertFakeCompilerHasStdinCall(fake_compiler, fixture,
                                                test_case_args)

    def run_fake_compiler(self, fake_compiler, fixture, arg_output,
                          test_case_args, stdin_output=None):
        fake_compiler.fake_output(arg_output, stdin_output)

        # NOTE: python -m unittest discover is a little over eager. Namely,
        #       even if we tell it to stay within the tests/ directory, if the
        #       below import was up with the rest of the imports, it would be
        #       added to the list of tests to run. Obviously, when running the
        #       tests for the tests, you don't want to run the tests being
        #       tested (when running tests in tests/*, we don't want any of the
        #       test harness in simple_test/test_*.py to run).
        #       To avoid this (and keep the subclasses of PhaseTestBase as
        #       simple as possible), we have the subclasses specify the FQN of
        #       the TestCase class and we load it here. Since this is after
        #       the unittest package does its discovery, it won't slurp up this
        #       TestCase that we import.
        fqn = self.__class__.cases_under_test  # noqa  # pylint: disable=E1101
        cases_module, class_name = fqn.rsplit('.', 1)
        test_cases_class = getattr(import_module(cases_module), class_name)
        test_cases = test_cases_class(runner=Runner(fake_compiler.sc_path),
                                      **test_case_args)

        getattr(test_cases, "test_{}".format(fixture.name))()

    def assertFakeCompilerHasCalls(self, fake_compiler, fixture,
                                   test_case_args):
        self.assertFakeCompilerHasArgumentCall(fake_compiler, fixture,
                                               test_case_args)
        self.assertFakeCompilerHasStdinCall(fake_compiler, fixture,
                                            test_case_args)

    def assertFakeCompilerHasArgumentCall(self, fake_compiler, fixture,
                                          test_case_args):
        base_args = self.__class__.sc_args  # pylint: disable=E1101

        cwd = Path('.').resolve()
        sim_file_path = str(fixture.sim_file_path.relative_to(cwd))

        argument_call = FakeCompilerCall([*base_args, sim_file_path], '')

        self.assertEqual(argument_call, fake_compiler.get_first_input())

    def assertFakeCompilerHasStdinCall(self, fake_compiler, fixture,
                                       test_case_args):
        base_args = self.__class__.sc_args  # pylint: disable=E1101

        with fixture.sim_file_path.open() as f:
            stdin_call = FakeCompilerCall(list(base_args), f.read())

        self.assertEqual(stdin_call, fake_compiler.get_second_input())


FakeCompilerCall = namedtuple('FakeCompilerResult', ('args', 'stdin'))


class FakeCompilerContext:
    def __enter__(self):
        self.directory = Path(mkdtemp())

        # Setup dummy compiler
        directory = (Path(__file__) / '..').resolve()  # pylint: disable=E1101
        self.sc_path = self.directory / 'sc'
        copyfile(str(directory / 'dummy_compiler.py'), str(self.sc_path))
        self.sc_path.chmod(0o755)  # pylint: disable=E1101

        # Paths to input/output files for dummy compiler
        self.arguments_files = [
            self.directory / 'arguments',
            self.directory / 'arguments.2',
        ]
        self.stdin_files = [
            self.directory / 'stdin',
            self.directory / 'stdin.2',
        ]
        self.stdout_files = [
            self.directory / 'stdout',
            self.directory / 'stdout.2',
        ]
        self.stderr_files = [
            self.directory / 'stderr',
            self.directory / 'stderr.2',
        ]

        return self

    # NOTE: this is dependent on the test order (pass file as argument first,
    #       then pass file into stdin)
    def fake_output(self, arg_output, stdin_output=None):
        """
        Sets (stdout, stderr) for the fake compiler when run with the sim file
        passed as an argument and then when run with the sim file passed in as
        stdin. If the stdin_output tuple is not specified, the fake compiler
        will output the same stdout and stderr for both invocations.
        """
        if stdin_output is None:
            stdin_output = arg_output

        for p in [*self.arguments_files, *self.stdin_files]:
            try:
                p.unlink()
            except FileNotFoundError:
                pass

        output = zip(self.stdout_files, self.stderr_files,
                     (arg_output, stdin_output))
        for stdout_file, stderr_file, (stdout, stderr) in output:
            with stdout_file.open('w') as f:
                f.write(stdout)

            with stderr_file.open('w') as f:
                f.write(stderr)

    def get_first_input(self):
        """
        Gets the arguments and stdin from the first invocation of the fake
        compiler.
        """
        return self._get_input(0)

    def get_second_input(self):
        """
        Gets the arguments and stdin from the second invocation of the fake
        compiler.
        """
        return self._get_input(1)

    def _get_input(self, i):
        args, stdin = self.arguments_files[i], self.stdin_files[i]

        with args.open() as args_f, stdin.open() as stdin_f:
            return FakeCompilerCall(json.load(args_f), stdin_f.read())

    def __exit__(self, exc_type, exc_val, exc_tb):
        rmtree(str(self.directory))
