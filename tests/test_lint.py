from contextlib import contextmanager, redirect_stdout
from io import StringIO
from os import chdir as setcwd, getcwd
from pathlib import Path
from subprocess import run, PIPE
from unittest import main, TestCase

from flake8.api.legacy import get_style_guide


REPO_ROOT = (Path(__file__) / '..' / '..').resolve()


class TestLint(TestCase):
    def test_lint(self):
        errors = [
            *get_flake8_errors(),
            *get_pylint_errors('simple_test', 'setup.py'),
            *get_pylint_errors('--disable=C0111,C0103,R0201,R0902,R0913,'
                               'R0914,W0201',
                               '--method-rgx=[a-z_][a-z0-9_]{2,50}',
                               'tests')
        ]
        errors.sort(key=parse_lint_error)

        if errors:
            errors_str = '\n'.join(errors)
            self.fail("found style errors:\n{}".format(errors_str))


def get_flake8_errors():
    # chrdir so reported paths are relative to it (and not absolute)
    with chdir(str(REPO_ROOT)):
        output = StringIO()

        with redirect_stdout(output):
            get_style_guide().check_files(['.'])

        return list(filter(None, output.getvalue().split('\n')))


@contextmanager
def chdir(path):
    old_cwd = getcwd()
    setcwd(path)
    yield
    setcwd(old_cwd)


def get_pylint_errors(*args):
    options = [
        '--reports=n',
        '--score=n',
        "--msg-template='{path}:{line}:{column}: {msg_id} {msg}'",
    ]

    result = run(['pylint', *options, *args], cwd=str(REPO_ROOT), stdout=PIPE,
                 stderr=PIPE)

    lines = result.stdout.decode('utf8').split('\n')
    return ["./{}".format(line) for line in filter(is_pylint_error, lines)]


def is_pylint_error(line):
    return line and not line.startswith('************* Module') \
            and not line.startswith(' ')


def parse_lint_error(line):
    path, line, col, rest = line.split(':', 3)
    msg_letter, (msg_id, _) = rest[1], rest[2:].split(' ', 1)  # noqa: F841
    return (path, int(line), int(col), msg_letter, int(msg_id))


if __name__ == '__main__':
    main()
