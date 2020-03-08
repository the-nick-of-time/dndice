"""Classes to hold and work with evaluation trees.

``EvalTree`` is naturally the core class here. It provides all the
functionality for looking at the tree as a unit, while ``EvalTreeNode``
is the basic component.
"""
import copy
import typing

from .exceptions import InputTypeError, EvaluationError, ParseError
from .helpers import wrap_exceptions_with
from .operators import OPERATORS, Roll, Operator, Side
from .tokenizer import Token, tokens

Result = typing.Union[Roll, int, float]
Final = typing.Union[int, float]
Predicate = typing.Callable[['EvalTreeNode'], bool]
Root = typing.Optional[typing.Union[str, typing.List[Token], 'EvalTree', None]]


class EvalTreeNode:
    """A node in the EvalTree, which can hold a value or operator."""
    __slots__ = 'payload', 'left', 'right', 'value'

    def __init__(self, payload: typing.Optional[Token], left: 'EvalTreeNode' = None,
                 right: 'EvalTreeNode' = None):
        """Initialize a new node in the expression tree.

        Leaf nodes (those with no left or right children) are guaranteed
        to hold concrete values while non-leaf nodes are guaranteed to
        hold operators.

        :param payload: The operator or value that is expressed by this
            node.
        :param left: The left child of this node, which holds the
            operand or expression to the left of this operator.
        :param right: The right child of this node, which holds the
            operand or expression to the right of this operator.
        """
        self.payload = payload  # type: Token
        self.left = left  # type: EvalTreeNode
        self.right = right  # type: EvalTreeNode
        self.value = None  # type: typing.Optional[Result]

    def evaluate(self) -> Result:
        """Recursively evaluate this subtree and return its computed value.

        As a side effect, it also annotates this node with the value. At
        the EvalTree level, this can be used to compose a more detailed
        report of the dice rolls.

        :return: The value computed.
        """
        if self.is_leaf():
            # Leaves are guaranteed to be concrete values
            self.value = self.payload
            return self.value
        else:
            self.value = self.payload(self.left and self.left.evaluate(),
                                      self.right and self.right.evaluate())
            return self.value

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class EvalTree:
    """An expression tree that can be used to evaluate roll expressions.

    An `expression tree <https://en.wikipedia.org/wiki/Binary_expression_tree>`_
    is, in short, a binary tree that holds an arithmetic expression. It
    is important to note that the binary tree not necessarily be
    complete; unary operators like factorial do create a tree where some
    leaf slots are unfilled, as they only take one operand instead of
    the two that most operators take.

    It is guaranteed that all leaf nodes hold a value (usually an
    integer) while all non-leaf nodes hold an operator.
    """
    __slots__ = 'root',

    def __init__(self, source: Root):
        """Initialize a tree of EvalTreeNodes that represent a given expression.

        :param source: The expression, generally as a string or already
            tokenized list or compiled tree.
        """
        self.root = None  # type: typing.Optional[EvalTreeNode]
        if isinstance(source, str):
            self.__from_tokens(tokens(source))
        elif isinstance(source, EvalTree):
            self.root = source.root
        elif isinstance(source, list):
            self.__from_tokens(source)
        elif isinstance(source, (int, float)):
            self.root = EvalTreeNode(source)
        elif source is None:
            # Explicitly do nothing; leave us with an empty tree
            pass
        else:
            fmt = "You can't construct an EvalTree from type {}"
            raise InputTypeError(fmt.format(type(source)))

    def __add__(self, other) -> 'EvalTree':
        """Join two trees together with the addition operator.

        The end result is as if you had wrapped both initial expressions
        in parentheses and added them together, like ``(expression 1) +
        (expression 2)``.

        :param other: The EvalTree to join with this one.
        :raises NotImplementedError: If anything but an EvalTree is passed in.
        """
        if isinstance(other, EvalTree):
            return self.__concat(OPERATORS['+'], other)
        raise InputTypeError('Cannot add a {} to an EvalTree.'.format(type(other)))

    def __iadd__(self, other) -> 'EvalTree':
        """Join two trees together with the addition operator in-place.

        The end result is as if you had wrapped both initial expressions
        in parentheses and added them together, like ``(expression 1) +
        (expression 2)``.

        As this mutates the objects in-place instead of performing a
        deep clone, it is much faster than the normal addition.
        This comes with a **very important warning**, though: neither
        of the inputs ends up independent of the output. If you use this
        operator, don't use either argument to it again. Otherwise the
        evaluation of any of the objects will pollute the others.

        :param other: The EvalTree to join with this one.
        :raises NotImplementedError: If anything but an EvalTree is passed in.
        """
        if isinstance(other, EvalTree):
            return self.__in_place_concat(OPERATORS['+'], other)
        raise InputTypeError('Cannot add a {} to an EvalTree.'.format(type(other)))

    def __sub__(self, other):
        """Join two trees together with the subtraction operator.

        The end result is as if you had wrapped both initial expressions
        in parentheses and subtracted them, like ``(expression 1) -
        (expression 2)``.

        :param other: The EvalTree to join with this one.
        :raises NotImplementedError: If anything but an EvalTree is passed in.
        """
        if isinstance(other, EvalTree):
            return self.__concat(OPERATORS['-'], other)
        raise InputTypeError('Cannot subtract a {} from an EvalTree.'.format(type(other)))

    def __isub__(self, other):
        """Join two trees together with the subtraction operator in-place.

        The end result is as if you had wrapped both initial expressions
        in parentheses and subtracted them, like ``(expression 1) -
        (expression 2)``.

        As this mutates the objects in-place instead of performing a
        deep clone, it is much faster than the normal subtraction.
        This comes with a **very important warning**, though: neither
        of the inputs ends up independent of the output. If you use this
        operator, don't use either argument to it again. Otherwise the
        evaluation of any of the objects will pollute the others.

        :param other: The EvalTree to join with this one.
        :raises NotImplementedError: If anything but an EvalTree is passed in.
        """
        if isinstance(other, EvalTree):
            return self.__in_place_concat(OPERATORS['-'], other)
        raise InputTypeError('Cannot subtract a {} from an EvalTree.'.format(type(other)))

    def __concat(self, operation: Operator, other: 'EvalTree') -> 'EvalTree':
        new = self.copy()
        new.root = EvalTreeNode(operation, new.root, other.copy().root)
        return new

    def __in_place_concat(self, operation: Operator, other: 'EvalTree') -> 'EvalTree':
        self.root = EvalTreeNode(operation, self.root, other.root)
        return self

    @wrap_exceptions_with(EvaluationError, 'Failed to evaluate expression.')
    def evaluate(self) -> Final:
        r"""Recursively evaluate the tree.

        Along the way, the ``value`` of each node is set to the value
        of the expression at this stage, so it can be inspected later.
        This is used to great effect by the "verbose mode" of the main
        roll function.

        What is meant by "value of the expression at this stage" can be
        shown through a diagram: ::

                  -        < 0
                /  \
              *     +      < 1
            /  \  /  \
            4  5  1  2     < 2

        This is the tree that would result from the expression
        "4 * 5 - (1 + 2)". If we were to start evaluating this tree, we
        would first recursively run down all three levels. Once reaching
        the leaves at level 2, their value is obvious: they are concrete
        already. Copy their ``payload`` into their ``value``. One level
        up, and we reach operators. The operator nodes receive values
        from each of their children, perform the operation they hold,
        and fill their own ``value`` slot with the result. For instance,
        the '*' would perform 4 * 5 and store 20. This continues until
        the root is reached, and the final value is returned.

        :return: The single final value from the tree.
        """
        if self.root is None:
            # An empty tree evaluates to nothing
            return 0
        final = self.root.evaluate()
        try:
            return sum(final)
        except TypeError:
            return final

    @wrap_exceptions_with(ParseError, 'Failed to construct an expression from the token list.')
    def __from_tokens(self, tokens: typing.List[Token]) -> None:
        """Construct the expression tree formed from the infix token list.

        This uses a `shunting-yard algorithm
        <https://en.wikipedia.org/wiki/Shunting-yard_algorithm>`_ to parse the infix token
        list into an expression tree. In relation to that algorithm, the "output" stack is
        populated with with subtrees that are progressively joined together using operators
        to create the final full tree.

        :param tokens: The list of tokens parsed from the infix expression.
        """
        expression = []  # type: typing.List[EvalTreeNode]
        operators = []  # type: typing.List[Operator]
        for t in tokens:
            if isinstance(t, (int, tuple)):
                expression.append(EvalTreeNode(t))
            elif t == '(':
                operators.append(t)
            elif t == ')':
                while operators[-1] != '(':
                    self.__one_operation(operators, expression)
                operators.pop()
            else:
                while (len(operators)
                       and isinstance(operators[-1], Operator)
                       and (operators[-1] > t
                            or (operators[-1].precedence == t.precedence
                                and operators[-1].associativity == Side.LEFT))):
                    self.__one_operation(operators, expression)
                operators.append(t)
        while len(operators):
            self.__one_operation(operators, expression)
        self.root = expression.pop() if len(expression) else EvalTreeNode(0)

    @staticmethod
    def __one_operation(ops: typing.List[Operator], values: typing.List[EvalTreeNode]):
        """Pop the top operator and give it the top one or two subtrees from the values stack.
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

    def in_order(self, abort=None) -> typing.Iterable[EvalTreeNode]:
        """Perform an in-order/infix traversal of the tree.

        This includes a minimal set of parentheses such that the
        original tree can be constructed from the results of this
        iterator.
        """
        if abort is not None:
            return self.__in_order_recursive(self.root, None, abort)
        else:
            return self.__in_order_recursive(self.root, None, lambda node: False)

    def __in_order_recursive(self, current: EvalTreeNode, parent: typing.Optional[EvalTreeNode],
                             abort: Predicate) \
            -> typing.Iterable[EvalTreeNode]:
        """Recurse through the tree."""
        if current.is_leaf() or abort(current):
            yield current
            return
        if parent and parent.payload > current.payload:
            yield EvalTreeNode('(')
        if current.left:
            yield from self.__in_order_recursive(current.left, current, abort)
        yield current
        if current.right:
            yield from self.__in_order_recursive(current.right, current, abort)
        if parent and parent.payload > current.payload:
            yield EvalTreeNode(')')

    def verbose_result(self) -> str:
        """Forms an infix string of the result, looking like the original with rolls evaluated.

        The expression is constructed with as few parentheses as possible. This means that if
        there were redundant parentheses in the input, they will not show up here.

        :return: A string representation of the result, showing the
            results from rolls.
        """

        def to_string(node: EvalTreeNode) -> str:
            if isinstance(node.payload, str):
                return node.payload
            if node.is_leaf() or node.payload.precedence >= 6:
                return str(node.value)
            return str(node.payload)
        if self.root is None:
            return ''
        if self.root.value is None:
            self.evaluate()
        tokens = [to_string(node) for node in
                  self.in_order(lambda node: node.payload.precedence >= 6)]
        base = ''.join(tokens)
        try:
            final = sum(self.root.value)
        except TypeError:
            final = self.root.value
        return base + ' = ' + str(final)

    def pre_order(self, abort=None) -> typing.Iterable[EvalTreeNode]:
        """Perform a pre-order/breadth-first traversal of the tree."""
        if abort is not None:
            return self.__pre_order_recursive(self.root, abort)
        else:
            return self.__pre_order_recursive(self.root, lambda node: False)

    def __pre_order_recursive(self, current: EvalTreeNode, abort: Predicate) -> \
            typing.Iterable[EvalTreeNode]:
        """Recurse through the tree."""
        yield current
        if not abort(current):
            if current.left:
                yield from self.__pre_order_recursive(current.left, abort)
            if current.right:
                yield from self.__pre_order_recursive(current.right, abort)

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
        for node in self.pre_order(lambda node: (isinstance(node.value, Roll)
                                                 and node.value.die == 20)):
            if isinstance(node.value, Roll) and node.value.die == 20 and 20 in node.value:
                return True
        return False

    def is_fail(self) -> bool:
        """Checks if this roll contains a d20 roll that is a natural 1."""
        for node in self.pre_order(lambda node: (isinstance(node.value, Roll)
                                                 and node.value.die == 20)):
            if isinstance(node.value, Roll) and node.value.die == 20 and 1 in node.value:
                return True
        return False

    def copy(self) -> 'EvalTree':
        return copy.deepcopy(self)
