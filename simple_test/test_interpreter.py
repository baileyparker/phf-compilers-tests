"""Tests for the interpreter of the simple compiler."""

from pathlib import Path
from unittest import main

from simple_test.fixtures import Fixture
from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.subprocess import ProgramInvocation


class TestInterpreter(FixturedTestCase, phase_name='run'):
    """Tests for the interpreter of the simple compiler."""

    def run_phase(self, sim_file: Path,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the interpreter of the simple compiler.
        """
        return self.runner.run_interpreter(sim_file, as_stdin)

    def assertFixture(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file produces the expected output.
        """

        # Note that as mentioned on Piazza, the interpreter should be able to
        # handle a sim file as stdin and then still allow READs (more stdin
        # after stdin has been "closed"). Although this is simple in C/C++, it
        # is often tricky in other languages that express stdin as a close-once
        # stream. So, we can only test as fixture argument and not stdin.
        # TODO: this is only necessary for tests with READs
        self.assertFixtureAsArgument(fixture)


if __name__ == '__main__':
    main()
