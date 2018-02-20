from unittest import main

from tests.simple_test.phase_test_base import PhaseTestBase


class TestTestCST(PhaseTestBase):
    """An integration test for TestCST."""
    cases_under_test = 'simple_test.test_cst.TestCST'
    phase_name = 'cst'
    sc_args = ('-c',)


if __name__ == '__main__':
    main()
