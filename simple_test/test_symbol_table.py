"""Tests for the symbol table phase of the simple compiler."""

from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.fixtures import PhaseFile
from simple_test.runner import Result, run_simple_symbol_table  # noqa:  # pylint: disable=W0611
from simple_test.utils import replace_values_with_fives


class TestSymbolTable(FixturedTestCase,
                      phase_name='st', run_simple=run_simple_symbol_table):
    """Tests for the symbol table phase of the simple compiler."""

    # TODO: randomized fuzzing tests  # pylint: disable=W0511

    def assertFixtureStdout(self, expected: PhaseFile, result: Result) -> None:
        """Assert the stdout from the simple compiler matches the expected."""
        # TODO: make this an ENV flag  # pylint: disable=W0511
        stdout = replace_values_with_fives(expected.stdout)
        self.assertStdoutEqual(stdout, result.stdout, result.stderr)


if __name__ == '__main__':
    main()
