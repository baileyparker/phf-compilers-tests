from unittest import main

from simple_test.utils import replace_values_with_fives
from tests.simple_test.phase_test_base import PhaseTestBase


class TestTestSymbolTable(PhaseTestBase):
    """An integration test for TestSymbolTable."""
    cases_under_test = 'simple_test.test_symbol_table.TestSymbolTable'
    phase_name = 'st'
    sc_args = ('-t',)
    extra_test_case_args = [{'st_all_fives': True}]

    def run_fake_compiler(self, fake_compiler, fixture, arg_output,
                          test_case_args, stdin_output=None):
        if test_case_args == {'st_all_fives': True}:
            arg_stdout, arg_stderr = arg_output
            arg_output = (replace_values_with_fives(arg_stdout), arg_stderr)

            if stdin_output:
                stdin_stdout, stdin_stderr = stdin_output
                stdin_output = (replace_values_with_fives(stdin_stdout),
                                stdin_stderr)

        super().run_fake_compiler(fake_compiler, fixture, arg_output,
                                  test_case_args, stdin_output)


if __name__ == '__main__':
    main()
