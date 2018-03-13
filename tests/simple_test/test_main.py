from collections import OrderedDict
from contextlib import contextmanager, redirect_stderr
import io
from pathlib import Path
import re
from sys import argv
from unittest import main as test_main, TestCase, TestSuite, TextTestRunner
from unittest.mock import call, MagicMock, Mock, patch

from simple_test.runner import Runner, BinaryNotFoundError, \
    BinaryNotExecutableError


PREFIX = 'simple_test.test_'


with patch(PREFIX + 'scanner.TestScanner') as TestScanner, \
        patch(PREFIX + 'cst.TestCST') as TestCST, \
        patch(PREFIX + 'symbol_table.TestSymbolTable') as TestSymbolTable, \
        patch(PREFIX + 'ast.TestAST') as TestAST:
    from simple_test.main import main


# TODO:  # pylint: disable=W0511
# These tests are a little fragile; forgetting to include one of these does not
# cause code coverage to go down (same for optional args). Also spelling of
# optional args is not enforced (either here or in the consuming TestCase).
# It would be optimal to fail a test if forgotten test_*.py are found in
# simple_test/. Similarly, a way to assert all optional args in main are tested
# would be swell.
ALL_TESTS = OrderedDict([('scanner', TestScanner),
                         ('cst', TestCST),
                         ('st', TestSymbolTable),
                         ('ast', TestAST)])


class TestMain(TestCase):
    def setUp(self):
        for test_case in ALL_TESTS.values():
            test_case.reset_mock()

    def test_main_no_args_runs_everything_with_defaults(self):
        self.assertMainRunsTests()

    def test_main_single_test(self):
        for name, test_class in ALL_TESTS.items():
            with self.subTest(name):
                self.assertMainRunsTests(tests=[test_class], args=[name])

    def test_main_bad_phase_errors(self):
        self.assertMainFailsWithStderr('invalid choice: \'foo\'', tests=[],
                                       args=['foo'])

    def test_main_with_sc_runs_everything(self):
        self.assertMainRunsTests(args=['--sc', 'other/sc'], sc='other/sc')

    def test_main_sc_not_exist_errors(self):
        error = BinaryNotFoundError('foo')
        self.assertMainFailsWithStderr('simple compiler does not exist: foo',
                                       tests=[], runner_create_raises=error)

    def test_main_sc_not_executable_errors(self):
        error = BinaryNotExecutableError('foo')
        msg = 'simple compiler is not executable: foo'
        self.assertMainFailsWithStderr(msg, tests=[],
                                       runner_create_raises=error)

    @patch('simple_test.main.warn')
    def test_main_sc_env_var_deprecation(self, warn):
        with fake_environ({'SC': 'other/sc'}):
            self.assertMainRunsTests(sc='other/sc')

        msg = 'The SC environment variable is deprecated. ' \
              'Use: run_harness --sc other/sc'
        warn.assert_called_once_with(msg, DeprecationWarning)

    def test_main_extra_args_passed_to_tests(self):
        extra_args = [(['--st-all-fives'], {'st_all_fives': True})]

        for args, config in extra_args:
            self.assertMainRunsTests(args=args, config=config)

    def assertMainFailsWithStderr(self, stderr, *args, **kwargs):
        f = io.StringIO()

        with redirect_stderr(f):
            with self.assertRaises(SystemExit):
                self.assertMainRunsTests(expect_exit=True, *args, **kwargs)

        self.assertIn(stderr, f.getvalue())

    def assertMainRunsTests(self, tests=None, args=None, sc='./sc',
                            verbosity=1, config=None,
                            runner_create_raises=None, expect_exit=False):
        if tests is None:
            tests = list(ALL_TESTS.values())
        if not args:
            args = []
        if not config:
            config = {}

        try:
            runner = Mock(Runner)
            test_suite = Mock(TestSuite)
            test_runner = Mock(TextTestRunner)
            created_tests = [MagicMock() for _ in tests]

            for test_class, created_test in zip(tests, created_tests):
                test_class.return_value = created_test

            with patch('simple_test.main.Runner') as Runner_, \
                    patch('simple_test.main.TextTestRunner') as TestRunner_, \
                    patch('simple_test.main.TestSuite') as TestSuite_:
                if runner_create_raises is None:
                    Runner_.create.return_value = runner
                else:
                    Runner_.create.side_effect = runner_create_raises

                TestRunner_.return_value = test_runner
                TestSuite_.return_value = test_suite

                with fake_argv(args):
                    main()

                Runner_.create.assert_called_once_with(Path(sc))
                TestRunner_.assert_called_once_with(verbosity=verbosity)
                TestSuite_.assert_called_once_with(created_tests)

            test_runner.run.assert_called_once_with(test_suite)

            for test_class in tests:
                subset = {'runner': runner, **config}
                self.assertCalledOnceWithKwargsSubset(test_class, subset)
        except SystemExit as e:
            if not expect_exit:
                self.fail("unexpected exit: {}".format(e))

            raise

    def assertCalledOnceWithKwargsSubset(self, f, subset):
        self.assertEqual(1, f.call_count,
                         "expected {} to only be called once".format(f))
        self.assertEqual(subset_call(**subset), f.call_args,
                         'expected call to be a kwargs subset')


@contextmanager
def fake_argv(new_argv):
    old_argv = argv[:]
    argv[:] = ['run_harness'] + new_argv

    try:
        yield
    finally:
        argv[:] = old_argv


@contextmanager
def fake_environ(new_environ):
    with patch('simple_test.main.environ', new=new_environ):
        yield


class _subset_call(type(call)):
    def __call__(self, *args, **kwargs):
        if self.name is None:
            return self.__class__(('', args, kwargs), name='()')

        name = self.name + '()'
        return self.__class__((self.name, args, kwargs), name=name,
                              parent=self)

    def __eq__(self, other):
        _, _, my_kwargs = self
        other_args, other_kwargs = other

        other_subset = call(*other_args,
                            **{k: v for k, v in other_kwargs.items()
                               if k in my_kwargs})

        return super().__eq__(other_subset)

    def __repr__(self):
        return re.sub(r'^call', 'subset_call', super().__repr__())


subset_call = _subset_call()


if __name__ == '__main__':
    test_main()
