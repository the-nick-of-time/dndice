import unittest
import itertools

from dndice.lib.evaltree import EvalTreeNode, EvalTree
from dndice.lib.exceptions import ParseError, EvaluationError
from dndice.lib.operators import OPERATORS


def trees_equal(a: EvalTree, b: EvalTree) -> bool:
    for nodeA, nodeB in itertools.zip_longest(a.pre_order(), b.pre_order(), fillvalue=EvalTreeNode(None)):
        if nodeA.payload != nodeB.payload:
            return False
    return True


# patch this thing in
EvalTree.__eq__ = trees_equal


class TreeTester(unittest.TestCase):
    def test_node(self):
        node = EvalTreeNode(4)
        self.assertEqual(node.payload, 4)
        self.assertIs(node.left, None)
        self.assertIs(node.right, None)
        self.assertIs(node.value, None)
        node.evaluate()
        self.assertEqual(node.payload, node.value)

    def test_tree_simple_parse(self):
        expr = '4d6'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(6))
        self.assertEqual(tree, expected)

    def test_tree_basic_precedence(self):
        expr = '2d6 + 5*2^2'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(6)),
                                     EvalTreeNode(OPERATORS['*'],
                                                  EvalTreeNode(5),
                                                  EvalTreeNode(OPERATORS['^'],
                                                               EvalTreeNode(2),
                                                               EvalTreeNode(2))))
        self.assertEqual(tree, expected)

    def test_tree_associativity(self):
        expr = '3+4-5'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['-'],
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(3),
                                                  EvalTreeNode(4)),
                                     EvalTreeNode(5))
        self.assertEqual(tree, expected)
        expr = '3 ^ 2 ^ 4'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['^'],
                                     EvalTreeNode(3),
                                     EvalTreeNode(OPERATORS['^'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(4)))
        self.assertEqual(tree, expected)

    def test_tree_parentheses(self):
        expr = '3+(8-5)'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(3),
                                     EvalTreeNode(OPERATORS['-'],
                                                  EvalTreeNode(8),
                                                  EvalTreeNode(5)))
        self.assertEqual(tree, expected)

    def test_parse_failure(self):
        expr = '4d6+2+'
        with self.assertRaises(ParseError):
            EvalTree(expr)

    def test_eval_failure(self):
        expr = '2d20h(7/2)'
        with self.assertRaises(EvaluationError):
            EvalTree(expr).evaluate()


if __name__ == '__main__':
    unittest.main()
