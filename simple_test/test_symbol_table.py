"""Tests for the symbol table phase of the simple compiler."""

from pathlib import Path
from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.fixtures import PhaseFile
from simple_test.runner import Result
from simple_test.utils import replace_values_with_fives


class TestSymbolTable(FixturedTestCase, phase_name='st'):
    """Tests for the symbol table phase of the simple compiler."""

    # TODO: randomized fuzzing tests  # pylint: disable=W0511

    def run_phase(self, sim_file: Path, as_stdin: bool = False) -> Result:
        """
        Run the symbol table phase of the simple compiler.
        """
        return self.runner.run_symbol_table(sim_file, as_stdin)

    def assertFixtureStdout(self, expected: PhaseFile, result: Result) -> None:
        """Assert the stdout from the simple compiler matches the expected."""
        # TODO: make this an ENV flag  # pylint: disable=W0511
        stdout = replace_values_with_fives(expected.stdout)
        self.assertStdoutEqual(stdout, result.stdout, result.stderr)


if __name__ == '__main__':
    main()
