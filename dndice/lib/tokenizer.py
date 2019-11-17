import string
from typing import Optional, Tuple, List, Type, Set, Iterable, Sequence, Union

from .exceptions import ParseError
from .operators import OPERATORS, Side, Roll, Operator

Value = Union[Roll, int, Tuple[float, ...]]
Token = Union[Value, Operator, str]


def tokens(s: str) -> List[Token]:
    return list(tokens_lazy(s))


def tokens_lazy(s: str) -> Iterable[Token]:
    opens = s.count('(')
    closes = s.count(')')
    if opens > closes:
        raise ParseError("Unclosed parenthesis detected.", s.find('('), s)
    if closes > opens:
        raise ParseError("Unopened parenthesis detected.", s.rfind(')'), s)
    state = InputStart(s, 0)
    while not isinstance(state, InputEnd):
        token, state = state.run()
        if token is not None:
            yield token


class State:
    _recognized = (set(''.join(OPERATORS)) - set('p')
                   | set(string.digits)
                   | set('.F,')
                   | set('[]()')
                   | set(string.whitespace))
    followers = tuple()  # type: Tuple[Type[State], ...]
    options = set()  # type: Set[str]
    consumes = 1
    __slots__ = 'expr', 'i'

    def __init__(self, expr: str, i: int):
        self.expr = expr  # type: str
        self.i = i  # type: int

    def run(self) -> Tuple[Token, 'State']:
        """Moves along the string to produce the current token."""
        agg = []
        while self.i < len(self.expr):
            char = self.expr[self.i]
            if self.is_unrecognized(char):
                raise ParseError("Unrecognized character detected.", self.i, self.expr)
            if char.isspace():
                self.slurp_whitespace()
                if self.i >= len(self.expr):
                    return self._end_of_input(agg)
                forward = self.next_state(self.expr[self.i], agg)
                if forward is None:
                    # Meaning it's trying to continue the same token
                    raise ParseError("Token is already broken.", self.i, self.expr)
                return self.collect(agg), forward
            forward = self.next_state(char, agg)
            if forward:
                return self.collect(agg), forward
            else:
                agg.append(char)
                self.i += 1
        return self._end_of_input(agg)

    def is_unrecognized(self, char: str) -> bool:
        return char not in self._recognized

    def slurp_whitespace(self):
        while self.i < len(self.expr) and self.expr[self.i].isspace():
            self.i += 1

    def next_state(self, char: str, agg: Sequence[str]) -> Optional['State']:
        if len(agg) < self.consumes and char in self.options:
            # Don't move forward yet, just add to the aggregator
            return None
        for typ in self.followers:
            if char in typ.options:
                return typ(self.expr, self.i)
        self._illegal_character(char)

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        """Create a token from the current aggregator.

        Returns None if this state does not produce a token. This includes

        :param agg: The list of characters that compose this token.
        """
        return None

    def _illegal_character(self, char: str):
        if char == 'F':
            fmt = "F is the 'fudge dice' value, and must appear as the side specifier of a " \
                  "roll."
        elif char == ')':
            fmt = "Unexpectedly terminated expression."
        else:
            fmt = "{} is not allowed in this position."
        raise ParseError(fmt.format(char), expr=self.expr, offset=self.i)

    def _end_of_input(self, agg: Sequence[str]):
        if InputEnd in self.followers:
            return self.collect(agg), InputEnd(self.expr, self.i)
        else:
            raise ParseError("Unexpected end of expression.", self.i, self.expr)


class ExprStart(State):
    options = State._recognized
    consumes = 0

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (OpenParen, UnaryPrefix, Integer)


class ExprEnd(State):
    options = State._recognized
    consumes = 0

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (UnarySuffix, Binary, Die, CloseParen, InputEnd)


class InputStart(State):
    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart, InputEnd)


class InputEnd(State):
    pass


class Integer(State):
    options = set(string.digits)
    # No one will have a million-digit integer right?
    consumes = 1e6

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def collect(self, agg: List[str]) -> Token:
        return int(''.join(agg))


class Operator(State):
    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        s = ''.join(agg)
        if s in OPERATORS:
            return OPERATORS[s]
        else:
            raise ParseError("Invalid operator.", self.i - len(s), self.expr)


class Binary(Operator):
    # All the operator codes
    codes = {code for code, op in OPERATORS.items() if (op.arity == Side.BOTH
                                                        and not code.startswith('d'))}
    # The characters that can start an operator
    options = {code[0] for code, op in OPERATORS.items() if (op.arity == Side.BOTH
                                                             and not code.startswith('d'))}

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        current = ''.join(agg)
        potential = current + char
        if potential in self.codes or len(agg) == 0:
            # Continue aggregation
            return None
        for typ in self.followers:
            if char in typ.options:
                return typ(self.expr, self.i)
        self._illegal_character(char)


class Die(Binary):
    options = 'd'
    codes = {code for code in OPERATORS if code.startswith('d')}

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (Integer, ListToken, FudgeDie, OpenParen)


class UnaryPrefix(Operator):
    options = set('+-')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        token = agg[0]
        if token == '+':
            return OPERATORS['p']
        if token == '-':
            return OPERATORS['m']


class UnarySuffix(Operator):
    options = '!'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)


class OpenParen(State):
    options = '('

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        return ExprStart(self.expr, self.i + 1)

    def collect(self, agg: List[str]) -> Optional[Token]:
        return '('


class CloseParen(State):
    options = ')'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        return ExprEnd(self.expr, self.i + 1)

    def collect(self, agg: List[str]) -> Optional[Token]:
        return ')'


class ListToken(State):
    # Overrides run so doesn't need to override collect or next_state
    options = '['

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def run(self) -> Tuple[Token, 'State']:
        sides = []
        state = ListStart(self.expr, self.i)
        while not isinstance(state, ListEnd):
            value, state = state.run()
            if value is not None:
                sides.append(value)
        return tuple(sides), ExprEnd(state.expr, state.i + 1)


class ListStart(State):
    options = '['

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ListValue,)


class ListValue(State):
    options = set(string.digits) | set('.')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ListSeparator, ListEnd)

    def collect(self, agg: Sequence[str]) -> Optional[Union[Token, float]]:
        return float(''.join(agg))


class ListSeparator(State):
    options = ','

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ListValue,)


class ListEnd(State):
    options = ']'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)


class FudgeDie(State):
    options = 'F'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        return -1, 0, 1

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        return ExprEnd(self.expr, self.i + 1)
