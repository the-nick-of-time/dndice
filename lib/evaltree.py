import typing

from .tokenizer import Token, tokens
from .exceptions import InputTypeError, EvaluationError, ParseError
from .helpers import wrap_exceptions_with
from .operators import OPERATORS, Roll, Operator, Side

Result = typing.Union[Roll, int, float]
Final = typing.Union[int, float]


class EvalTreeNode:
    """A node in the EvalTree, which can hold a value or operator."""
    __slots__ = 'payload', 'left', 'right', 'value'

    def __init__(self, payload: Token, left: 'EvalTreeNode' = None, right: 'EvalTreeNode' = None):
        """Initialize a new node in the expression tree.

        Leaf nodes (those with no left or right children) are guaranteed to hold concrete values while non-leaf nodes
        are guaranteed to hold operators.

        :param payload: The operator or value that is expressed by this node.
        :param left: The left child of this node, which holds the operand or expression to the left of this operator.
        :param right: The right child of this node, which holds the operand or expression to the right of this operator.
        """
        self.payload: Token = payload
        self.left: EvalTreeNode = left
        self.right: EvalTreeNode = right
        self.value: typing.Optional[Result] = None

    def evaluate(self) -> Result:
        r"""Recursively evaluate this subtree and annotate this node with its computed value.

        Along the way, the ``value`` of each node is set to the value of the expression at this stage, so it can be
        inspected later. This is used to great effect by the "verbose mode" of the main roll function.

        What is meant by "value of the expression at this stage can be shown through a diagram: ::

              -        < 0
            /  \
          *     +      < 1
        /  \  /  \
        4  5  1  2     < 2

        This is the tree that would result from the expression 4 * 5 - (1 + 2). If we were to start evaluating this
        tree, we would first recursively run down all three levels. Once reaching the leaves, their value is obvious:
        they are concrete already. Copy their ``payload`` into their ``value``. One level up, and we reach operators.
        The operator nodes receive values from each of their children, perform the operation they hold, and fill their
        ``value`` slot with the result. For instance, the '*' would perform 4 * 5 and store 20. This continues until the
        root is reached, and the final value is returned.

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
    """An expression tree that can be used to evaluate roll expressions.

    An `expression tree <https://en.wikipedia.org/wiki/Binary_expression_tree>`_ is, in short, a binary tree that holds
    an arithmetic expression. It is important to note that the binary tree not necessarily be complete; unary operators
    like factorial do create a tree where some leaf slots are unfilled, as they only take one operand instead of the two
    that most operators take.

    It is guaranteed that all leaf nodes hold a value (usually an integer) while all non-leaf nodes hold an operator.
    """
    __slots__ = 'root',

    def __init__(self, source: typing.Union[str, typing.List[Token], 'EvalTree', None]):
        """Initialize a tree of EvalTreeNodes that represent a given expression.

        :param source: The expression, generally as a string or already tokenized list or compiled tree.
        """
        self.root: typing.Optional[EvalTreeNode] = None
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

    @wrap_exceptions_with(EvaluationError, 'Failed to evaluate expression.')
    def evaluate(self) -> Final:
        """Recursively evaluate the tree.

        :return: The single final value from the tree.
        """
        final = self.root.evaluate()
        try:
            return sum(final)
        except TypeError:
            return final

    @wrap_exceptions_with(ParseError, 'Failed to construct an expression from the token list.')
    def from_tokens(self, tokens: typing.List[Token]) -> None:
        """Construct and take possession of the expression tree formed from the infix token list.

        This uses a `shunting-yard algorithm <https://en.wikipedia.org/wiki/Shunting-yard_algorithm>`_ to parse the
        infix token list into an expression tree. In relation to that algorithm, the "output" stack is populated with
        with subtrees that are progressively joined together using operators to create the final full tree.

        :param tokens: The list of tokens parsed from the infix expression.
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
        self.root = expression.pop() if len(expression) else EvalTreeNode(0)

    @staticmethod
    def one_operation(ops: typing.List[Operator], values: typing.List[EvalTreeNode]):
        """Pop the top operator and give it the top one or two subtrees from the values stack as children.
        Then push the resulting subtree onto the values stack for application in future.

        :param ops: The current stack of operators.
        :param values: The current stack of values.
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
        """Perform a pre-order/breadth-first traversal of the tree."""
        return self.__pre_order_recursive(self.root)

    def __pre_order_recursive(self, current: EvalTreeNode) -> typing.Generator[EvalTreeNode, None, None]:
        """Recurse through the tree."""
        yield current
        if current.left:
            yield from self.__pre_order_recursive(current.left)
        if current.right:
            yield from self.__pre_order_recursive(current.right)

    def critify(self) -> 'EvalTree':
        """Modify rolls in this expression to critical rolls.

        :return: This tree after it has been modified in-place.
        """
        # Note: crit is superseded by maximum
        # Though why you're using roll_max anyway is a mystery
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da':
                node.payload = OPERATORS['dc']
        return self

    def averageify(self) -> 'EvalTree':
        """Modify rolls in this expression to average rolls.

        :return: This tree after it has been modified in-place.
        """
        # Note: average is superseded by crit or max
        for node in self.pre_order():
            if node.payload == 'd':
                node.payload = OPERATORS['da']
        return self

    def maxify(self) -> 'EvalTree':
        """Modify rolls in this expression to maximum rolls.

        :return: This tree after it has been modified in-place.
        """
        # Max supersedes all
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da' or node.payload == 'dc':
                node.payload = OPERATORS['dm']
        return self

    def is_critical(self) -> bool:
        """Checks if this roll contains a d20 roll that is a natural 20."""
        for node in self.pre_order():
            if node.payload == 'd' and node.right.payload == [20] and node.value == 20:
                return True
        return False

    def is_fail(self) -> bool:
        """Checks if this roll contains a d20 roll that is a natural 1."""
        for node in self.pre_order():
            if node.payload == 'd' and node.right.payload == [1] and node.value == 20:
                return True
        return False
