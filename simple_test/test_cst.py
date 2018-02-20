"""Tests for the scanner phase of the simple compiler."""

from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.runner import run_simple_cst  # pylint: disable=W0611


class TestCST(FixturedTestCase,
              phase_name='cst', run_simple=run_simple_cst):
    """Tests for the CST phase of the simple compiler."""

    # TODO: randomized fuzzing tests  # pylint: disable=W0511
    pass


if __name__ == '__main__':
    main()
