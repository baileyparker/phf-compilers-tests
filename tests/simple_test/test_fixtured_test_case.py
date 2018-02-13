from unittest import main, TestCase
from unittest.mock import Mock, patch

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.fixtures import Fixture, PhaseFile
from simple_test.runner import Result


PREFIX = 'simple_test.fixtured_test_case'


class TestFixturedTestCase(TestCase):
    def test_subclassing_adds_fixture_test_methods(self):
        with patch("{}.discover_fixtures".format(PREFIX)) as discover_fixtures:

            fixtures = [
                _make_fixture(name='bar', phase_name='foo'),
                _make_fixture(name='baz', phase_name='bat'),
                _make_fixture(name='cat', phase_name='foo'),
            ]
            runner = Mock()

            discover_fixtures.return_value = fixtures

            class DummyTestCase(FixturedTestCase,
                                phase_name='foo', run_simple=runner):
                pass

            # Assert test methods were added for each fixture (for that phase)
            test_case = DummyTestCase()
            self.assertHasMethod('test_bar', test_case)
            self.assertHasMethod('test_cat', test_case)

            # Assert these methods properly delegate to assertFixture
            test_case.assertFixture = Mock()

            test_case.test_bar()  # pylint: disable=E1101
            test_case.assertFixture.assert_called_once_with(fixtures[0],
                                                            runner)
            test_case.assertFixture.reset_mock()

            test_case.test_cat()  # pylint: disable=E1101
            test_case.assertFixture.assert_called_once_with(fixtures[2],
                                                            runner)
            test_case.assertFixture.reset_mock()

    def test_subclassing_with_method_name_collision(self):
        with patch("{}.discover_fixtures".format(PREFIX)) as discover_fixtures:

            fixtures = [
                _make_fixture(name='foo', phase_name='bar'),
            ]
            runner = Mock()  # pylint: disable=W0612

            discover_fixtures.return_value = fixtures

            error = r'replace existing test method: test_foo'
            with self.assertRaisesRegex(AssertionError, error):
                class DummyTestCase(FixturedTestCase,  # noqa  # pylint: disable=W0612
                                    phase_name='bar', run_simple=runner):
                    def test_foo(self):
                        pass

    def assertHasMethod(self, name, obj):
        if not callable(getattr(obj, name, None)):
            self.fail("{}.{} should be a method".format(obj.__class__.__name__,
                                                        name))


def _make_fixture(name, phase_name):
    fixture = Mock(autospec=Fixture, phase_name=phase_name)
    fixture.name = name
    return fixture


class TestFixturedTestCaseAssertions(TestCase):
    def setUp(self):
        self.test_case = FixturedTestCase()

        self.sim_file_path = Mock()
        self.expected_stdout = Mock()
        self.phase_file = Mock(autospec=PhaseFile, stdout=self.expected_stdout)
        self.stdout = Mock()
        self.stdout_str = 'stdout!'
        self.stderr = Mock()
        self.stderr_str = 'stderr!'
        self.result = Mock(autospec=Result, cmd='result cmd',
                           stdout=self.stdout, stderr=self.stderr)

        self.fixture = Mock(autospec=Fixture, sim_file_path=self.sim_file_path,
                            phase_file=self.phase_file)
        self.runner = Mock()

        self.stdout.decode.return_value = self.stdout_str
        self.stderr.decode.return_value = self.stderr_str

    def test_assertFixture(self):
        self.test_case.assertFixtureAsArgument = Mock()
        self.test_case.assertFixtureAsStdin = Mock()

        self.test_case.assertFixture(self.fixture, self.runner)

        self.test_case.assertFixtureAsArgument \
            .assert_called_once_with(self.fixture, self.runner)
        self.test_case.assertFixtureAsStdin. \
            assert_called_once_with(self.fixture, self.runner)

    def test_assertFixtureAsArgument(self):
        self.runner.return_value = self.result
        self.test_case.assertFixtureOutput = Mock()

        self.test_case.assertFixtureAsArgument(self.fixture, self.runner)

        self.runner.assert_called_once_with(self.sim_file_path)
        self.test_case.assertFixtureOutput. \
            assert_called_once_with(self.phase_file, self.result)

    def test_assertFixtureAsStdin(self):
        self.runner.return_value = self.result
        self.test_case.assertFixtureOutput = Mock()

        self.test_case.assertFixtureAsStdin(self.fixture, self.runner)

        self.runner.assert_called_once_with(self.sim_file_path, as_stdin=True)
        self.test_case.assertFixtureOutput \
            .assert_called_once_with(self.phase_file, self.result)

    def test_assertFixtureOutput(self):
        self.test_case.assertFixtureStdout = Mock()
        self.test_case.assertFixtureStderr = Mock()

        self.test_case.assertFixtureOutput(self.phase_file, self.result)

        self.test_case.assertFixtureStdout \
            .assert_called_once_with(self.phase_file, self.result)
        self.test_case.assertFixtureStderr \
            .assert_called_once_with(self.phase_file, self.result)

    def test_assertFixtureOutput_adds_context(self):
        assertion_error = AssertionError('P = NP')
        self.test_case.assertFixtureStdout = Mock(side_effect=assertion_error)
        self.test_case.assertFixtureStderr = Mock(side_effect=assertion_error)

        error = "while running: {}\n\n.*P = NP".format(self.result.cmd)
        with self.assertRaisesRegex(AssertionError, error):
            self.test_case.assertFixtureOutput(self.phase_file, self.result)

    def test_assertFixtureStdout(self):
        self.test_case.assertStdoutEqual = Mock()

        self.test_case.assertFixtureStdout(self.phase_file, self.result)

        self.test_case.assertStdoutEqual \
            .assert_called_once_with(self.expected_stdout, self.stdout,
                                     self.stderr)

    def test_assertFixtureStderr_expected_error(self):
        self.assertStderrAssertionSucceeds(True, 'error: stuff\n')

    def test_assertFixtureStderr_unexpected_and_no_error(self):
        self.assertStderrAssertionSucceeds(False, '')

    def assertStderrAssertionSucceeds(self, has_error, stderr):
        self.phase_file.has_error = has_error
        self.stderr.decode.return_value = stderr

        self.test_case.assertFixtureStderr(self.phase_file, self.result)
        self.stderr.decode.assert_called_once_with('utf8')

    def test_assertFixtureStderr_expected_but_no_error(self):
        stderr = ''
        error = 'at least one error.*\n\nstdout.*:\n\n{}\n\nstderr.*:\n\n{}' \
            .format(self.stdout_str, stderr)

        self.assertStderrAssertionFails(True, stderr, error)

    def test_assertFixtureStderr_unexpected_error(self):
        stderr = 'error: unexpected!\n'
        error = 'expected no error.*\n\nstdout.*:\n\n{}\n\nstderr.*:\n\n{}' \
            .format(self.stdout_str, stderr)

        self.assertStderrAssertionFails(False, stderr, error)

    def assertStderrAssertionFails(self, has_error, stderr, assertion_regex):
        with self.assertRaisesRegex(AssertionError, assertion_regex):
            self.phase_file.has_error = has_error
            self.stderr.decode.return_value = stderr

            self.test_case.assertFixtureStderr(self.phase_file, self.result)

        self.stdout.decode.assert_called_once_with('utf8')
        self.stderr.decode.assert_called_once_with('utf8')

    def test_assertStdoutEqual_equal(self):
        value = Mock()
        encoded_value = Mock()
        encoded_value.decode.return_value = value

        self.test_case.assertStdoutEqual(value, encoded_value, self.stderr)
        encoded_value.decode.assert_called_with('utf8')

    def test_assertStdoutEqual_not_equal(self):
        with patch("{}.unified_diff".format(PREFIX)) as unified_diff, \
             patch("{}.sys.stdout.isatty".format(PREFIX)) as isatty:
            expected = Mock()
            actual = Mock()
            actual_str = Mock()

            actual.decode.return_value = actual_str
            unified_diff.return_value = 'diff return!'

            error = "wrong stdout:\n{}\n\nstderr was:\n\n{}" \
                .format(unified_diff.return_value, self.stderr_str)
            with self.assertRaisesRegex(AssertionError, error):
                self.test_case.assertStdoutEqual(expected, actual, self.stderr)

            actual.decode.assert_called_with('utf8')
            self.stderr.decode.assert_called_with('utf8')
            unified_diff.assert_called_with(expected, actual_str,
                                            fromfile='expected_stdout',
                                            tofile='actual_stdout',
                                            color=isatty.return_value)


if __name__ == '__main__':
    main()
