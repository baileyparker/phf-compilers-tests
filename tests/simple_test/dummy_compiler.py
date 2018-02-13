#!/usr/bin/env python3

import json
from pathlib import Path
import sys


def main():
    directory = (Path(__file__) / '..').resolve()  # pylint: disable=E1101

    arguments = directory / 'arguments'
    stdin = directory / 'stdin'
    stdout = directory / 'stdout'
    stderr = directory / 'stderr'

    # Use second variant of files if this is our section invocation (the one
    # where the file is passed in via stdin instead of CLI arg)
    if arguments.exists() or stdin.exists():
        arguments = arguments.with_suffix('.2')
        stdin = stdin.with_suffix('.2')
        stdout = stdout.with_suffix('.2')
        stderr = stderr.with_suffix('.2')

    # Write out CLI args
    with arguments.open('w') as f:
        json.dump(sys.argv[1:], f)

    # Write out stdin
    with stdin.open('w') as f:
        f.write(sys.stdin.read())

    # Return faked stdout
    with stdout.open() as f:
        sys.stdout.write(f.read())

    # Return faked stderr
    with stderr.open() as f:
        sys.stderr.write(f.read())


if __name__ == '__main__':
    main()
