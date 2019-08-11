import enum
import typing

from exceptions import InputTypeError
from operators import OPERATORS, Operator, Side, Roll
from tokenize_flat import tokens, Token

Result = typing.Union[Roll, int, float]
Final = typing.Union[int, float]


class Mode(enum.Flag):
    """Modifications to make to the roll expression before evaluation.

    As a flag enum that can encode several modes at once, you want to check the state of `mode & Mode.<CONSTANT>`.
    """
    NORMAL = 0
    AVERAGE = 1
    CRIT = 2
    MAX = 4


class EvalTreeNode:
    def __init__(self, payload: Token, left=None, right=None):
        self.payload: Token = payload
        self.left: EvalTreeNode = left
        self.right: EvalTreeNode = right
        self.value: typing.Union[Result, None] = None

    def evaluate(self) -> Result:
        """Recursively evaluate this subtree and annotate this node with its computed value.

        :return: The value computed.
        """
        if self.is_leaf():
            # Leaves are guaranteed to be concrete values
            self.value = self.payload
            return self.value
        else:
            self.value = self.payload(self.left and self.left.evaluate(), self.right and self.right.evaluate())
            return self.value

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class EvalTree:
    def __init__(self, source: typing.Union[str, typing.List[Token], 'EvalTree', None]):
        self.root: typing.Union[EvalTreeNode, None] = None
        if isinstance(source, str):
            self.from_tokens(tokens(source))
        elif isinstance(source, EvalTree):
            self.root = source.root
        elif isinstance(source, list):
            self.from_tokens(source)
        elif source is None:
            # Explicitly do nothing; leave us with an empty tree
            pass
        else:
            raise InputTypeError(f"You can't construct an EvalTree from type {type(source)}")

    def evaluate(self) -> Final:
        """Recursively evaluate the tree

        :return: The single final value from the tree
        """
        final = self.root.evaluate()
        if isinstance(final, Roll):
            final = final.sum()
        return final

    def from_tokens(self, tokens: typing.List[Token]) -> None:
        """Construct and take possession of the expression tree formed from the infix token list

        :param tokens: The list of tokens parsed from the infix expression
        """
        expression: typing.List[EvalTreeNode] = []
        operators: typing.List[Operator] = []
        for t in tokens:
            if isinstance(t, (int, tuple)):
                expression.append(EvalTreeNode(t))
            elif t == '(':
                operators.append(t)
            elif t == ')':
                while operators[-1] != '(':
                    self.one_operation(operators, expression)
                operators.pop()
            else:
                while (len(operators)
                       and isinstance(operators[-1], Operator)
                       and (operators[-1] > t
                            or (operators[-1].precedence == t.precedence
                                and operators[-1].associativity == Side.LEFT))):
                    self.one_operation(operators, expression)
                operators.append(t)
        while len(operators):
            self.one_operation(operators, expression)
        self.root = expression.pop()

    @staticmethod
    def one_operation(ops: typing.List[Operator], values: typing.List[EvalTreeNode]):
        """Pop the top operator and give it the top one or two subtrees from the values stack as children
        Then push the resulting subtree onto the values stack for application in future

        :param ops: The current stack of operators
        :param values: The current stack of values
        """
        current = ops.pop()
        node = EvalTreeNode(current)
        if current.arity & Side.RIGHT:
            node.right = values.pop()
        if current.arity & Side.LEFT:
            node.left = values.pop()
        values.append(node)

    def verbose_result(self) -> str:
        """Forms an infix expression of the result, basically looking like the original but with rolls evaluated.

        Note that parentheses are discarded in the parsing step so the output may not match the input when there was
        a parenthetical expression.

        :return: A string representation of the result, showing the results from rolls.
        """
        if self.root.value is None:
            self.evaluate()
        base = self.__verbose_result_recursive(self.root, 6)
        try:
            final = sum(self.root.value)
        except TypeError:
            final = self.root.value
        return base + ' = ' + str(final)

    def __verbose_result_recursive(self, current: EvalTreeNode, threshold: int) -> str:
        """Perform an in-order traversal to build the string of the result."""
        if current is None:
            return ''
        if current.is_leaf() or current.payload.precedence >= threshold:
            return str(current.value)
        return (self.__verbose_result_recursive(current.left, threshold)
                + str(current.payload)
                + self.__verbose_result_recursive(current.right, threshold))

    def pre_order(self) -> typing.Generator[EvalTreeNode, None, None]:
        return self.__pre_order_recursive(self.root)

    def __pre_order_recursive(self, current: EvalTreeNode) -> typing.Generator[EvalTreeNode, None, None]:
        yield current
        if current.left:
            yield self.__pre_order_recursive(current.left)
        if current.right:
            yield self.__pre_order_recursive(current.right)

    def critify(self):
        """Modify rolls in this expression to critical rolls.

        :rtype: EvalTree
        """
        # Note: crit is superseded by maximum
        # Though why you're using roll_max anyway is a mystery
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da':
                node.payload = OPERATORS['dc']
        return self

    def averageify(self):
        """Modify rolls in this expression to average rolls.

        :rtype: EvalTree
        """
        # Note: average is superseded by crit or max
        for node in self.pre_order():
            if node.payload == 'd':
                node.payload = OPERATORS['da']
        return self

    def maxify(self):
        """Modify rolls in this expression to maximum rolls.

        :rtype: EvalTree
        """
        # Max supersedes all
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da' or node.payload == 'dc':
                node.payload = OPERATORS['dm']
        return self

    def is_critical(self):
        """Checks if this roll contains a d20 roll that is a natural 20"""
        for node in self.pre_order():
            if node.payload == 'd' and node.right.payload == [20] and node.value == 20:
                return True
        return False

    def is_fail(self):
        """Checks if this roll contains a d20 roll that is a natural 1"""
        for node in self.pre_order():
            if node.payload == 'd' and node.right.payload == [1] and node.value == 20:
                return True
        return False


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
        if isinstance(expr, str):
            if modifiers != 0:
                tree = EvalTree("{}+{}".format(expr, modifiers))
            else:
                tree = EvalTree(expr)
        elif isinstance(expr, EvalTree):
            tree = expr
        elif isinstance(expr, list):
            tree = EvalTree(expr + ([OPERATORS['+'], modifiers] if modifiers != 0 else []))
        else:
            raise TypeError("Expression must be a string, list of tokens, or already compiled evaluation tree")
        return tree.verbose_result()
    elif option == 'multipass_critical':
        if modifiers != 0:
            tree = EvalTree("{}+{}".format(expr, modifiers))
        else:
            tree = EvalTree(expr)
        tree.critify()
        return tree.verbose_result()
    elif option == 'compile':
        if isinstance(expr, EvalTree):
            return expr
        if isinstance(expr, str):
            if modifiers != 0:
                tree = EvalTree("{}+{}".format(expr, modifiers))
            else:
                tree = EvalTree(expr)
        elif isinstance(expr, list):
            tree = EvalTree(expr + ([OPERATORS['+'], modifiers] if modifiers != 0 else []))
        else:
            raise TypeError("Expression must be a string, list of tokens, or already compiled evaluation tree")
        return tree
    elif option == 'tokenize':
        if isinstance(expr, str):
            return tokens(expr)
        elif isinstance(expr, list):
            return expr
        else:
            raise TypeError("Cannot fully reconstruct expression from compiled form")
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
    if modifiers != 0:
        _add_modifiers(tree, modifiers)
    return tree.evaluate()


def tokenize(expr: str, modifiers=0) -> typing.List[Token]:
    if not isinstance(expr, str):
        raise InputTypeError("You can only tokenize a string expression.")
    tok = tokens(expr)
    if modifiers != 0:
        tok.extend((OPERATORS['+'], modifiers))
    return tok


if __name__ == '__main__':
    testCases = ["1d4+1",
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
