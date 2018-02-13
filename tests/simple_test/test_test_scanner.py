from unittest import main

from tests.simple_test.phase_test_base import PhaseTestBase


class TestTestScanner(PhaseTestBase):
    """An integration test for TestScanner."""
    cases_under_test = 'simple_test.test_scanner.TestScanner'
    phase_name = 'scanner'
    sc_args = ('-s',)


if __name__ == '__main__':
    main()
