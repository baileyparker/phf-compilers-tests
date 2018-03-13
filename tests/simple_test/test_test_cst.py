from unittest import main, SkipTest

from tests.simple_test.phase_test_base import PhaseTestBase


class TestTestCST(PhaseTestBase):
    """An integration test for TestCST."""
    cases_under_test = 'simple_test.test_cst.TestCST'
    phase_name = 'cst'
    sc_args = ('-c',)
    extra_test_case_args = [{'skip_cst_passes': True}]

    def assertTestCaseWithArgsPassesFixture(self, fake_compiler, fixture,
                                            test_case_args):
        if test_case_args == {'skip_cst_passes': True}:
            with self.assertRaisesRegex(SkipTest, r'--skip-cst-passes'):
                super().assertTestCaseWithArgsPassesFixture(fake_compiler,
                                                            fixture,
                                                            test_case_args)
        else:
            super().assertTestCaseWithArgsPassesFixture(fake_compiler,
                                                        fixture,
                                                        test_case_args)


if __name__ == '__main__':
    main()
