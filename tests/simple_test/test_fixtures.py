from pathlib import Path
from unittest import main, TestCase
from unittest.mock import Mock, patch

from simple_test.fixtures import FIXTURES, Fixture, discover_fixtures


class TestFixture(TestCase):
    def test_properties(self):
        path = FIXTURES / 'foo.phase'
        fixture = Fixture(path)
        sim_path = FIXTURES / 'foo.sim'

        self.assertEqual('foo', fixture.name)
        self.assertEqual('phase', fixture.phase_name)
        self.assertEqual(sim_path, fixture.sim_file_path)
        self.assertEqual(sim_path.relative_to(FIXTURES),
                         fixture.relative_sim_file_path)
        self.assertLoadsPhaseFile(fixture, 'phase',  # pylint: disable=E1120
                                  path)

    def test_suffixed_properties(self):
        path = FIXTURES / 'foo.suffix.run'
        fixture = Fixture(path)
        sim_path = FIXTURES / 'foo.sim'

        self.assertEqual('foo_suffix', fixture.name)
        self.assertEqual('run', fixture.phase_name)
        self.assertEqual(sim_path, fixture.sim_file_path)
        self.assertEqual(sim_path.relative_to(FIXTURES),
                         fixture.relative_sim_file_path)
        self.assertLoadsPhaseFile(fixture, 'run',  # pylint: disable=E1120
                                  path)

    @patch('simple_test.fixtures.PhaseFile')
    def assertLoadsPhaseFile(self, fixture, phase_name, path, PhaseFile):
        phase_file = Mock()
        PhaseFile.load.return_value = phase_file

        self.assertEqual(phase_file, fixture.phase_file)
        PhaseFile.load.assert_called_with(phase_name, path)

    def test_name_for_subdirectory_path(self):
        fixture = Fixture(FIXTURES / 'foo' / 'bar.phase')
        self.assertEqual('foo_bar', fixture.name)


class PathMock(type(Path('.'))):
    def __init__(self, _, is_file=True):
        self._is_file = is_file

    def is_file(self):
        return self._is_file


class TestDiscoverFixtures(TestCase):
    def test_discover_fixtures(self):
        paths = [
            PathMock('.gitkeep'),
            PathMock('foo.sim'),
            PathMock('foo.scanner'),
            PathMock('foo.parser'),
            PathMock('bar.sim'),
            PathMock('bar.parser'),
            PathMock('baz', is_file=False),
            PathMock('baz/foo.sim'),
            PathMock('baz/foo.parser'),
            PathMock('baz/foo.code_generator'),
            PathMock('bah.sim'),
            PathMock('bah.first.run'),
            PathMock('bah.second.run'),
        ]

        discovered = self.discover_fixtures(paths)

        fixtures = [
            Fixture(paths[2]),
            Fixture(paths[3]),
            Fixture(paths[5]),
            Fixture(paths[8]),
            Fixture(paths[9]),
            Fixture(paths[11]),
            Fixture(paths[12]),
        ]

        self.assertCountEqual(fixtures, discovered)

    def test_discover_fixtures_unexpected_file(self):
        with self.assertRaisesRegex(AssertionError, 'unexpected fixture file'):
            self.discover_fixtures([PathMock('foo')])

    def test_discover_fixtures_sim_with_no_phases(self):
        error = r'\.sim files have no phases:\nfoo\.sim'
        with self.assertRaisesRegex(AssertionError, error):
            self.discover_fixtures([PathMock('foo.sim')])

    def test_discover_fixtures_phase_with_no_sim(self):
        error = r'\.sim files .* are missing:\nfoo\.sim'
        with self.assertRaisesRegex(AssertionError, error):
            self.discover_fixtures([
                PathMock('foo.scanner'),
                PathMock('foo.bar.run'),
            ])

    def test_discover_fixtures_suffixed_phase_with_no_sim(self):
        error = r'\.sim files .* are missing:\nbaz\.sim'
        with self.assertRaisesRegex(AssertionError, error):
            self.discover_fixtures([
                PathMock('baz.stuff.run'),
            ])

    def test_discover_fixtures_name_collision_dir(self):
        error = \
            r'name collision .* ' \
            r'(foo_bar\.sim and foo/bar\.sim|foo/bar\.sim and foo_bar\.sim)'
        with self.assertRaisesRegex(AssertionError, error):
            self.discover_fixtures([
                PathMock('foo_bar.sim'),
                PathMock('foo_bar.scanner'),
                PathMock('foo/bar.sim'),
                PathMock('foo/bar.scanner'),
            ])

    def test_discover_fixtures_name_collision_suffix(self):
        error = \
            r'name collision .* ' \
            r'(foo_bar\.sim and foo\.sim|foo\.sim and foo_bar\.sim)'
        with self.assertRaisesRegex(AssertionError, error):
            self.discover_fixtures([
                PathMock('foo_bar.sim'),
                PathMock('foo_bar.scanner'),
                PathMock('foo.sim'),
                PathMock('foo.bar.run'),
            ])

    def test_discover_fixtures_name_collision_suffix_dir(self):
        error = \
            r'name collision .* ' \
            r'(foo/bar\.sim and foo\.sim|foo\.sim and foo/bar\.sim)'
        with self.assertRaisesRegex(AssertionError, error):
            self.discover_fixtures([
                PathMock('foo/bar.sim'),
                PathMock('foo/bar.scanner'),
                PathMock('foo.sim'),
                PathMock('foo.bar.run'),
            ])

    def discover_fixtures(self, files):
        with patch('simple_test.fixtures.FIXTURES',
                   autospec=Path) as fixtures_dir:
            fixtures_dir.glob.return_value = files

            fixtures = discover_fixtures()
            fixtures_dir.glob.assert_called_with('**/*')
            return fixtures


if __name__ == '__main__':
    main()
