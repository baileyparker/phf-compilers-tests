from unittest import main, TestCase
from unittest.mock import Mock, patch

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.fixtures import Fixture, PhaseFile
from simple_test.subprocess import ProgramInvocation


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

            class DummyTestCase(FixturedTestCase, phase_name='foo'):
                def run_phase(self, sim_file, as_stdin=False):
                    return self.runner.foo(sim_file, as_stdin)

            # Assert test methods were added for each fixture (for that phase)
            test_case = DummyTestCase(runner)

            self.assertEqual(runner, test_case.runner)
            self.assertHasMethod('test_bar', test_case)
            self.assertHasMethod('test_cat', test_case)

            # Assert these methods properly delegate to assertFixture
            test_case.assertFixture = Mock()

            test_case.test_bar()  # pylint: disable=E1101
            test_case.assertFixture.assert_called_once_with(fixtures[0])
            test_case.assertFixture.reset_mock()

            test_case.test_cat()  # pylint: disable=E1101
            test_case.assertFixture.assert_called_once_with(fixtures[2])
            test_case.assertFixture.reset_mock()

    def test_subclassing_with_method_name_collision(self):
        with patch("{}.discover_fixtures".format(PREFIX)) as discover_fixtures:

            fixtures = [
                _make_fixture(name='foo', phase_name='bar'),
            ]

            discover_fixtures.return_value = fixtures

            error = r'replace existing test method: test_foo'
            with self.assertRaisesRegex(AssertionError, error):
                class DummyTestCase(FixturedTestCase,  # noqa  # pylint: disable=W0612
                                    phase_name='bar'):
                    def test_foo(self):
                        pass

                    def run_phase(self, sim_file, as_stdin=False):
                        raise NotImplementedError

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
        self.runner = Mock()
        self.test_case = FixturedTestCase(self.runner)
        self.test_case.run_phase = self.test_case.runner.foo

        self.sim_file_path = Mock()
        self.expected_stdout = Mock()
        self.phase_file = Mock(autospec=PhaseFile)
        self.phase_file.assert_behavior = Mock()
        self.stdout = Mock()
        self.stdout_str = 'stdout!'
        self.stderr = Mock()
        self.stderr_str = 'stderr!'
        self.invocation = Mock(spec=ProgramInvocation)
        self.invocation.cmd = 'some cmd'

        self.fixture = Mock(autospec=Fixture, sim_file_path=self.sim_file_path,
                            phase_file=self.phase_file)

        self.stdout.decode.return_value = self.stdout_str
        self.stderr.decode.return_value = self.stderr_str

    def test_assertFixture(self):
        self.test_case.assertFixtureAsArgument = Mock()
        self.test_case.assertFixtureAsStdin = Mock()

        self.test_case.assertFixture(self.fixture)

        self.test_case.assertFixtureAsArgument \
            .assert_called_once_with(self.fixture)
        self.test_case.assertFixtureAsStdin \
            .assert_called_once_with(self.fixture)

    def test_assertFixtureAsArgument(self):
        self.runner.foo.return_value = self.invocation
        self.test_case.assertFixtureBehavior = Mock()

        self.test_case.assertFixtureAsArgument(self.fixture)

        self.runner.foo.assert_called_once_with(self.sim_file_path)
        self.test_case.assertFixtureBehavior. \
            assert_called_once_with(self.phase_file, self.invocation)

    def test_assertFixtureAsStdin(self):
        self.runner.foo.return_value = self.invocation
        self.test_case.assertFixtureBehavior = Mock()

        self.test_case.assertFixtureAsStdin(self.fixture)

        self.runner.foo.assert_called_once_with(self.sim_file_path,
                                                as_stdin=True)
        self.test_case.assertFixtureBehavior \
            .assert_called_once_with(self.phase_file, self.invocation)

    def test_assertFixtureBehavior(self):
        self.test_case.assertFixtureBehavior(self.phase_file, self.invocation)

        self.phase_file.assert_behavior \
            .assert_called_once_with(self.test_case, self.invocation)

    def test_assertFixtureBehavior_adds_context(self):
        self.phase_file.assert_behavior.side_effect = AssertionError('P = NP')

        error = "while running: {}\n\n.*P = NP".format(self.invocation.cmd)
        with self.assertRaisesRegex(AssertionError, error):
            self.test_case.assertFixtureBehavior(self.phase_file,
                                                 self.invocation)


if __name__ == '__main__':
    main()
