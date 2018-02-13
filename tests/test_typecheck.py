import os
from pathlib import Path
from subprocess import run, PIPE
from unittest import main, TestCase


REPO_ROOT = (Path(__file__) / '..' / '..').resolve()
OPTIONS = [
    '--strict',
    '--incremental',
]


class TestTypecheck(TestCase):
    def test_typecheck(self):
        result = \
            run(['mypy', *OPTIONS, 'simple_test'], stdout=PIPE,
                cwd=str(REPO_ROOT), env={'MYPYPATH': 'stubs', **os.environ})

        if result.returncode != 0:
            self.fail("typecheck errors:\n{}"
                      .format(result.stdout.decode('utf8')))


if __name__ == '__main__':
    main()
