import pytest

from dndice import basic, Mode, compile, tokenize, verbose, tokenize_lazy
from dndice.lib.evaltree import EvalTree, EvalTreeNode
from dndice.lib.exceptions import InputTypeError
from dndice.lib.operators import OPERATORS, Roll
# noinspection PyUnresolvedReferences
from tests.utilities import tree_empty, mock_randint, tree_eq


@pytest.mark.parametrize("roll,mode,modifiers,expected", [
    ('3d4', Mode.NORMAL, 0, 22),
    ('3d4', Mode.AVERAGE, 0, 7.5),
    ('3d6', Mode.MAX, 0, 18),
    ('3d4', Mode.CRIT, 0, 63),
    ('3d4', Mode.NORMAL, 4, 26),
    (2, Mode.NORMAL, 0, 2),
    (2, Mode.NORMAL, 4, 6),
])
def test_basic(roll, mode, modifiers, expected, mock_randint):
    assert basic(roll, mode, modifiers) == expected


def test_basic_type_error():
    with pytest.raises(InputTypeError):
        basic([40, 2])


def test_compile(tree_eq, mock_randint):
    tree = compile('3d4')
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['d'],
                                 EvalTreeNode(3),
                                 EvalTreeNode(4))
    assert tree == expected


def test_compile_modifier(tree_eq, mock_randint):
    expected = EvalTree(None)
    expected.root = EvalTreeNode(OPERATORS['+'],
                                 EvalTreeNode(OPERATORS['d'],
                                              EvalTreeNode(3),
                                              EvalTreeNode(4)),
                                 EvalTreeNode(2))
    assert compile('3d4', 2) == expected


def test_compile_int(tree_eq, mock_randint):
    expected = EvalTree(None)
    expected.root = EvalTreeNode(2)
    assert compile(2) == expected
    expected.root = EvalTreeNode(OPERATORS['+'],
                                 EvalTreeNode(2),
                                 EvalTreeNode(4))
    assert compile(2, 4) == expected


def test_compile_wrong_type(mock_randint):
    with pytest.raises(InputTypeError):
        compile([40, 2])


def test_verbose(mock_randint):
    expected = '{roll}+2 = 24'.format(roll=Roll([1, 20, 1], 4))
    assert verbose('3d4 + 2') == expected


def test_verbose_modifier(mock_randint):
    expected = '{roll}+2+1 = 25'.format(roll=Roll([1, 20, 1], 4))
    assert verbose('3d4 + 2', modifiers=1) == expected


def test_verbose_average(mock_randint):
    expected = '{}+2 = 9.5'.format(Roll([2.5, 2.5, 2.5], 4))
    assert verbose('3d4+2', mode=Mode.AVERAGE) == expected


def test_verbose_max(mock_randint):
    expected = '{}+2 = 20'.format(Roll([6, 6, 6], 6))
    assert verbose('3d6+2', mode=Mode.MAX) == expected


def test_verbose_crit(mock_randint):
    expected = '{}+2 = 65'.format(Roll([1, 1, 1, 20, 20, 20], 4))
    assert verbose('3d4+2', mode=Mode.CRIT) == expected


def test_verbose_wrong_type():
    with pytest.raises(InputTypeError):
        verbose([40, 2])


def test_tokenize():
    assert tokenize('3d4+2') == [3, OPERATORS['d'], 4, OPERATORS['+'], 2]


def test_tokenize_modifier():
    toks = ['(', 3, OPERATORS['d'], 4, OPERATORS['+'], 2, ')', OPERATORS['+'], 2]
    assert tokenize('3d4+2', 2) == toks


def test_tokenize_int():
    assert tokenize(1) == [1]


def test_tokenize_int_modifier():
    assert tokenize(1, 1) == [1, OPERATORS['+'], 1]


def test_tokenize_wrong_type():
    with pytest.raises(InputTypeError):
        tokenize([40, 2])


def test_mode():
    assert Mode.from_string('average') == Mode.AVERAGE
    assert Mode.from_string('critical') == Mode.CRIT
    assert Mode.from_string('maximum') == Mode.MAX
    assert Mode.from_string('normal') == Mode.NORMAL
    assert Mode.from_string('random') == Mode.NORMAL


def test_lazy():
    iterator = tokenize_lazy('3d4+2')
    assert next(iterator) == 3
    assert next(iterator) == OPERATORS['d']
    assert next(iterator) == 4
    assert next(iterator) == OPERATORS['+']
    assert next(iterator) == 2
    with pytest.raises(StopIteration):
        next(iterator)


def test_lazy_modifier():
    iterator = tokenize_lazy('3d4+2', 1)
    assert next(iterator) == '('
    assert next(iterator) == 3
    assert next(iterator) == OPERATORS['d']
    assert next(iterator) == 4
    assert next(iterator) == OPERATORS['+']
    assert next(iterator) == 2
    assert next(iterator) == ')'
    assert next(iterator) == OPERATORS['+']
    assert next(iterator) == 1
    with pytest.raises(StopIteration):
        next(iterator)


def test_lazy_int():
    iterator = tokenize_lazy(1)
    assert next(iterator) == 1
    with pytest.raises(StopIteration):
        next(iterator)


def test_lazy_int_modifier():
    iterator = tokenize_lazy(1, 1)
    assert next(iterator) == 1
    assert next(iterator) == OPERATORS['+']
    assert next(iterator) == 1
    with pytest.raises(StopIteration):
        next(iterator)


def test_lazy_wrong_type():
    with pytest.raises(InputTypeError):
        iterator = tokenize_lazy([40, 2])
        next(iterator)
