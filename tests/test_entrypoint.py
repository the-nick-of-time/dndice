import itertools
import unittest

from dndice import basic, Mode, compile, tokenize, verbose
from dndice.lib.evaltree import EvalTree, EvalTreeNode
from dndice.lib.operators import OPERATORS, random, Roll
from dndice.lib.exceptions import InputTypeError


def trees_equal(a: EvalTree, b: EvalTree) -> bool:
    for nodeA, nodeB in itertools.zip_longest(a.pre_order(), b.pre_order(),
                                              fillvalue=EvalTreeNode(None)):
        if nodeA.payload != nodeB.payload:
            return False
    return True


class TestCoreFunctions(unittest.TestCase):
    def setUp(self) -> None:
        random.randint = lambda start, end: 4  # The most random number, https://xkcd.com/221/
        EvalTree.__eq__ = trees_equal

    def test_basic(self):
        self.assertEqual(basic('3d4'), 12)
        self.assertEqual(basic('3d4', mode=Mode.AVERAGE), 7.5)
        self.assertEqual(basic('3d6', mode=Mode.MAX), 18)
        self.assertEqual(basic('3d4', mode=Mode.CRIT), 24)
        self.assertEqual(basic('3d4', modifiers=4), 16)
        self.assertEqual(basic(2), 2)
        self.assertEqual(basic(2, modifiers=4), 6)
        with self.assertRaises(InputTypeError):
            basic([40, 2])

    def test_compile(self):
        expr = '3d4'
        tree = compile(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(3),
                                     EvalTreeNode(4))
        self.assertEqual(tree, expected)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(3),
                                                  EvalTreeNode(4)),
                                     EvalTreeNode(2))
        self.assertEqual(compile(expr, 2), expected)
        expected.root = EvalTreeNode(2)
        self.assertEqual(compile(2), expected)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(2),
                                     EvalTreeNode(4))
        self.assertEqual(compile(2, 4), expected)
        with self.assertRaises(InputTypeError):
            compile([40, 2])

    def test_verbose(self):
        expected = '{roll}+2 = 14'.format(roll=Roll([4, 4, 4], 4))
        self.assertEqual(verbose('3d4 + 2'), expected)
        expected = '{roll}+2+1 = 15'.format(roll=Roll([4, 4, 4], 4))
        self.assertEqual(verbose('3d4 + 2', modifiers=1), expected)
        expected = '{}+2 = 9.5'.format(Roll([2.5, 2.5, 2.5], 4))
        self.assertEqual(verbose('3d4+2', mode=Mode.AVERAGE), expected)
        expected = '{}+2 = 20'.format(Roll([6, 6, 6], 6))
        self.assertEqual(verbose('3d6+2', mode=Mode.MAX), expected)
        expected = '{}+2 = 26'.format(Roll([4, 4, 4, 4, 4, 4], 4))
        self.assertEqual(verbose('3d4+2', mode=Mode.CRIT), expected)
        with self.assertRaises(InputTypeError):
            verbose([40, 2])

    def test_tokenize(self):
        expr = '3d4+2'
        self.assertEqual(tokenize(expr), [3, OPERATORS['d'], 4, OPERATORS['+'], 2])
        toks = ['(', 3, OPERATORS['d'], 4, OPERATORS['+'], 2, ')', OPERATORS['+'], 2]
        self.assertEqual(tokenize(expr, 2), toks)
        self.assertEqual(tokenize(1), [1])
        self.assertEqual(tokenize(1, 1), [1, OPERATORS['+'], 1])
        with self.assertRaises(InputTypeError):
            tokenize([40, 2])

    def test_mode(self):
        self.assertEqual(Mode.from_string('average'), Mode.AVERAGE)
        self.assertEqual(Mode.from_string('critical'), Mode.CRIT)
        self.assertEqual(Mode.from_string('maximum'), Mode.MAX)
        self.assertEqual(Mode.from_string('normal'), Mode.NORMAL)
        self.assertEqual(Mode.from_string('random'), Mode.NORMAL)


if __name__ == '__main__':
    unittest.main()
