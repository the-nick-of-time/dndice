import pytest

from dndice.lib.evaltree import EvalTreeNode, EvalTree
from dndice.lib.exceptions import EvaluationError, InputTypeError
from dndice.lib.operators import OPERATORS, Roll


def tree_empty(tree: EvalTree) -> bool:
    for node in tree.pre_order():
        if node.value is not None:
            return False
    return True


def test_node():
    node = EvalTreeNode(4)
    assert node.payload == 4
    assert node.left is None
    assert node.right is None
    assert node.value is None
    node.evaluate()
    assert node.payload == node.value


def test_tree_from_tokens(tree_eq):
    fromTokens = EvalTree([4, OPERATORS['d'], 6])
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['d'],
                                 EvalTreeNode(4),
                                 EvalTreeNode(6))
    assert fromTokens == expected


def test_tree_from_existing(tree_eq):
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['d'],
                                 EvalTreeNode(4),
                                 EvalTreeNode(6))
    fromExisting = EvalTree(expected)
    assert fromExisting == expected


def test_tree_wrong_type():
    with pytest.raises(InputTypeError):
        EvalTree({'invalid'})


def test_empty_tree_evaluate():
    assert EvalTree(None).evaluate() == 0


def test_tree_simple_parse(tree_eq):
    expr = '4d6'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['d'],
                                 EvalTreeNode(4),
                                 EvalTreeNode(6))
    assert tree == expected


def test_tree_basic_precedence(tree_eq):
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
    assert tree == expected


def test_tree_associativity(tree_eq):
    expr = '3+4-5'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['-'],
                                 EvalTreeNode(OPERATORS['+'],
                                              EvalTreeNode(3),
                                              EvalTreeNode(4)),
                                 EvalTreeNode(5))
    assert tree == expected
    expr = '3 ^ 2 ^ 4'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['^'],
                                 EvalTreeNode(3),
                                 EvalTreeNode(OPERATORS['^'],
                                              EvalTreeNode(2),
                                              EvalTreeNode(4)))
    assert tree == expected


def test_tree_parentheses(tree_eq):
    expr = '3+(8-5)'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['+'],
                                 EvalTreeNode(3),
                                 EvalTreeNode(OPERATORS['-'],
                                              EvalTreeNode(8),
                                              EvalTreeNode(5)))
    assert tree == expected


def test_tree_unnecessary_parentheses(tree_eq):
    expr = '2*((8)+(4))'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['*'],
                                 EvalTreeNode(2),
                                 EvalTreeNode(OPERATORS['+'],
                                              EvalTreeNode(8),
                                              EvalTreeNode(4)))
    assert tree == expected
    expr = '((3))'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(3)
    assert tree == expected


def test_unary_prefix(tree_eq):
    expr = '+3'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['p'],
                                 None,
                                 EvalTreeNode(3))
    assert tree == expected


def test_unary_suffix(tree_eq):
    expr = '4!'
    tree = EvalTree(expr)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['!'],
                                 EvalTreeNode(4))
    assert tree == expected


def test_tree_addition(tree_eq):
    expr1 = '2d20'
    tree1 = EvalTree(expr1)
    expr2 = '5+3'
    tree2 = EvalTree(expr2)
    tree = tree1 + tree2
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['+'],
                                 EvalTreeNode(OPERATORS['d'],
                                              EvalTreeNode(2),
                                              EvalTreeNode(20)),
                                 EvalTreeNode(OPERATORS['+'],
                                              EvalTreeNode(5),
                                              EvalTreeNode(3)))
    assert tree == expected
    tree1copy = EvalTree(None)
    tree1copy.root = EvalTreeNode(OPERATORS['d'],
                                  EvalTreeNode(2),
                                  EvalTreeNode(20))
    # Ensure that the original is untouched
    tree.evaluate()
    assert tree1 == tree1copy
    assert tree_empty(tree1)


def test_tree_in_place_addition(tree_eq):
    expr1 = '2d20'
    tree1 = EvalTree(expr1)
    expr2 = '5+3'
    tree2 = EvalTree(expr2)
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['+'],
                                 EvalTreeNode(OPERATORS['d'],
                                              EvalTreeNode(2),
                                              EvalTreeNode(20)),
                                 EvalTreeNode(OPERATORS['+'],
                                              EvalTreeNode(5),
                                              EvalTreeNode(3)))
    # Also test in-place concatenation
    tree1 += tree2
    assert tree1 == expected


def test_tree_addition_wrong_type(tree_eq):
    tree = EvalTree('2d20')
    with pytest.raises(InputTypeError):
        tree += 1
    with pytest.raises(InputTypeError):
        tree + 1


def test_tree_subtraction(tree_eq):
    expr1 = '2d20'
    tree1 = EvalTree(expr1)
    expr2 = '5+3'
    tree2 = EvalTree(expr2)
    tree = tree1 - tree2
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['-'],
                                 EvalTreeNode(OPERATORS['d'],
                                              EvalTreeNode(2),
                                              EvalTreeNode(20)),
                                 EvalTreeNode(OPERATORS['+'],
                                              EvalTreeNode(5),
                                              EvalTreeNode(3)))
    assert tree == expected
    tree1copy = EvalTree(None)
    tree1copy.root = EvalTreeNode(OPERATORS['d'],
                                  EvalTreeNode(2),
                                  EvalTreeNode(20))
    # Ensure that the original is untouched
    tree.evaluate()
    assert tree1 == tree1copy
    assert tree_empty(tree1)


def test_tree_in_place_subtraction(tree_eq):
    expr1 = '2d20'
    tree1 = EvalTree(expr1)
    expr2 = '5+3'
    tree2 = EvalTree(expr2)
    # Also test in-place concatenation
    tree1 -= tree2
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['-'],
                                 EvalTreeNode(OPERATORS['d'],
                                              EvalTreeNode(2),
                                              EvalTreeNode(20)),
                                 EvalTreeNode(OPERATORS['+'],
                                              EvalTreeNode(5),
                                              EvalTreeNode(3)))
    assert tree1 == expected


def test_tree_subtraction_wrong_type(tree_eq):
    expr = '2d20'
    tree = EvalTree(expr)
    with pytest.raises(InputTypeError):
        tree -= 1
    with pytest.raises(InputTypeError):
        tree - 1


def test_eval_failure(tree_eq):
    expr = '2d20h(7/2)'
    with pytest.raises(EvaluationError):
        EvalTree(expr).evaluate()


def test_critify(tree_eq):
    root = EvalTreeNode(OPERATORS['d'],
                        EvalTreeNode(1),
                        EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(20)))
    tree = EvalTree(None)
    tree.root = root
    tree.critify()
    assert tree.root.payload == OPERATORS['dc']
    assert tree.root.right.payload == OPERATORS['dc']


def test_maxify(tree_eq):
    root = EvalTreeNode(OPERATORS['d'],
                        EvalTreeNode(1),
                        EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(20)))
    tree = EvalTree(None)
    tree.root = root
    tree.maxify()
    assert tree.root.payload == OPERATORS['dm']
    assert tree.root.right.payload == OPERATORS['dm']


def test_averageify(tree_eq):
    root = EvalTreeNode(OPERATORS['d'],
                        EvalTreeNode(1),
                        EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(20)))
    tree = EvalTree(None)
    tree.root = root
    tree.averageify()
    assert tree.root.payload == OPERATORS['da']
    assert tree.root.right.payload == OPERATORS['da']


def test_is_critical(tree_eq, mock_randint):
    tree = EvalTree('2d20h1')
    tree.evaluate()
    assert tree.is_critical()
    assert not tree.is_fail()
    tree = EvalTree('10d20h5l2')
    tree.evaluate()
    assert not tree.is_critical()
    assert not tree.is_fail()


def test_is_fail(tree_eq, mock_randint):
    tree = EvalTree('2d20l1')
    tree.evaluate()
    assert tree.is_fail()
    assert not tree.is_critical()
    tree = EvalTree('1d20 + 1d20')
    tree.evaluate()
    assert tree.is_fail()
    assert tree.is_critical()


def test_copy(tree_eq, mock_randint):
    root = EvalTreeNode(OPERATORS['d'],
                        EvalTreeNode(1),
                        EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(20)))
    tree = EvalTree(None)
    tree.root = root
    tree.evaluate()
    copy = tree.copy()
    assert tree == copy
    assert tree is not copy
    for origNode, copyNode in zip(tree.pre_order(), copy.pre_order()):
        assert origNode is not copyNode
        # Avoid false positives from int interning
        if not isinstance(origNode.value, int):
            assert origNode.value is not copyNode.value
        if not isinstance(origNode.payload, int):
            assert origNode.payload is not copyNode.payload


def test_print_roll(mock_randint):
    root = EvalTreeNode(OPERATORS['+'],
                        EvalTreeNode(1),
                        EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(20)))
    tree = EvalTree(None)
    tree.root = root
    assert tree.verbose_result() == '1+' + str(Roll([1, 20, 1, 20], 20)) + ' = 43'


def test_print_empty():
    tree = EvalTree(None)
    assert tree.verbose_result() == ''


def test_print_unary():
    root = EvalTreeNode(OPERATORS['m'],
                        None,
                        EvalTreeNode(4))
    tree = EvalTree(None)
    tree.root = root
    assert tree.verbose_result() == '-4 = -4'
    # The other unary operator, !, has a high enough precedence to
    # be evaluated before printing so it isn't shown


def test_print_parentheses():
    root = EvalTreeNode(OPERATORS['*'],
                        EvalTreeNode(2),
                        EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(8)))
    tree = EvalTree(None)
    tree.root = root
    assert tree.verbose_result() == '2*(4+8) = 24'


def test_print_high_precedence():
    root = EvalTreeNode(OPERATORS['m'],
                        None,
                        EvalTreeNode(OPERATORS['!'],
                                     EvalTreeNode(5)))
    tree = EvalTree(None)
    tree.root = root
    # it evaluates ! before display because of its high precedence
    assert tree.verbose_result() == '-120 = -120'


def test_print_unnecessary_parentheses():
    tree = EvalTree('1+(2*4)')
    assert tree.verbose_result() == '1+2*4 = 9'


def test_in_order_roundtrip(tree_eq):
    tree = EvalTree('(2)*(4+8)')
    tokens = [node.payload for node in tree.in_order()]
    reconstructed = EvalTree(tokens)
    assert tree == reconstructed
