import io
import sys
from argparse import Namespace
from unittest import TestCase
from unittest.mock import patch, Mock

from dndice import roller

sentinel = object()


class TestParser(TestCase):
    def setUp(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def test_mode(self):
        with patch.object(sys, 'argv', ['roller.py', '-a', '1d4']):
            self.assertTrue(roller.parse().average)
            self.assertFalse(roller.parse().critical)
            self.assertFalse(roller.parse().maximum)
        with patch.object(sys, 'argv', ['roller.py', '-c', '1d4']):
            self.assertTrue(roller.parse().critical)
        with patch.object(sys, 'argv', ['roller.py', '-m', '1d4']):
            self.assertTrue(roller.parse().maximum)
        with patch.object(sys, 'argv', ['roller.py', '-m', '-c', '1d4']):
            self.assertRaises(SystemExit, roller.parse)

    def test_number(self):
        with patch.object(sys, 'argv', ['roller.py', '-n', '10', '1d4']):
            self.assertEqual(roller.parse().number, 10)
        with patch.object(sys, 'argv', ['roller.py', '1d4']):
            self.assertEqual(roller.parse().number, 1)
        with patch.object(sys, 'argv', ['roller.py', '-n', 'b', '1d4']):
            self.assertRaises(SystemExit, roller.parse)

    def test_display_flags(self):
        with patch.object(sys, 'argv', ['roller.py', '-w', '10', '1d4']):
            self.assertEqual(roller.parse().wrap, 10)
        with patch.object(sys, 'argv', ['roller.py', '-v', '1d4']):
            self.assertTrue(roller.parse().verbose)
        with patch.object(sys, 'argv', ['roller.py', '-vc', '1d4']):
            self.assertTrue(roller.parse().verbose)
            self.assertTrue(roller.parse().critical)

    def test_expression(self):
        with patch.object(sys, 'argv', ['roller.py', '1d4']):
            self.assertEqual(roller.parse().expression, ['1d4'])
        with patch.object(sys, 'argv', ['roller.py', '1d4', '2d6']):
            self.assertEqual(roller.parse().expression, ['1d4', '2d6'])


def base_args(**kwargs):
    default = {
        'expression': ['1d20'],
        'average': False,
        'critical': False,
        'maximum': False,
        'wrap': 80,
        'verbose': False,
        'number': 1,
    }
    return Namespace(**{**default, **kwargs})


class TestMain(TestCase):
    def setUp(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    @patch.object(roller, 'parse', Mock(return_value=base_args()))
    @patch.object(roller, 'basic', Mock(return_value=5))
    def test_basic(self):
        roller.main()
        self.assertEqual(self.stdout.getvalue().strip(), '5')

    @patch.object(roller, 'parse', Mock(return_value=base_args(number=3)))
    @patch.object(roller, 'basic', Mock(return_value=5))
    def test_number(self):
        roller.main()
        self.assertEqual(self.stdout.getvalue().strip(), '5 5 5')

    @patch.object(roller, 'parse', Mock(return_value=base_args(average=True)))
    @patch.object(roller, 'compile', Mock(return_value=sentinel))
    @patch.object(roller, 'basic')
    def test_average(self, basic: Mock):
        basic.return_value = 5
        roller.main()
        self.assertEqual(self.stdout.getvalue().strip(), '5')
        basic.assert_called_with(sentinel, roller.Mode.AVERAGE)

    @patch.object(roller, 'parse')
    @patch.object(roller, 'compile', Mock(return_value=sentinel))
    @patch.object(roller, 'basic')
    def test_critical(self, basic: Mock, parse: Mock):
        basic.return_value = 5
        parse.return_value = base_args(critical=True)
        roller.main()
        basic.assert_called_with(sentinel, roller.Mode.CRIT)
        parse.return_value = base_args(critical=True, average=True)
        roller.main()
        basic.assert_called_with(sentinel, roller.Mode.CRIT)

    @patch.object(roller, 'parse')
    @patch.object(roller, 'compile', Mock(return_value=sentinel))
    @patch.object(roller, 'basic')
    def test_max(self, basic: Mock, parse: Mock):
        basic.return_value = 5
        parse.return_value = base_args(maximum=True)
        roller.main()
        basic.assert_called_with(sentinel, roller.Mode.MAX)
        parse.return_value = base_args(maximum=True, average=True)
        roller.main()
        basic.assert_called_with(sentinel, roller.Mode.MAX)
        parse.return_value = base_args(maximum=True, critical=True, average=True)
        roller.main()
        basic.assert_called_with(sentinel, roller.Mode.MAX)

    @patch.object(roller, 'parse', Mock(return_value=base_args(number=500)))
    @patch.object(roller, 'basic', Mock(return_value=5))
    def test_wrap(self):
        roller.main()
        lines = self.stdout.getvalue().split('\n')
        self.assertLessEqual(max(len(line) for line in lines), 80)

    @patch.object(roller, 'parse', Mock(return_value=base_args(number=500, wrap=0)))
    @patch.object(roller, 'basic', Mock(return_value=5))
    def test_wrap_off(self):
        roller.main()
        output = self.stdout.getvalue().strip()
        self.assertEqual(len(output), 999)

    @patch.object(roller, 'parse', Mock(return_value=base_args(verbose=True)))
    @patch.object(roller, 'compile', Mock(return_value=sentinel))
    @patch.object(roller, 'verbose')
    def test_verbose(self, verbose):
        verbose.return_value = '5 = 5'
        roller.main()
        self.assertEqual(self.stdout.getvalue().strip(), '5 = 5')
        verbose.assert_called_with(sentinel, roller.Mode.NORMAL)
