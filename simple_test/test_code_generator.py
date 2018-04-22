"""Tests for the codegenerator of the simple compiler."""

from pathlib import Path

from simple_test.fixtures import Fixture
from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.phase_file import StopTestError
from simple_test.runner import CompilationError
from simple_test.subprocess import ProgramInvocation


class TestCodeGenerator(FixturedTestCase, phase_name='run'):
    """Tests for the interpreter of the simple compiler."""

    def setUp(self):
        super().setUp()

        # TODO: XXX: uncomment this
        # assert self.remote is not None, 'must specify --remote'

    def run_phase(self, fixture: Fixture,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the codegen of the simple compiler.
        """
        phase_file = fixture.phase_file

        try:
            invocation = self.runner.run_compiler(fixture.sim_file_path,
                                                  as_stdin)
            phase_file.handle_compilation_error(self, None)
            return invocation
        except CompilationError as e:
            phase_file.handle_compilation_error(self, e)

    def assertFixture(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file produces the expected output.
        """

        # NOTE: Marc has been quoted in office hours as saying that they only
        #       test the stdin functionality of the compiler. For now, this
        #       will do.
        self.assertFixtureAsStdin(fixture)

    def assertFixtureAsStdin(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file as stdin produces the expected output.
        """
        try:
            invocation = self.run_phase(fixture, as_stdin=True)
            self.assertFixtureBehavior(fixture.phase_file, invocation)
        except StopTestError:
            pass
