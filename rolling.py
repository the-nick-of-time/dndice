import string
import typing

from operators import operators, Operator, Side, Roll

Value = typing.Union[Roll, int, typing.List[float]]
Result = typing.Union[Roll, int, float]
Final = typing.Union[int, float]
Token = typing.Union[Value, Operator]


class EvalTreeNode:
    def __init__(self, payload: Token, left=None, right=None):
        self.payload: Token = payload
        self.left: EvalTreeNode = left
        self.right: EvalTreeNode = right
        self.value: Result = None

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


def _string_to_operator(s: str) -> typing.Union[str, Operator]:
    return operators.get(s, s)


def _read_list(s: str, mode=float) -> typing.Iterable[float]:
    """Read a list defined in a string."""
    return list(map(mode, map(str.strip, s.split(','))))


def tokens(s: str) -> typing.List[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree and evaluated

    :param s: The expression to be parsed
    :return: A list of tokens
    """
    # Every character that could be part of an operator
    possibilities = ''.join(operators)
    curr_num = []
    curr_op = []
    tokenlist = []
    i = 0
    while i < len(s):
        char = s[i]
        if char in string.digits:
            if curr_op:
                op = _string_to_operator(''.join(curr_op))
                tokenlist.append(op)
                curr_op = []
            curr_num.append(char)
        elif char in possibilities or char in '()':
            # Things that will end up on the operators stack
            if curr_num:
                tokenlist.append(int(''.join(curr_num)))
                curr_num = []
            if char == '+' and (i == 0 or s[i - 1] in possibilities + '('):
                tokenlist.append(_string_to_operator('p'))
                curr_op = []
            elif char == '-' and (i == 0 or s[i - 1] in possibilities + '('):
                tokenlist.append(_string_to_operator('m'))
                curr_op = []
            else:
                if len(curr_op) == 0:
                    # This is the first time you see an operator since last
                    # time the list was cleared
                    curr_op.append(char)
                elif ''.join(curr_op + [char]) in operators:
                    # This means that the current char is part of a
                    # multicharacter operation like <=
                    curr_op.append(char)
                else:
                    # Two separate operators; push out the old one and start
                    # collecting the new one
                    op = _string_to_operator(''.join(curr_op))
                    tokenlist.append(op)
                    curr_op = [char]
        elif char == '[':
            if curr_op:
                tokenlist.append(_string_to_operator(''.join(curr_op)))
                curr_op = []
            # Start a list of floats
            sidelist = []
            i += 1
            while s[i] != ']':
                sidelist.append(s[i])
                i += 1
            tokenlist.append(_read_list(''.join(sidelist)))
        elif char == 'F':
            if curr_op:
                tokenlist.append(_string_to_operator(''.join(curr_op)))
                curr_op = []
            # Fudge die
            tokenlist.append([-1, 0, 1])
        i += 1
    if curr_num:
        tokenlist.append(int(''.join(curr_num)))
    elif curr_op:
        tokenlist.append(_string_to_operator(''.join(curr_op)))
    return tokenlist


class EvalTree:
    def __init__(self, source: typing.Union[str, typing.List[Token], 'EvalTree']):
        self.root: EvalTreeNode = None
        if isinstance(source, str):
            self.from_tokens(tokens(source))
        elif isinstance(source, EvalTree):
            self.root = source.root
        elif isinstance(source, list):
            self.from_tokens(source)

    def evaluate(self) -> Final:
        """Recursively evaluate the tree

        :return: The single final value from the tree
        """
        final = self.root.evaluate()
        try:
            return sum(final)
        except TypeError:
            return final

    def from_tokens(self, tokens: typing.List[Token]) -> None:
        """Construct and take possession of the expression tree formed from the infix token list

        :param tokens: The list of tokens parsed from the infix expression
        """
        expression: typing.List[EvalTreeNode] = []
        operators: typing.List[Operator] = []
        for t in tokens:
            if isinstance(t, (int, list)):
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
                node.payload = operators['dc']
        return self

    def averageify(self):
        """Modify rolls in this expression to average rolls.

        :rtype: EvalTree
        """
        # Note: average is superseded by crit or max
        for node in self.pre_order():
            if node.payload == 'd':
                node.payload = operators['da']
        return self

    def maxify(self):
        """Modify rolls in this expression to maximum rolls.

        :rtype: EvalTree
        """
        # Max supersedes all
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da' or node.payload == 'dc':
                node.payload = operators['dm']
        return self


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
            tree = EvalTree("{}+{}".format(expr, modifiers))
        elif isinstance(expr, EvalTree):
            tree = expr
        elif isinstance(expr, list):
            tree = EvalTree(expr + [operators['+'], modifiers])
        else:
            raise TypeError("Expression must be a string, list of tokens, or already compiled evaluation tree")
        return tree.verbose_result()
    elif option == 'multipass_critical':
        tree = EvalTree("{}+{}".format(expr, modifiers))
        tree.critify()
        return tree.verbose_result()
    elif option == 'compile':
        if isinstance(expr, EvalTree):
            return expr
        if isinstance(expr, str):
            tree = EvalTree("{}+{}".format(expr, modifiers))
        elif isinstance(expr, list):
            tree = EvalTree(expr + [operators['+'], modifiers])
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
            tree = EvalTree(expr + [operators['+'], modifiers])
            return tree.evaluate()
        else:
            raise TypeError("You need to actually pass tokens in")
    elif option == 'zero':
        return 0


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
