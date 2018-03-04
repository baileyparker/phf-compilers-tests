import re
from unittest import main, TestCase

from simple_test.fixtures import discover_fixtures


class TestLintFixtures(TestCase):
    def test_fixtures_are_snake_case(self):
        non_snake_case = []

        for fixture in discover_fixtures():
            for part in fixture.relative_sim_file_path.with_suffix('').parts:
                if not re.match(r'^[a-z]+(_[a-z0-9]+)*$', part):
                    non_snake_case.append(fixture.relative_sim_file_path)

        if non_snake_case:
            self.fail("Fixture names must be snake case:\n\n{}"
                      .format('\n'.join("\t{}".format(n)
                                        for n in non_snake_case)))

    def test_no_duplicate_sim_files(self):
        sim_file_contents = {}
        sim_files = set()
        duplicates = []

        for fixture in discover_fixtures():
            if fixture.sim_file_path not in sim_files:
                with fixture.sim_file_path.open() as f:
                    contents = f.read()

                    if contents in sim_file_contents:
                        duplicates.append((fixture.relative_sim_file_path,
                                           sim_file_contents[contents]))

                    sim_file_contents[contents] = \
                        fixture.relative_sim_file_path
                    sim_files.add(fixture.sim_file_path)

        if duplicates:
            self.fail("Identical sim files:\n\n{}\n\nPlease merge them!"
                      .format('\n'.join("\t{} and {}".format(a, b)
                                        for a, b in duplicates)))

    # TODO: ensure ST files don't have 5's replaced  # pylint: disable=W0511


if __name__ == '__main__':
    main()
