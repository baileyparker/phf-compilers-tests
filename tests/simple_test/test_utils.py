from pathlib import Path
from unittest import main, TestCase
from unittest.mock import Mock, MagicMock, patch

from simple_test.utils import assertion_context, unified_diff, \
    replace_values_with_fives, relative_to_cwd, join_cmd, catch_map, \
    MultiException, list_split


class TestUtils(TestCase):
    def test_assertion_context_with_raise_assert(self):
        with self.assertRaisesRegex(AssertionError, 'foo bar'):
            with assertion_context('foo '):
                assert False, 'bar'

    def test_assertion_context_with_raise_other(self):
        with self.assertRaisesRegex(Exception, 'something'):
            with assertion_context('foo '):
                raise Exception('something')

    def test_assertion_context_with_no_raise(self):
        with assertion_context('foo '):
            pass

    def test_unified_diff(self):
        diff = unified_diff('a\nb\n', 'a\nc\n', fromfile='foo', tofile='bar')
        self.assertEqual('--- foo\n'
                         '+++ bar\n'
                         '@@ -1,2 +1,2 @@\n'
                         ' a\n'
                         '-b\n'
                         '+c\n',
                         diff)

    def test_unified_diff_long(self):
        a = 'a\nb\nc\nd\ne\n'
        b = a[:-2] + 'f\n'
        diff = unified_diff(a, b, fromfile='foo', tofile='bar')
        self.assertEqual('--- foo\n'
                         '+++ bar\n'
                         '@@ -2,4 +2,4 @@\n'
                         ' b\n'
                         ' c\n'
                         ' d\n'
                         '-e\n'
                         '+f\n',
                         diff)

    def test_unified_diff_all_lines(self):
        a = 'a\nb\nc\nd\ne\n'
        b = a[:-2] + 'f\n'
        diff = unified_diff(a, b, fromfile='foo', tofile='bar', all_lines=True)
        self.assertEqual('--- foo\n'
                         '+++ bar\n'
                         '@@ -1,5 +1,5 @@\n'
                         ' a\n'
                         ' b\n'
                         ' c\n'
                         ' d\n'
                         '-e\n'
                         '+f\n',
                         diff)

    def test_unified_diff_colored(self):
        diff = unified_diff('a\nb\n', 'a\nc\n', fromfile='foo', tofile='bar',
                            color=True)
        self.assertEqual('\033[1;31m--- foo\n\033[0;0m'
                         '\033[1;32m+++ bar\n\033[0;0m'
                         '\033[1;34m@@ -1,2 +1,2 @@\n\033[0;0m'
                         ' a\n'
                         '\033[1;31m-b\n\033[0;0m'
                         '\033[1;32m+c\n\033[0;0m',
                         diff)

    def test_replace_values_with_fixes(self):
        self.assertEqual('value:\n  5',
                         replace_values_with_fives('value:\n  8675309'))

    def test_replace_values_with_fixes_in_context(self):
        stdout = 'SCOPE BEGIN\n'                        \
                 '  x123 =>\n'                          \
                 '    CONST BEGIN\n'                    \
                 '      type:\n'                        \
                 '        INTEGER\n'                    \
                 '      value:\n'                       \
                 '        18006492568\n'                \
                 '    END CONST\n'                      \
                 '  y23x28 =>\n'                        \
                 '    CONST BEGIN\n'                    \
                 '      type:\n'                        \
                 '        INTEGER\n'                    \
                 '      value:\n'                       \
                 '        42\n'                         \
                 '    END CONST\n'                      \
                 '  y2345 =>\n'                         \
                 '    RECORD BEGIN\n'                   \
                 '      SCOPE BEGIN\n'                  \
                 '        x22 =>\n'                     \
                 '          ARRAY BEGIN\n'              \
                 '            type:\n'                  \
                 '              INTEGER\n'              \
                 '            length:\n'                \
                 '              43252003274489856000\n' \
                 '          END ARRAY\n'                \
                 '      END SCOPE\n'                    \
                 '    END RECORD\n'                     \
                 '  x24 =>\n'                           \
                 '    ARRAY BEGIN\n'                    \
                 '      type:\n'                        \
                 '        INTEGER\n'                    \
                 '      length:\n'                      \
                 '        5\n'                          \
                 '    END ARRAY\n'                      \
                 'END SCOPE\n'

        expected = 'SCOPE BEGIN\n'           \
                   '  x123 =>\n'             \
                   '    CONST BEGIN\n'       \
                   '      type:\n'           \
                   '        INTEGER\n'       \
                   '      value:\n'          \
                   '        5\n'             \
                   '    END CONST\n'         \
                   '  y23x28 =>\n'           \
                   '    CONST BEGIN\n'       \
                   '      type:\n'           \
                   '        INTEGER\n'       \
                   '      value:\n'          \
                   '        5\n'             \
                   '    END CONST\n'         \
                   '  y2345 =>\n'            \
                   '    RECORD BEGIN\n'      \
                   '      SCOPE BEGIN\n'     \
                   '        x22 =>\n'        \
                   '          ARRAY BEGIN\n' \
                   '            type:\n'     \
                   '              INTEGER\n' \
                   '            length:\n'   \
                   '              5\n'       \
                   '          END ARRAY\n'   \
                   '      END SCOPE\n'       \
                   '    END RECORD\n'        \
                   '  x24 =>\n'              \
                   '    ARRAY BEGIN\n'       \
                   '      type:\n'           \
                   '        INTEGER\n'       \
                   '      length:\n'         \
                   '        5\n'             \
                   '    END ARRAY\n'         \
                   'END SCOPE\n'
        self.assertEqual(expected, replace_values_with_fives(stdout))

    def test_relative_to_cwd(self):
        self.assertRelativeToCwd('relative/path',
                                 relative_to=Path('relative/path'))

    def test_relative_to_cwd_raises(self):
        self.assertRelativeToCwd('abs/path', abs_path='abs/path',
                                 relative_to=ValueError('relative_to failed'))

    def test_relative_to_cwd_binary(self):
        self.assertRelativeToCwd('./binary', binary=True,
                                 relative_to=Path('binary'))

    def test_relative_to_cwd_raises_binary(self):
        self.assertRelativeToCwd('./binary', abs_path='./binary',
                                 relative_to=ValueError('relative_to failed'),
                                 binary=True)

    def assertRelativeToCwd(self, expected, abs_path='abs/path',
                            relative_to=Path('relative/path'), binary=False):
        path = FakePath(abs_path)
        path.relative_to = MagicMock()
        if isinstance(relative_to, Exception):
            path.relative_to.side_effect = relative_to
        else:
            path.relative_to.return_value = relative_to

        self.assertEqual(expected, relative_to_cwd(path, binary=binary))

    @patch('simple_test.utils.shell_quote')
    def test_join_cmd(self, shell_quote):
        args = [Mock() for _ in range(5)]
        quoted_args = [chr(97 + i) for i, _ in enumerate(args)]

        args_map = {arg: quoted for arg, quoted in zip(args, quoted_args)}
        shell_quote.side_effect = lambda x: args_map[x]

        self.assertEqual(' '.join(quoted_args), join_cmd(args))

    def test_catch_map(self):
        self.assertEqual(list(range(1, 5)),
                         catch_map(lambda x: x + 1, range(4)))

    def test_catch_map_exceptions(self):
        iterable = range(5)
        exceptions = [Exception(str(i)) for i, _ in enumerate(iterable)]

        with self.assertRaises(MultiException) as cm:
            def raise_one(x):
                raise exceptions[x]

            catch_map(raise_one, iterable)

        self.assertEqual(exceptions, cm.exception.exceptions)

    def test_list_split(self):
        result = list(list_split(0, [0, 1, 2, 0, 3, 0, 0, 4]))
        self.assertEqual([[], [1, 2], [3], [], [4]], result)


# Paths are a pain to mock, we subclass to allow overwriting methods with mocks
class FakePath(type(Path('.'))):
    def relative_to(self, *p):  # pylint: disable=W0235
        return super().relative_to(*p)


if __name__ == '__main__':
    main()
