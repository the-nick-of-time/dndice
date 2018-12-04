import itertools
import operator
import string
import typing

import rolling as r


class Arity:
    LEFT = 0b01
    RIGHT = 0b10
    BOTH = 0b11
    NEITHER = 0b00


class Operator:
    def __init__(self, code: str, precedence: int, func: callable, arity: int = Arity.BOTH,
                 associativity: int = Arity.LEFT, cajole: int = Arity.BOTH):
        self.code = code
        self.precedence = precedence
        self.function = func
        self.arity = arity
        self.associativity = associativity
        self.cajole = cajole

    def __ge__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence >= other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __gt__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence > other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __le__(self, other):
        if isinstance(other, str):
            return True
        elif isinstance(other, Operator):
            return self.precedence <= other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __lt__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence < other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __eq__(self, other):
        if isinstance(other, Operator):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other
        return False

    def __repr__(self):
        return '{}:{} {}'.format(self.code, self.arity, self.precedence)

    def __str__(self):
        return self.code

    def __call__(self, left, right):
        if self.cajole & Arity.LEFT:
            try:
                left = sum(left)
            except TypeError:
                pass
        if self.cajole & Arity.RIGHT:
            try:
                right = sum(right)
            except TypeError:
                pass
        return self.function(*filter(lambda v: v is not None, [left, right]))


Value = typing.Union[typing.List[float], int, r.Roll]
Token = typing.Union[Value, r.Operator]


class EvalTreeNode:
    def __init__(self, payload, left=None, right=None):
        self.payload: typing.Union[r.Operator, int, typing.List[float]] = payload
        self.left: EvalTreeNode = left
        self.right: EvalTreeNode = right
        self.value: typing.Union[int, float, r.Roll] = None

    def evaluate(self) -> typing.Union[int, float, r.Roll]:
        if self.is_leaf():
            self.value = self.payload
            return self.value
        else:
            self.value = self.payload(self.left and self.left.evaluate(), self.right and self.right.evaluate())
            return self.value

    def is_leaf(self):
        return self.left is None and self.right is None


class EvalTree:
    operators = {
        'd': Operator('d', 7, r.roll_basic, cajole=Arity.LEFT),
        'da': Operator('da', 7, r.roll_average, cajole=Arity.LEFT),
        'dc': Operator('dc', 7, r.roll_critical, cajole=Arity.LEFT),
        'dm': Operator('dm', 7, r.roll_max, cajole=Arity.LEFT),
        'h': Operator('h', 6, r.take_high, cajole=Arity.RIGHT),
        'l': Operator('l', 6, r.take_low, cajole=Arity.RIGHT),
        'f': Operator('f', 6, r.floor_val, cajole=Arity.RIGHT),
        'c': Operator('c', 6, r.ceil_val, cajole=Arity.RIGHT),
        'r': Operator('r', 6, r.reroll_once_on, cajole=Arity.RIGHT),
        'R': Operator('R', 6, r.reroll_unconditional_on, cajole=Arity.RIGHT),
        'r<': Operator('r<', 6, r.reroll_once_lower, cajole=Arity.RIGHT),
        'R<': Operator('R<', 6, r.reroll_unconditional_lower, cajole=Arity.RIGHT),
        'rl': Operator('rl', 6, r.reroll_once_lower, cajole=Arity.RIGHT),
        'Rl': Operator('Rl', 6, r.reroll_unconditional_lower, cajole=Arity.RIGHT),
        'r>': Operator('r>', 6, r.reroll_once_higher, cajole=Arity.RIGHT),
        'R>': Operator('R>', 6, r.reroll_unconditional_higher, cajole=Arity.RIGHT),
        'rh': Operator('rh', 6, r.reroll_once_higher, cajole=Arity.RIGHT),
        'Rh': Operator('Rh', 6, r.reroll_unconditional_higher, cajole=Arity.RIGHT),
        '^': Operator('^', 5, lambda x, y: x ** y, associativity=Arity.RIGHT),
        'm': Operator('m', 4, lambda x: -x, arity=Arity.RIGHT, cajole=Arity.RIGHT),
        'p': Operator('p', 4, lambda x: x, arity=Arity.RIGHT, cajole=Arity.RIGHT),
        '!': Operator('!', 3, lambda x: itertools.accumulate(range(x), operator.mul), arity=Arity.LEFT,
                      cajole=Arity.LEFT),
        '*': Operator('*', 3, lambda x, y: x * y),
        '/': Operator('/', 3, lambda x, y: x / y),
        '%': Operator('%', 3, lambda x, y: x % y),
        '-': Operator('-', 2, lambda x, y: x - y),
        '+': Operator('+', 2, lambda x, y: x + y),
        '>': Operator('>', 1, lambda x, y: x > y),
        'gt': Operator('gt', 1, lambda x, y: x > y),
        '>=': Operator('>=', 1, lambda x, y: x >= y),
        'ge': Operator('ge', 1, lambda x, y: x >= y),
        '<': Operator('<', 1, lambda x, y: x < y),
        'lt': Operator('lt', 1, lambda x, y: x < y),
        '<=': Operator('<=', 1, lambda x, y: x <= y),
        'le': Operator('le', 1, lambda x, y: x <= y),
        '=': Operator('=', 1, lambda x, y: x == y),
        '|': Operator('|', 1, lambda x, y: x or y),
        '&': Operator('&', 1, lambda x, y: x and y),
    }

    def __init__(self, string):
        self.root: EvalTreeNode = None
        self.from_tokens(self.tokens(string))

    def evaluate(self):
        return self.root.evaluate()

    def from_tokens(self, tokens):
        expression: typing.List[EvalTreeNode] = []
        opers: typing.List[Operator] = []
        for t in tokens:
            if isinstance(t, (int, list)):
                expression.append(EvalTreeNode(t))
            elif t == '(':
                opers.append(t)
            elif t == ')':
                while opers[-1] != '(':
                    self.one_operation(opers, expression)
                opers.pop()
            else:
                while (len(opers)
                       and isinstance(opers[-1], Operator)
                       and (opers[-1] > t
                            or (opers[-1].precedence == t.precedence
                                and opers[-1].associativity == Arity.LEFT))):
                    self.one_operation(opers, expression)
                opers.append(t)
        while len(opers):
            self.one_operation(opers, expression)
        self.root = expression.pop()

    def one_operation(self, ops: typing.List[Operator], values: typing.List[EvalTreeNode]):
        current = ops.pop()
        node = EvalTreeNode(current)
        if current.arity & Arity.RIGHT:
            node.right = values.pop()
        if current.arity & Arity.LEFT:
            node.left = values.pop()
        values.append(node)

    def string_to_operator(self, s):
        return self.operators.get(s, s)

    def tokens(self, s):
        """Split a string into tokens for use with execute()
        :rtype: List[int|float|Operator]
        """
        # Every character that could be part of an operator
        possibilities = ''.join(self.operators)
        curr_num = []
        curr_op = []
        tokenlist = []
        i = 0
        while i < len(s):
            char = s[i]
            if char in string.digits:
                if curr_op:
                    op = self.string_to_operator(''.join(curr_op))
                    tokenlist.append(op)
                    curr_op = []
                curr_num.append(char)
            elif char in possibilities or char in '()':
                # Things that will end up on the operators stack
                if curr_num:
                    tokenlist.append(int(''.join(curr_num)))
                    curr_num = []
                if char == '+' and (i == 0 or s[i - 1] in possibilities + '('):
                    tokenlist.append(self.string_to_operator('p'))
                    curr_op = []
                elif char == '-' and (i == 0 or s[i - 1] in possibilities + '('):
                    tokenlist.append(self.string_to_operator('m'))
                    curr_op = []
                else:
                    if len(curr_op) == 0:
                        # This is the first time you see an operator since last
                        # time the list was cleared
                        curr_op.append(char)
                    elif ''.join(curr_op + [char]) in self.operators:
                        # This means that the current char is part of a
                        # multicharacter operation like <=
                        curr_op.append(char)
                    else:
                        # Two separate operators; push out the old one and start
                        # collecting the new one
                        op = self.string_to_operator(''.join(curr_op))
                        tokenlist.append(op)
                        curr_op = [char]
            elif char == '[':
                if curr_op:
                    tokenlist.append(self.string_to_operator(''.join(curr_op)))
                    curr_op = []
                # Start a list of floats
                sidelist = []
                while s[i] != ']':
                    sidelist.append(s[i])
                    i += 1
                sidelist.append(s[i])
                tokenlist.append(self.read_list(''.join(sidelist)))
            elif char == 'F':
                if curr_op:
                    tokenlist.append(self.string_to_operator(''.join(curr_op)))
                    curr_op = []
                # Fudge die
                tokenlist.append([-1, 0, 1])
            i += 1
        if curr_num:
            tokenlist.append(int(''.join(curr_num)))
        elif curr_op:
            tokenlist.append(self.string_to_operator(''.join(curr_op)))
        return tokenlist

    def read_list(self, s: str, mode=float):
        """Read a list defined in a string."""
        return map(mode, s.split(','))


if __name__ == '__main__':
    testcases = ["1d4+1",
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
    for expr in testcases:
        tree = EvalTree(expr)
        print(expr, ' = ', tree.evaluate())
