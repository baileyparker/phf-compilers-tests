from unittest import main, TestCase

from simple_test.fixtures import discover_fixtures


class TestLintFixtures(TestCase):
    def test_fixtures_are_snake_case(self):
        for fixture in discover_fixtures():
            for part in fixture.relative_sim_file_path.with_suffix('').parts:
                self.assertRegex(part, r'^[a-z0-9]+(_[a-z0-9]+)*$',
                                 msg="fixture files should be snake case: {}"
                                 .format(fixture.relative_sim_file_path))

    def test_no_duplicate_sim_files(self):
        sim_file_contents = {}

        for fixture in discover_fixtures():
            with fixture.sim_file_path.open() as f:
                contents = f.read()

                if contents in sim_file_contents:
                    self.fail("identical sim files {} and {}"
                              .format(fixture.relative_sim_file_path,
                                      sim_file_contents[contents]))

                sim_file_contents[contents] = fixture.relative_sim_file_path


if __name__ == '__main__':
    main()
