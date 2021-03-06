from pathlib import Path
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from simple_test.fixtures import FIXTURES, Fixture, PhaseFile, \
    discover_fixtures


class TestFixture(TestCase):
    def test_properties(self):
        path = FIXTURES / 'foo.phase'
        fixture = Fixture(path)
        sim_path = path.with_suffix('.sim')

        self.assertEqual('foo', fixture.name)
        self.assertEqual('phase', fixture.phase_name)
        self.assertEqual(sim_path, fixture.sim_file_path)
        self.assertEqual(sim_path.relative_to(FIXTURES),
                         fixture.relative_sim_file_path)

        with patch('simple_test.fixtures.PhaseFile') as PhaseFile_:
            phase_file = Mock()
            PhaseFile_.load.return_value = phase_file

            self.assertEqual(phase_file, fixture.phase_file)

            PhaseFile_.load.assert_called_with(path)

    def test_name_for_subdirectory_path(self):
        fixture = Fixture(FIXTURES / 'foo' / 'bar.phase')
        self.assertEqual('foo_bar', fixture.name)


class TestPhaseFile(TestCase):
    def test_load_no_errors(self):
        self.assertLoads("a\nb\nc\n", "a\nb\nc\n", False)

    def test_load_with_errors(self):
        self.assertLoads("a\nb\nerror: foo\nc\n", "a\nb\nc\n", True)

    def assertLoads(self, contents, stdout, has_error):
        path = Mock(autospec=Path)
        file_context = MagicMock()
        f = Mock()
        path.open.return_value = file_context
        file_context.__enter__.return_value = f
        f.read.return_value = contents

        phase_file = PhaseFile.load(path)

        path.open.assert_called_once_with()
        self.assertEqual(stdout, phase_file.stdout)
        self.assertEqual(has_error, phase_file.has_error)


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
        ]

        discovered = self.discover_fixtures(paths)

        fixtures = [
            Fixture(paths[2]),
            Fixture(paths[3]),
            Fixture(paths[5]),
            Fixture(paths[8]),
            Fixture(paths[9]),
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
            self.discover_fixtures([PathMock('foo.scanner')])

    def test_discover_fixtures_name_collision(self):
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

    def discover_fixtures(self, files):
        with patch('simple_test.fixtures.FIXTURES',
                   autospec=Path) as fixtures_dir:
            fixtures_dir.glob.return_value = files

            fixtures = discover_fixtures()
            fixtures_dir.glob.assert_called_with('**/*')
            return fixtures


if __name__ == '__main__':
    main()
