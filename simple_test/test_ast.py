"""Tests for the AST phase of the simple compiler."""

from pathlib import Path
from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.subprocess import ProgramInvocation


class TestAST(FixturedTestCase, phase_name='ast'):
    """Tests for the AST phase of the simple compiler."""

    # TODO: randomized fuzzing tests  # pylint: disable=W0511

    def run_phase(self, sim_file: Path,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the AST phase of the simple compiler.
        """
        return self.runner.run_ast(sim_file, as_stdin)


if __name__ == '__main__':
    main()
