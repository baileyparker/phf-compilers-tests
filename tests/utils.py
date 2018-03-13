from os import environ
from unittest import skipIf


def skip_slow_tests():
    return bool(environ.get('SLOW_TESTS', False))


slow_test = skipIf(skip_slow_tests(), 'slow test')
