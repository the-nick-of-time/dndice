import string
from typing import Optional, Tuple, List

from .operators import OPERATORS
from .exceptions import ParseError
from .tokenizer import Token


class State:
    _digits = set(string.digits)
    _recognized = (set(''.join(OPERATORS)) - set('p')
                   | set(string.digits)
                   | set('.')
                   | set('[]()')
                   | set(string.whitespace))

    def __init__(self, expr: str, i: int):
        self.expr = expr
        self.i = i

    def run(self) -> Tuple[Token, 'State']:
        agg = []
        while True:
            char = self.expr[self.i]
            if self.is_unrecognized(char):
                raise ParseError("Unrecognized character detected.", self.i, self.expr)
            if char.isspace():
                self.slurp_whitespace()
                return self.collect(agg), self.next_state(self.expr[self.i])
            forward = self.next_state(char)
            if forward:
                return self.collect(agg), forward
            else:
                agg.append(char)
                self.i += 1

    def is_unrecognized(self, char: str) -> bool:
        return char not in self._recognized

    def slurp_whitespace(self):
        while self.i < len(self.expr) and self.expr[self.i].isspace():
            self.i += 1

    def next_state(self, char: str) -> Optional['State']:
        raise NotImplementedError

    def collect(self, agg: List[str]) -> Optional[Token]:
        """Create a token from the current aggregator.

        Returns None if this state does not produce a token. This includes

        :param agg: The list of characters that compose this token.
        """
        raise NotImplementedError

    def _illegal_character(self, char: str):
        fmt = "{} is not allowed in this position."
        raise ParseError(fmt.format(char), expr=self.expr, offset=self.i)


class ExprStart(State):
    def next_state(self, char: str) -> Optional['State']:
        if char == '(':
            return OpenParen(self.expr, self.i)
        if char in UnaryPrefix.options:
            return UnaryPrefix(self.expr, self.i)
        if char in Integer.options:
            return Integer(self.expr, self.i)
        self._illegal_character(char)

    def collect(self, agg: List[str]) -> Optional[Token]:
        return None


class ExprEnd(State):
    def next_state(self, char: str) -> Optional['State']:
        if char in UnarySuffix.options:
            return UnarySuffix(self.expr, self.i)


class Integer(State):
    options = set(string.digits)

    def next_state(self, char: str) -> Optional['State']:
        if char in self.options:
            return None
        return ExprEnd(self.expr, self.i)

    def collect(self, agg: List[str]) -> Token:
        return int(''.join(agg))


class Binary(State):
    pass


class UnaryPrefix(State):
    options = set('+-')


class UnarySuffix(State):
    options = set('!')


class OpenParen(State):
    options = set('(')


class CloseParen(State):
    options = set(')')
