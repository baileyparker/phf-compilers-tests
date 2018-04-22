"""Tests for the codegenerator of the simple compiler."""

from pathlib import Path

from simple_test.fixtures import Fixture
from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.subprocess import ProgramInvocation


class TestDecentCodeGenerator(FixturedTestCase, phase_name='run'):
    """Tests for the decent codegen of the simple compiler."""

    def setUp(self):
        super().setUp()

        # TODO: XXX: uncomment this
        # assert self.remote is not None, 'must specify --remote'

    def run_phase(self, sim_file: Path,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the compiler of the simple compiler.
        """
        return self.runner.run_compiler(sim_file, as_stdin, advanced=True)

    def assertFixture(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file produces the expected output.
        """

        # NOTE: Marc has been quoted in office hours as saying that they only
        #       test the stdin functionality of the compiler. For now, this
        #       will do.
        self.assertFixtureAsStdin(fixture)
