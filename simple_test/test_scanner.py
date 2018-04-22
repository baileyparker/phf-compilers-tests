"""Tests for the scanner phase of the simple compiler."""

from pathlib import Path
from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.subprocess import ProgramInvocation


class TestScanner(FixturedTestCase, phase_name='scanner'):
    """Tests for the scanner phase of the simple compiler."""

    # TODO: randomized fuzzing tests  # pylint: disable=W0511

    def run_phase(self, sim_file: Path,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the scanner phase of the simple compiler.
        """
        return self.runner.run_scanner(sim_file, as_stdin)


if __name__ == '__main__':
    main()
