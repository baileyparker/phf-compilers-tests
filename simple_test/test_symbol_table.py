"""Tests for the symbol table phase of the simple compiler."""

from pathlib import Path
from typing import Any
from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.phase_file import PhaseFile, OutputPhaseFile
from simple_test.subprocess import ProgramInvocation
from simple_test.utils import replace_values_with_fives


class TestSymbolTable(FixturedTestCase, phase_name='st'):
    """Tests for the symbol table phase of the simple compiler."""

    def __init__(self, st_all_fives: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.all_fives = st_all_fives

    # TODO: randomized fuzzing tests  # pylint: disable=W0511

    def run_phase(self, sim_file: Path,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the symbol table phase of the simple compiler.
        """
        return self.runner.run_symbol_table(sim_file, as_stdin)

    def assertFixtureBehavior(self, phase_file: PhaseFile,
                              invocation: ProgramInvocation) -> None:
        """
        Asserts that the given stdout/stderr from the simple compiler matches
        the expected output from the `PhaseFile`.
        """

        if self.all_fives:
            assert isinstance(phase_file, OutputPhaseFile)

            stdout = replace_values_with_fives(phase_file.stdout)
            phase_file = OutputPhaseFile(stdout, phase_file.has_error)

        super().assertFixtureBehavior(phase_file, invocation)


if __name__ == '__main__':
    main()
