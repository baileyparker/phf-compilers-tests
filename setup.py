# pylint: disable=C0111,C0413,E0401,E0611
# flake8: noqa: E402
from distutils.core import setup
from distutils.cmd import Command
from distutils.util import convert_path
from os import chdir
from pathlib import Path
from subprocess import call
import sys


chdir(str((Path(__file__) / '..').resolve()))  # pylint: disable=E1101


class OptionlessCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


TEST_ARGS = ['-m', 'unittest', 'discover', '-s', 'tests', '-t', '.']


class TestCommand(OptionlessCommand):
    description = 'runs the unit and integration tests'

    def run(self):  # pylint: disable=R0201
        sys.exit(call([sys.executable] + TEST_ARGS))


class CoverageCommand(OptionlessCommand):
    description = 'measures code coverage of the unit and integration tests'

    def run(self):  # pylint: disable=R0201
        self._call_or_exit('Coverage',
                           ['run', '--source=simple_test'] + TEST_ARGS)
        self._call_or_exit('Coverage report', ['report'])
        self._call_or_exit('Coverage html report', ['html', '-d', '.htmlcov'])

        uri = (Path(__file__) / '..' / '.htmlcov' / 'index.html').resolve() \
            .as_uri()
        print("\nView more detailed results at: {}".format(uri))

    def _call_or_exit(self, name, args):  # pylint: disable=R0201
        exit_code = call(['coverage3'] + args)

        if exit_code != 0:
            print("{} failed!".format(name), file=sys.stderr)
            sys.exit(exit_code)


with open(convert_path('simple_test/version.py')) as f:
    METADATA = {}
    exec(f.read(), METADATA)  # pylint: disable=W0122


setup(name='simple_test',
      version=METADATA['__version__'],
      description='Simple compiler test harness for PHF\'s 601.[346]28 course',
      author=METADATA['__author__'],
      author_email=METADATA['__email__'],
      cmdclass={
          'test': TestCommand,
          'coverage': CoverageCommand,
      })
