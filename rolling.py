import string
import typing

from operators import operators, Operator, Arity, Roll


class EvalTreeNode:
    def __init__(self, payload, left=None, right=None):
        self.payload: typing.Union[Operator, int, typing.List[float]] = payload
        self.left: EvalTreeNode = left
        self.right: EvalTreeNode = right
        self.value: typing.Union[int, float, Roll] = None

    def evaluate(self) -> typing.Union[int, float, Roll]:
        if self.is_leaf():
            self.value = self.payload
            return self.value
        else:
            self.value = self.payload(self.left and self.left.evaluate(), self.right and self.right.evaluate())
            return self.value

    def is_leaf(self):
        return self.left is None and self.right is None


def string_to_operator(s):
    return operators.get(s, s)


def read_list(s: str, mode=float):
    """Read a list defined in a string."""
    return map(mode, s.split(','))


def tokens(s):
    """Split a string into tokens for use with execute()
    :rtype: List[int|float|Operator]
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
                op = string_to_operator(''.join(curr_op))
                tokenlist.append(op)
                curr_op = []
            curr_num.append(char)
        elif char in possibilities or char in '()':
            # Things that will end up on the operators stack
            if curr_num:
                tokenlist.append(int(''.join(curr_num)))
                curr_num = []
            if char == '+' and (i == 0 or s[i - 1] in possibilities + '('):
                tokenlist.append(string_to_operator('p'))
                curr_op = []
            elif char == '-' and (i == 0 or s[i - 1] in possibilities + '('):
                tokenlist.append(string_to_operator('m'))
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
                    op = string_to_operator(''.join(curr_op))
                    tokenlist.append(op)
                    curr_op = [char]
        elif char == '[':
            if curr_op:
                tokenlist.append(string_to_operator(''.join(curr_op)))
                curr_op = []
            # Start a list of floats
            sidelist = []
            while s[i] != ']':
                sidelist.append(s[i])
                i += 1
            sidelist.append(s[i])
            tokenlist.append(read_list(''.join(sidelist)))
        elif char == 'F':
            if curr_op:
                tokenlist.append(string_to_operator(''.join(curr_op)))
                curr_op = []
            # Fudge die
            tokenlist.append([-1, 0, 1])
        i += 1
    if curr_num:
        tokenlist.append(int(''.join(curr_num)))
    elif curr_op:
        tokenlist.append(string_to_operator(''.join(curr_op)))
    return tokenlist


class EvalTree:
    def __init__(self, string):
        self.root: EvalTreeNode = None
        self.from_tokens(tokens(string))

    def evaluate(self):
        try:
            return sum(self.root.evaluate())
        except TypeError:
            return self.root.evaluate()

    def from_tokens(self, tokens):
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
                                and operators[-1].associativity == Arity.LEFT))):
                    self.one_operation(operators, expression)
                operators.append(t)
        while len(operators):
            self.one_operation(operators, expression)
        self.root = expression.pop()

    @staticmethod
    def one_operation(ops: typing.List[Operator], values: typing.List[EvalTreeNode]):
        current = ops.pop()
        node = EvalTreeNode(current)
        if current.arity & Arity.RIGHT:
            node.right = values.pop()
        if current.arity & Arity.LEFT:
            node.left = values.pop()
        values.append(node)

    def verbose_result(self):
        self.evaluate()
        base = self.__verbose_result_recursive(self.root, 6)
        return base + ' = ' + str(self.root.value)

    def __verbose_result_recursive(self, current: EvalTreeNode, threshold: int) -> str:
        if current is None:
            return ''
        if current.is_leaf() or current.payload.precedence >= threshold:
            return str(current.value)
        return (self.__verbose_result_recursive(current.left, threshold)
                + str(current.payload)
                + self.__verbose_result_recursive(current.right, threshold))

    def pre_order(self):
        return self.__pre_order_recursive(self.root)

    def __pre_order_recursive(self, current: EvalTreeNode) -> typing.Generator[EvalTreeNode, None, None]:
        yield current
        if current.left:
            yield self.__pre_order_recursive(current.left)
        if current.right:
            yield self.__pre_order_recursive(current.right)

    def critify(self):
        # Note: crit is superseded by maximum
        # Though why you're using roll_max anyway is a mystery
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da':
                node.payload = operators['dc']
        return self

    def averageify(self):
        # Note: average is superseded by crit or max
        for node in self.pre_order():
            if node.payload == 'd':
                node.payload = operators['da']
        return self

    def maxify(self):
        # Max supersedes all
        for node in self.pre_order():
            if node.payload == 'd' or node.payload == 'da' or node.payload == 'dc':
                node.payload = operators['dm']
        return self


def roll(s: str, modifiers=0, option='execute'):
    """Roll dice and do arithmetic."""
    if isinstance(s, (float, int)):
        # If you're naughty and pass a number in...
        # it really doesn't matter.
        return s + modifiers
    elif s == '':
        return 0 + modifiers
    elif option == 'execute':
        return EvalTree(s).evaluate() + modifiers
    elif option == 'critical':
        return EvalTree(s).critify().evaluate() + modifiers
    elif option == 'average':
        return EvalTree(s).averageify().evaluate() + modifiers
    elif option == 'multipass':
        tree = EvalTree(s)
        return tree.verbose_result()
    elif option == 'multipass_critical':
        tree = EvalTree(s)
        tree.critify()
        return tree.verbose_result()
    elif option == 'tokenize':
        return tokens(s)
    elif option == 'from_tokens':
        tree = EvalTree('')
        tree.from_tokens(s)
        return tree.evaluate()
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
        print()
