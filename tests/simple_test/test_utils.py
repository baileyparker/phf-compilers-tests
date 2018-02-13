from unittest import main, TestCase

from simple_test.utils import assertion_context, unified_diff


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


if __name__ == '__main__':
    main()
