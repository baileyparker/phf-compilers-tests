"""Tests for the scanner phase of the simple compiler."""

from pathlib import Path
from typing import Any
from unittest import main

from simple_test.fixtures import Fixture
from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.runner import Result


class TestCST(FixturedTestCase, phase_name='cst'):
    """Tests for the CST phase of the simple compiler."""

    def __init__(self, skip_cst_passes: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.skip_passes = skip_cst_passes

    # TODO: randomized fuzzing tests  # pylint: disable=W0511

    def run_phase(self, sim_file: Path, as_stdin: bool = False) -> Result:
        """
        Run the CST phase of the simple compiler.
        """
        return self.runner.run_cst(sim_file, as_stdin)

    def assertFixture(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file produces the expected output.
        """

        # With --skip-cst-passes, skip any fixtures that don't have errors
        # (they may be syntactically valid, but not semantically valid)
        if self.skip_passes and not fixture.phase_file.has_error:
            self.skipTest('valid CST fixture may not be semantically valid, '
                          'skipping due to --skip-cst-passes')

        self.assertFixtureAsArgument(fixture)
        self.assertFixtureAsStdin(fixture)


if __name__ == '__main__':
    main()
