"""Base class for test harness TestCases that have fixtures."""

# pylint: disable=C0103
from pathlib import Path
import sys
from typing import Callable

from simple_test.fixtures import Fixture, PhaseFile, discover_fixtures
from simple_test.test_case import TestCase
from simple_test.subprocess import ProgramInvocation
from simple_test.utils import assertion_context


TestMethod = Callable[['FixturedTestCase'], None]


def _create_test_method(fixture: Fixture) -> TestMethod:
    return lambda self: self.assertFixture(fixture)


if sys.version_info < (3, 6):  # pragma: no cover
    import types

    class _PEP487(type):
        """A metaclass for monkeypatching PEP487 behavior in Python 3.5.

        Note this doesn't exactly mirror PEP487 behavior, in that the first
        class with metaclass=_PEP487 cannot call super().__init_subclass__(),
        but for this use case that isn't needed.

        Credit: https://www.python.org/dev/peps/pep-0487/
        """
        def __new__(mcs, *args, **kwargs):
            if len(args) != 3:
                return super().__new__(mcs, *args)

            name, bases, ns = args
            init = ns.get('__init_subclass__')
            if isinstance(init, types.FunctionType):
                ns['__init_subclass__'] = classmethod(init)

            self = super().__new__(mcs, name, bases, ns)

            for k, v in self.__dict__.items():
                func = getattr(v, '__set_name__', None)
                if func is not None:
                    func(self, k)

            # A bit of a hack here to not call __init_subclass__ on the class
            # that first uses this metaclass.
            if any(isinstance(base, mcs) for base in bases):
                self.__init_subclass__(**kwargs)

            return self

        def __init__(cls, name, bases, ns, **kwargs):  # pylint: disable=W0613
            super().__init__(name, bases, ns)
else:  # pragma: no cover
    class _PEP487(type):
        pass


class FixturedTestCase(TestCase, metaclass=_PEP487):
    """Base class for test harness TestCases that have fixtures.

    Subclasses should provide the phase_name and run_simple kwargs. Example:

        class ScannerTest(FixturedTestCase, phase_name='scanner',
                          run_simple=run_simple_scanner):
            # etc.

    phase_name is the file extension the harness should look for in the
    fixtures directory. Files with this extension should contain the expected
    combined stdout/stderr from running this phase of the simple compiler (by
    calling the provided run_simple function).
    """
    @classmethod
    def __init_subclass__(cls, phase_name: str) -> None:
        # NOTE: See above, the metaclass hackey to add PEP487 support to python
        #       does not provide a super().__init_subclass__()
        # super().__init_subclass__()

        # Add the test_{fixture.name} methods for each fixture discovered
        for fixture in discover_fixtures():
            if fixture.phase_name == phase_name:
                test_method = _create_test_method(fixture)
                method_name = "test_{}".format(fixture.name)
                test_method.__name__ = method_name

                assert not hasattr(cls, method_name), \
                    "fixture name would replace existing test method: {}" \
                    .format(method_name)

                setattr(cls, method_name, test_method)

    def run_phase(self, sim_file: Path,
                  as_stdin: bool = False) -> ProgramInvocation:
        """
        Run the appropriate phase of the simple compiler for this test case.
        """
        raise NotImplementedError

    def assertFixture(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file produces the expected output.
        """
        self.assertFixtureAsArgument(fixture)
        self.assertFixtureAsStdin(fixture)

    def assertFixtureAsArgument(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file as an argument produces the expected
        output.
        """
        invocation = self.run_phase(fixture.sim_file_path)
        self.assertFixtureBehavior(fixture.phase_file, invocation)

    def assertFixtureAsStdin(self, fixture: Fixture) -> None:
        """
        Asserts that the simple compiler when run under the fixture's phase and
        given the fixture's sim file as stdin produces the expected output.
        """
        invocation = self.run_phase(fixture.sim_file_path, as_stdin=True)
        self.assertFixtureBehavior(fixture.phase_file, invocation)

    def assertFixtureBehavior(self, phase_file: PhaseFile,
                              invocation: ProgramInvocation) -> None:
        """
        Asserts that the given stdout/stderr from the simple compiler matches
        the expected output from the `PhaseFile`.
        """
        # Wrap assertion errors in the exact command to invoke
        # (that can be copied and pasted) for convenience
        with assertion_context("while running: {}\n\n".format(invocation.cmd)):
            phase_file.assert_behavior(self, invocation)
