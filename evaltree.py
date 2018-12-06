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
        print(expr, ' = ', tree.evaluate())
