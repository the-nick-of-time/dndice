import string
from typing import Optional, Tuple, List, Type, Set

from .exceptions import ParseError
from .operators import OPERATORS, Side
from .tokenizer import Token


class State:
    _recognized = (set(''.join(OPERATORS)) - set('p')
                   | set(string.digits)
                   | set('.')
                   | set('[]()')
                   | set(string.whitespace))
    followers = tuple()  # type: Tuple[Type[State], ...]
    options = set()  # type: Set[str]
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
                return self.collect(agg), self.next_state(self.expr[self.i])
            forward = self.next_state(char)
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

    def next_state(self, char: str) -> Optional['State']:
        if char in self.options:
            # Don't move forward yet
            return None
        for typ in self.followers:
            if char in typ.options:
                return typ(self.expr, self.i)
        self._illegal_character(char)

    def collect(self, agg: List[str]) -> Optional[Token]:
        """Create a token from the current aggregator.

        Returns None if this state does not produce a token. This includes

        :param agg: The list of characters that compose this token.
        """
        return None

    def _illegal_character(self, char: str):
        fmt = "{} is not allowed in this position."
        raise ParseError(fmt.format(char), expr=self.expr, offset=self.i)

    def _end_of_input(self, agg: List[str]):
        if InputEnd in self.followers:
            return self.collect(agg), InputEnd(self.expr, self.i)
        else:
            raise ParseError("Unexpected end of expression.", self.i, self.expr)


class ExprStart(State):
    options = State._recognized

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (OpenParen, UnaryPrefix, Integer)


class ExprEnd(State):
    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (UnarySuffix, Binary, InputEnd)


class InputStart(State):
    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart, InputEnd)


class InputEnd(State):
    pass


class Integer(State):
    options = set(string.digits)

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd,)

    def collect(self, agg: List[str]) -> Token:
        return int(''.join(agg))


class Operator(State):
    def collect(self, agg: List[str]) -> Optional[Token]:
        s = ''.join(agg)
        if s in OPERATORS:
            return OPERATORS[s]
        else:
            raise ParseError("Invalid operator.", self.i - len(s), self.expr)


class Binary(Operator):
    options = {code[0] for code, op in OPERATORS.items() if op.arity == Side.BOTH}

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def next_state(self, char: str) -> Optional['State']:
        # Has to deal with multi-character operators
        pass

    def collect(self, agg: List[str]) -> Optional[Token]:
        pass


class UnaryPrefix(Operator):
    options = set('+-')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)


class UnarySuffix(Operator):
    options = set('!')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd,)


class OpenParen(State):
    options = set('(')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def next_state(self, char: str) -> Optional['State']:
        return ExprStart(self.expr, self.i)

    def collect(self, agg: List[str]) -> Optional[Token]:
        return '('


class CloseParen(State):
    options = set(')')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd,)

    def next_state(self, char: str) -> Optional['State']:
        return ExprEnd(self.expr, self.i)

    def collect(self, agg: List[str]) -> Optional[Token]:
        return ')'
