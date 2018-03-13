from unittest import main

from tests.simple_test.phase_test_base import PhaseTestBase


class TestTestAST(PhaseTestBase):
    """An integration test for TestAST."""
    cases_under_test = 'simple_test.test_ast.TestAST'
    phase_name = 'ast'
    sc_args = ('-a',)


if __name__ == '__main__':
    main()
