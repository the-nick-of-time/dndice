import enum
import typing

try:
    # script version
    from lib.exceptions import InputTypeError
    from lib.operators import OPERATORS
    from lib.tokenizer import tokens, Token
    from lib.evaltree import EvalTree, EvalTreeNode
except ImportError:
    # module version
    from .lib.exceptions import InputTypeError
    from .lib.operators import OPERATORS
    from .lib.tokenizer import tokens, Token
    from .lib.evaltree import EvalTree, EvalTreeNode


class Mode(enum.IntFlag):
    """Modifications to make to the roll expression before evaluation.

    As a flag enum that can encode several modes at once, you want to check the state of `mode & Mode.<CONSTANT>`.
    """
    NORMAL = 0b000
    AVERAGE = 0b001
    CRIT = 0b010
    MAX = 0b100

    @classmethod
    def from_string(cls, string: str) -> 'Mode':
        encode = {
            'average': cls.AVERAGE,
            'critical': cls.CRIT,
            'maximum': cls.MAX,
        }
        return encode.get(string.lower(), cls.NORMAL)


def _add_modifiers(tree: EvalTree, modifiers) -> EvalTree:
    # Manually stick the + <modifier> onto the root of the tree so it gets evaluated at the end
    new = EvalTree(None)
    plus = EvalTreeNode(OPERATORS['+'])
    number = EvalTreeNode(modifiers)
    plus.right = number
    new.root = plus
    new.root.left = tree.root
    return new


# NOTE/WARNING: Modifiers being nonzero when the original roll involves anything with lower precedence
# will produce results that are probably not as intended. The modifiers are added at the very end
# so if you're looking at the output of boolean or comparison operators you will see more.
def roll(expr: typing.Union[str, typing.List[Token], EvalTree], modifiers=0, option='execute') -> \
        typing.Union[int, float, str, typing.List[Token], EvalTree]:
    """Roll dice and do arithmetic."""
    if isinstance(expr, (float, int)):
        # If you're naughty and pass a number in...
        # it really doesn't matter.
        return expr + modifiers
    elif expr == '':
        return 0 + modifiers
    elif option == 'execute':
        return EvalTree(expr).evaluate() + modifiers
    elif option == 'critical':
        return EvalTree(expr).critify().evaluate() + modifiers
    elif option == 'average':
        return EvalTree(expr).averageify().evaluate() + modifiers
    elif option == 'multipass':
        return verbose(expr, modifiers=modifiers)
    elif option == 'multipass_critical':
        return verbose(expr, Mode.CRIT, modifiers)
    elif option == 'compile':
        return compile(expr, modifiers)
    elif option == 'tokenize':
        return tokenize(expr, modifiers)
    elif option == 'from_tokens':
        if isinstance(expr, list):
            tree = EvalTree(expr + ([OPERATORS['+'], modifiers] if modifiers != 0 else []))
            return tree.evaluate()
        else:
            raise TypeError("You need to actually pass tokens in")
    elif option == 'zero':
        return 0


def verbose(expr: typing.Union[str, EvalTree], mode: Mode = Mode.NORMAL, modifiers=0) -> str:
    if not isinstance(expr, (str, EvalTree)):
        raise InputTypeError("This function can only take a rollable string or a compiled evaluation tree.")
    tree = EvalTree(expr)
    if mode:
        if mode & Mode.AVERAGE:
            tree.averageify()
        if mode & Mode.CRIT:
            tree.critify()
        if mode & Mode.MAX:
            tree.maxify()
    if modifiers != 0:
        _add_modifiers(tree, modifiers)
    tree.evaluate()
    return tree.verbose_result()


def compile(expr: str, modifiers=0) -> EvalTree:
    if not isinstance(expr, str):
        raise InputTypeError("You can only compile a string into an EvalTree.")
    tree = EvalTree(expr)
    if modifiers != 0:
        _add_modifiers(tree, modifiers)
    return tree


def basic(expr: typing.Union[str, EvalTree], mode: Mode = Mode.NORMAL, modifiers=0) -> typing.Union[int, float]:
    if not isinstance(expr, (str, EvalTree)):
        raise InputTypeError("This function can only take a rollable string or a compiled evaluation tree.")
    tree = EvalTree(expr)
    if mode:
        if mode & Mode.AVERAGE:
            tree.averageify()
        if mode & Mode.CRIT:
            tree.critify()
        if mode & Mode.MAX:
            tree.maxify()
    return tree.evaluate() + modifiers


def tokenize(expr: str, modifiers=0) -> typing.List[Token]:
    if not isinstance(expr, str):
        raise InputTypeError("You can only tokenize a string expression.")
    tok = tokens(expr)
    if modifiers != 0:
        tok.extend((OPERATORS['+'], modifiers))
    return tok


if __name__ == '__main__':
    testCases = [
        "1d4+1",
        "1d4-1",
        "2d20h1",
        "2d20l1",
        "40d20r1h1",
        "10d4r1",
        "10d4ro1",
        "10d4Ro1",
        "10d4R1",
        "1d4d4d4",
        "-5",
        "+1d4",
        "2*-1d4",
        "-2^1d4",
        "8d6/2",
        "1+(1+4)d6",
        "(1d6)!",
        "1d6!",
        "1d100<14",
        "1d100<=18",
        "8d6f2",
        "1d20+5>10",
        "5d20r<15",
        "5d20R<15",
        "(1d4-1)&(1d3-2>0)",
        "(1d4-1)|(1d3-2>0)",
        "1dc8+1dc4+3",
        "1dm6+1d6",
        "2d4c2",
        "2da6",
        "3da6",
        "2d10%2",
        "1d4=4|1d4=3",
        "1d8>=6",
        "10d8r>4",
        "10d8R>4",
        "10d[3,3,3,5]",
        "10d[3, 3, 3, 5]",
        "15d6t5",
        "15d6T1",
    ]
    for expr in testCases:
        tree = EvalTree(expr)
        print('EVALUATING ' + expr)
        print('EVALUATING USING TREE DIRECTLY')
        print(tree.evaluate())
        print('EVALUATING USING ROLL FUNCTION')
        print(roll(expr))
        print('EVALUATING USING ROLL FUNCTION IN MULTIPASS MODE')
        print(roll(expr, option='multipass'))
        print('EVALUATING USING ROLL FUNCTION AND MODIFIER')
        print(roll(expr, 3))
        print('EVALUATING USING ROLL FUNCTION IN MULTIPASS MODE AND MODIFIER')
        print(roll(expr, 3, option='multipass'))
        print()
