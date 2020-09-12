import enum
import typing

from .lib.evaltree import EvalTree, EvalTreeNode
from .lib.exceptions import InputTypeError
from .lib.operators import OPERATORS
from .lib.tokenizer import Token, tokens_lazy


class Mode(enum.Enum):
    """Change the way that a roll is performed.

    Average makes each die give back the average value, which ends up
    with halves for the normal even-sided dice. Critical causes a roll
    to be like the damage roll of a critical hit, which means roll each
    die twice as many times. Max makes each die give its maximum value.
    This isn't really used as far as I can tell.

    Higher modes overwrite lower, so MAX supersedes CRIT which
    supersedes AVERAGE.
    """
    NORMAL = 0
    AVERAGE = 1
    CRIT = 2
    MAX = 3

    @classmethod
    def from_string(cls, string: str) -> 'Mode':
        """Get an enum value from a string, defaulting to NORMAL."""
        encode = {
            'average': cls.AVERAGE,
            'critical': cls.CRIT,
            'maximum': cls.MAX,
        }
        return encode.get(string.lower(), cls.NORMAL)


def _add_modifiers(tree: EvalTree, modifiers) -> EvalTree:
    # Manually stick the + <modifier> onto the root of the tree so it gets evaluated at the end
    tree.root = EvalTreeNode(OPERATORS['+'],
                             tree.root,
                             EvalTreeNode(modifiers))
    return tree


def verbose(expr: typing.Union[str, int, float, EvalTree], mode: Mode = Mode.NORMAL,
            modifiers=0) -> str:
    """Create a string that shows the actual values rolled alongside the final value.

    :param expr: The rollable string or precompiled expression tree.
    :param mode: Roll this as an average, a critical hit, or to find the
        maximum value.
    :param modifiers: A number that can be added on to the expression at
        the very end.
    :return: A string showing the expression with rolls evaluated
        alongside the final result.
    """
    if not isinstance(expr, (str, int, float, EvalTree)):
        raise InputTypeError("This function can only take a rollable string, a number, or a "
                             "compiled evaluation tree.")
    tree = EvalTree(expr)
    if mode:
        if mode == Mode.AVERAGE:
            tree.averageify()
        if mode == Mode.CRIT:
            tree.critify()
        if mode == Mode.MAX:
            tree.maxify()
    if modifiers != 0:
        _add_modifiers(tree, modifiers)
    tree.evaluate()
    return tree.verbose_result()


def compile(expr: typing.Union[str, int, float], modifiers=0) -> EvalTree:
    """Parse an expression into an evaluation tree to save time at later executions.

    You want to use this when the particular expression is going to be
    used many times. For instance, for D&D, d20 rolls, possibly with
    advantage or disadvantage, are used all over. Precompiling those and
    referencing the compiled versions is therefore very likely to be
    worth the extra step.

    :param expr: The rollable string.
    :param modifiers: A number that can be added on to the expression at
        the very end.
    :return: An evaluation tree that can be passed to one of the roll
        functions or be manipulated on its own.
    """
    if not isinstance(expr, (str, int, float)):
        raise InputTypeError("You can only compile a string or a number into an EvalTree.")
    tree = EvalTree(expr)
    if modifiers != 0:
        _add_modifiers(tree, modifiers)
    return tree


def basic(expr: typing.Union[str, int, float, EvalTree], mode: Mode = Mode.NORMAL,
          modifiers=0) -> typing.Union[int, float]:
    """Roll an expression and return just the end result.

    :param expr: The rollable string or precompiled expression tree.
    :param mode: Roll this as an average, a critical hit, or to find the
        maximum value.
    :param modifiers: A number that can be added on to the expression at
        the very end.
    :return: The final number that is calculated.
    """
    if isinstance(expr, (int, float)):
        return expr + modifiers
    if not isinstance(expr, (str, EvalTree)):
        raise InputTypeError("This function can only take a rollable string, a number, or a "
                             "compiled evaluation tree.")
    tree = EvalTree(expr)
    if mode:
        if mode == Mode.AVERAGE:
            tree.averageify()
        if mode == Mode.CRIT:
            tree.critify()
        if mode == Mode.MAX:
            tree.maxify()
    return tree.evaluate() + modifiers


def tokenize(expr: typing.Union[str, int, float], modifiers=0) -> typing.List[Token]:
    """Split a string into tokens, which can be operators or numbers.

    :param expr: The string to be parsed.
    :param modifiers: A value to be added on at the very end. The
        semantics are like (expr)+modifiers.
    :return: The list of tokens.
    """
    return list(tokenize_lazy(expr, modifiers))


def tokenize_lazy(expr: typing.Union[str, int, float], modifiers=0) -> typing.Iterator[Token]:
    """Split a string into tokens and yield them lazily.

    :param expr: The string to be parsed.
    :param modifiers: A value to be added on at the very end. The
        semantics are like (expr)+modifiers.
    :return: An iterable of the tokens parsed from the string.
    """
    if isinstance(expr, (int, float)):
        yield expr
        if modifiers != 0:
            yield OPERATORS['+']
            yield modifiers
        return
    if not isinstance(expr, str):
        raise InputTypeError("You can only tokenize a string expression or a number.")
    if modifiers != 0:
        yield '('
    yield from tokens_lazy(expr)
    if modifiers != 0:
        yield ')'
        yield OPERATORS['+']
        yield modifiers


