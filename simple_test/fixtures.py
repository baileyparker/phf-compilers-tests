"""Fixture representation and discovery used by the test harness."""
from collections import defaultdict
from itertools import chain
from pathlib import Path
from typing import DefaultDict, Dict, List, NamedTuple, Set  # noqa  # pylint: disable=W0611

from simple_test.phase_file import PhaseFile


FIXTURES = (Path(__file__) / '..' / 'fixtures').resolve()


class Fixture(NamedTuple('Fixture', [('phase_file_path', Path)])):
    """
    Represents an input sim file that should be fed into the simple compiler
    under test, the phase in which to run the compiler, and the output that
    the harness should expected from this.
    """
    @property
    def name(self) -> str:
        """Returns the name of the fixture.

        If the fixture has a phase subname then the dot is replaced with an
        underscore (to allow the name to be used as a unittest TestCase test
        method name). For example, a fixture with phase file
        'fixtures/foo.bar.run' will be named 'foo_bar'.

        For fixtures in a subdirectory, the slashes are replaced with
        underscores (to allow the name to be used as a unittest TestCase test
        method name. For example, a fixture with phase file
        'fixtures/foo/bar.scanner' will be named 'foo_bar'.
        """
        relative_path = str(self._relative_phase_file_path.with_suffix(''))
        return relative_path.replace('/', '_').replace('.', '_')

    @property
    def phase_name(self) -> str:
        """Returns the compiler phase name the fixture should be run with."""
        return str(self._relative_phase_file_path.suffix[1:])

    @property
    def sim_file_path(self) -> Path:
        """Returns the path to the sim file to pass into the compiler."""
        phase_file_path = self.phase_file_path
        if '.' in phase_file_path.stem:
            phase_file_path = phase_file_path.with_suffix('')

        return phase_file_path.with_suffix('.sim')

    @property
    def relative_sim_file_path(self) -> Path:
        """Returns the path to the sim file relative to the fixtures dir."""
        return self.sim_file_path.relative_to(FIXTURES)

    @property
    def phase_file(self) -> 'PhaseFile':
        """
        Returns the PhaseFile representing the expected compiler phase output.
        """
        return PhaseFile.load(self.phase_name, self.phase_file_path)

    @property
    def _relative_phase_file_path(self) -> Path:
        return self.phase_file_path.relative_to(FIXTURES)


def discover_fixtures() -> List[Fixture]:
    """
    Retrieves a list of `Fixture`s from the fixtures/ directory. A fixture
    comprises a least two files:

      1. A sim file (fixtures/**/*.sim) - the sim program that should be fed
         into the simple compiler under test

      2. A phase file (features/**/*.{scanner}) - the combined expected
         stdout/stderr when the sim file is fed into the simple compiler. The
         extension of this file indicates which phase of the compiler should be
         invoked to obtain this output. Any lines starting with "error: " will
         be removed from the expected stdout (and instead will be used to
         assert that the compiler printed at least one error to stderr). If
         none of these error lines exist in the phase file, the test harness
         will assert that no errors were printed to stderr by the compiler.

    One sim file can have multiple phase files (each pair produces a separate
    fixture). These fixtures can be organized into directories if desired.
    """
    phase_files = defaultdict(list)  # type: DefaultDict[Path, List[Fixture]]
    sim_files = set()  # type: Set[Path]

    for path in filter(lambda p: p.name[0] != '.', FIXTURES.glob('**/*')):
        if path.is_file():
            assert path.suffix != '', \
                "unexpected fixture file: {}".format(path)

            # Organize phase tests by their associated .sim file
            if path.suffix != '.sim':
                fixture = Fixture(path)
                phase_files[fixture.sim_file_path].append(fixture)

            # Keep track of sim files (see assertions below)
            else:
                sim_files.add(path)

    # Every fixture not ending in .sim, must have a corresponding .sim file (of
    # the same name, just with the extension changed to .sim). This is an easy
    # mistake to make (ex. due to a typo), so we should check if any needed sim
    # files are missing
    missing_sim_files = phase_files.keys() - sim_files
    assert not missing_sim_files, \
        "these *.sim files have phases, but are missing:\n{}" \
        .format('\n'.join(map(str, sorted(missing_sim_files))))

    # It's also possible to have a .sim file with no associated tests. This may
    # indicate that the tests weren't checked into git, for example.
    testless_sim_files = sim_files - phase_files.keys()
    assert not testless_sim_files, "these *.sim files have no phases:\n{}" \
        .format('\n'.join(map(str, sorted(testless_sim_files))))

    fixtures = list(chain.from_iterable(phase_files.values()))

    # We replace '/' in paths with '_' for the test name. This could allow for
    # a scenario where both a/b and a_b exist. Instead of just having one
    # overwrite the other, we want to warn the user.
    test_names = {}  # type: Dict[str, Fixture]

    # One Fixture per *.sim file (to prevent multiple phases for the same sim
    # file from causing a "name collision"--when there is no collision, they
    # just have the same sim file)
    sim_file_fixtures = {f.sim_file_path: f for f in fixtures}.values()

    for fixture in sim_file_fixtures:
        if fixture.name in test_names:
            assert False, "name collision between {} and {}" \
                .format(fixture.relative_sim_file_path,
                        test_names[fixture.name].relative_sim_file_path)

        test_names[fixture.name] = fixture

    return fixtures
