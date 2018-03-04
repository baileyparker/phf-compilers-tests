from unittest import main, TestCase

from simple_test.utils import assertion_context, unified_diff, \
    replace_values_with_fives


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
        self.assertEqual('--- foo\n+++ bar\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n',
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


if __name__ == '__main__':
    main()
