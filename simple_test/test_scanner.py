"""Tests for the scanner phase of the simple compiler."""

from unittest import main

from simple_test.fixtured_test_case import FixturedTestCase
from simple_test.runner import run_simple_scanner  # pylint: disable=W0611


class TestScanner(FixturedTestCase,
                  phase_name='scanner', run_simple=run_simple_scanner):
    """Tests for the scanner phase of the simple compiler."""

    # TODO: randomized fuzzing tests  # pylint: disable=W0511
    pass


if __name__ == '__main__':
    main()
