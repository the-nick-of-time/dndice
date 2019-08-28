import itertools
import unittest

from dndice import basic, Mode, compile, tokenize
from dndice.lib.evaltree import EvalTree, EvalTreeNode
from dndice.lib.operators import OPERATORS, random


def trees_equal(a: EvalTree, b: EvalTree) -> bool:
    for nodeA, nodeB in itertools.zip_longest(a.pre_order(), b.pre_order(), fillvalue=EvalTreeNode(None)):
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
        self.assertEqual(basic('3d4', mode=Mode.MAX), 12)
        self.assertEqual(basic('3d4', mode=Mode.CRIT), 24)
        self.assertEqual(basic('3d4', modifiers=4), 16)

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

    def test_verbose(self):
        pass

    def test_tokenize(self):
        expr = '3d4+2'
        self.assertEqual(tokenize(expr), [3, OPERATORS['d'], 4, OPERATORS['+'], 2])
        toks = ['(', 3, OPERATORS['d'], 4, OPERATORS['+'], 2, ')', OPERATORS['+'], 2]
        self.assertEqual(tokenize(expr, 2), toks)


if __name__ == '__main__':
    unittest.main()
