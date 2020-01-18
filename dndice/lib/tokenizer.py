"""Split a string into a list of tokens, meaning operators or values.

Two functions may be useful to the outside: ``tokens`` and
``tokens_lazy``. ``tokens`` returns a list of the tokens, while
``tokens_lazy`` is a generator
"""
import string
from typing import Optional, Tuple, List, Type, Set, Iterable, Sequence, Union

from .exceptions import ParseError
from .operators import OPERATORS, Side, Roll, Operator

Value = Union[Roll, int, Tuple[float, ...]]
Token = Union[Value, Operator, str]


def tokens(s: str) -> List[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree.

    For specifics, see :py:func:`tokens_lazy`.

    :param s: The expression to be parsed
    :return: A list of tokens
    """
    return list(tokens_lazy(s))


def tokens_lazy(s: str) -> Iterable[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree.

    This parser is based around a state machine. Starting with
    InputStart, it traverses the string character by character taking on
    a sequence of states. At each of these states, it asks that state to
    produce a token if applicable and produce the state that follows it.
    The token is yielded and the movement of the machine continues.

    :param s: The expression to be parsed
    :return: An iterator of tokens
    """
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
    """The base class for all of the states of the tokenizer.

    A number of these states will consume one or more characters to
    produce a token, but some instead serve as markers. For instance,
    the ExprStart state marks the start of an expression, which can be
    followed by a unary prefix operator, an open parenthesis (which will
    itself start a new expression), or an integer value.

    This base class also provides several constants and simple methods
    that factor into the algorithms of most or all varieties of states.

    :cvar _recognized: The set of all characters that could be part of
                       an expression.
    :cvar starters: The set of all characters that can start this token.
    :cvar consumes: The maximum number of characters this token can
                    consume.
    :ivar followers: The set of states that are allowed to follow this
                     one. This is a sequence of the class objects. It
                     must be ordered, and if applicable, 'ExprStart'/
                     'ExprEnd' must come last. Otherwise, anything could
                     cause a transfer to those marker states. This
                     should semantically be a class variable; it is not
                     simply because then it would be evaluated at
                     definition time and it needs to reference other
                     class objects which don't exist at that time.
    """
    _recognized = (set(''.join(OPERATORS)) - set('p')
                   | set(string.digits)
                   | set('.F,')
                   | set('[]()')
                   | set(string.whitespace))
    starters = set()  # type: Set[str]
    consumes = 1
    __slots__ = 'expr', 'i', 'followers'

    def __init__(self, expr: str, i: int):
        """Save the information required to look at the expression.

        :param expr: The string that is being tokenized.
        :param i: The index in the string at which this token starts.
        """
        self.expr = expr  # type: str
        self.i = i  # type: int
        self.followers = tuple()  # type: Tuple[Type[State], ...]

    def run(self) -> Tuple[Optional[Token], 'State']:
        """Moves along the string to produce the current token.

        This base implementation moves along the string, performing the
        following steps:

        #.  If the current character is not one that is recognized,
            raise a ParseError.
        #.  If the current token is whitespace, run along the string
            until the end of the whitespace, then transfer to the next
            state. If the ``next_state`` function indicates that the
            character after the whitespace should be part of the
            existing one, raise a ParseError.
        #.  Check if the machine should transfer to the next state using
            the ``next_state`` function. If yes, return the token that
            has been collected along with that next state.

        It stops when it encounters the first character of the next
        token.

        :raise ParseError: If a character is not recognized, or a token
                           is not allowed in a certain position, or the
                           expression ends unexpectedly.
        :return: The pair (the token that this produces if applicable,
                 the next state)
        """
        agg = []
        while self.i < len(self.expr):
            char = self.expr[self.i]
            if self._is_unrecognized(char):
                raise ParseError("Unrecognized character detected.", self.i, self.expr)
            if char.isspace():
                self._slurp_whitespace()
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

    def next_state(self, char: str, agg: Sequence[str]) -> Optional['State']:
        """Decides what state to transfer to.

        :param char: The current character.
        :param agg: The sequence of characters that has been identified
                    as the current token.
        :return: An instance of the State that will pick up starting
                 with the current character.
        """
        if len(agg) < self.consumes and char in self.starters:
            # Don't move forward yet, just add to the aggregator
            return None
        for typ in self.followers:
            if char in typ.starters:
                return typ(self.expr, self.i)
        self._illegal_character(char)

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        """Create a token from the current aggregator.

        Returns None if this state does not produce a token. This is for
        the "marker" states that correspond to abstract notions of
        positions in the expression rather than actual concrete tokens.

        This default implementation simply returns None, which is common
        to all of the marker states while every real token will have its
        own implementation.

        :param agg: The list of characters that compose this token.
        """
        return None

    def _is_unrecognized(self, char: str) -> bool:
        return char not in self._recognized

    def _slurp_whitespace(self):
        while self.i < len(self.expr) and self.expr[self.i].isspace():
            self.i += 1

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


class Integer(State):
    """A whole number.

    Is followed by the end of an expression.
    """
    starters = set(string.digits)
    # No one will have a million-digit integer right?
    consumes = 1e6

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def collect(self, agg: List[str]) -> Token:
        """Collects the sequence of characters into an int."""
        return int(''.join(agg))


class Operator(State):
    """An incomplete base class for the operators."""

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        """Interprets the sequence of characters as an operator.

        :raise ParseError: If the characters don't actually compose a
                           real operator.
        """
        s = ''.join(agg)
        if s in OPERATORS:
            return OPERATORS[s]
        else:
            # Should be impossible due to next_state filtering down to
            # valid operators only
            raise ParseError("Invalid operator.", self.i - len(s), self.expr)


class Binary(Operator):
    """A binary operator.

    Is followed by the start of an expression.
    """
    # All the operator codes
    codes = {code for code, op in OPERATORS.items() if (op.arity == Side.BOTH
                                                        and not code.startswith('d'))}
    # The characters that can start an operator
    starters = {code[0] for code, op in OPERATORS.items() if (op.arity == Side.BOTH
                                                              and not code.startswith('d'))}

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        """Reads a possibly multi-character operator.

        Overrides because unlike integers, they have finite length and
        the order is important, and unlike other tokens like
        parentheses, they may have length greater than one. This
        requires checking at every step whether the appending of the
        current character to the current sequence produces a valid
        operator.
        """
        current = ''.join(agg)
        potential = current + char
        if potential in self.codes or len(agg) == 0:
            # Continue aggregation
            return None
        for typ in self.followers:
            if char in typ.starters:
                return typ(self.expr, self.i)
        # should be impossible because characters that don't go into the
        # current operator get captured by `ExprStart` in the `for`
        # captures anything that could be a valid portion of a token,
        # while `State._is_unrecognized` captures characters that aren't
        # allowed
        self._illegal_character(char)


class UnaryPrefix(Operator):
    """A unary prefix operator.

    The only ones that exist now are the positive and negative signs.

    Is followed by the start of an expression.
    """
    starters = set('+-')

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        """Returns the correct unary operator.

        These are special cases to avoid ambiguity in the definitions.
        """
        token = agg[0]
        if token == '+':
            return OPERATORS['p']
        if token == '-':
            return OPERATORS['m']


class UnarySuffix(Operator):
    """A unary suffix operator.

    The only one that exists now is the factorial, !.

    Is followed by the end of an expression.
    """
    starters = '!'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)


class Die(Binary):
    """One of the die operators, which are a subset of the binary.

    Can be followed by:

    - A number
    - A list
    - The "fudge die"
    - An open parenthesis. Note that this will not remember that this is
      the sides of a die and will not therefore allow the special tokens
      that can only exist as the sides of dice: the fudge die and the
      side list.
    """
    starters = 'd'
    codes = {code for code in OPERATORS if code.startswith('d')}

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (Integer, ListToken, FudgeDie, OpenParen)


class FudgeDie(State):
    """The "fudge die" value.

    Followed by the end of the expression or string.
    """
    starters = 'F'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def collect(self, agg: Sequence[str]) -> Optional[Token]:
        """Produces the side list [-1, 0, 1]."""
        return -1, 0, 1

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        """Goes directly to the end of the expression."""
        return ExprEnd(self.expr, self.i + 1)


class ListToken(State):
    """Collects a list of die sides into a single token."""
    # Overrides run so doesn't need to override collect or next_state
    starters = '['

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def run(self) -> Tuple[Token, 'State']:
        """Uses a sub-state machine to read the list."""
        sides = []
        state = ListStart(self.expr, self.i)
        while not isinstance(state, ListEnd):
            value, state = state.run()
            if value is not None:
                sides.append(value)
        return tuple(sides), ExprEnd(state.expr, state.i + 1)


class ListStart(State):
    """Starts the list.

    Can be followed by a value.
    """
    starters = '['

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ListValue,)


class ListValue(State):
    """A value in a sides list.

    Can be followed by a list separator or the end of the list.
    """
    starters = set(string.digits) | set('.')
    consumes = 1e6

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ListSeparator, ListEnd)

    def collect(self, agg: Sequence[str]) -> Optional[Union[Token, float]]:
        """Collects the sequence of characters into a float."""
        try:
            return float(''.join(agg))
        except ValueError:
            fmt = "{} cannot be interpreted as a decimal number."
            raise ParseError(fmt.format(''.join(agg)), self.i - len(agg), self.expr)


class ListSeparator(State):
    """The comma that separates the list values.

    Can only be followed by a value.
    """
    starters = ','

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ListValue,)


class ListEnd(State):
    """Ends the list.

    Followed by the end of the expression or string.
    """
    starters = ']'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)


class OpenParen(State):
    """An open parenthesis.

    Is followed by the start of an expression.
    """
    starters = '('

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart,)

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        """Goes directly into the start of an expression."""
        return ExprStart(self.expr, self.i + 1)

    def collect(self, agg: List[str]) -> Optional[Token]:
        """Produces the single character '('."""
        return '('


class CloseParen(State):
    """An closing parenthesis.

    Is followed by the end of an expression.
    """
    starters = ')'

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprEnd, InputEnd)

    def next_state(self, char: str, agg: Sequence[str] = None) -> Optional['State']:
        """Goes directly into the end of an expression."""
        return ExprEnd(self.expr, self.i + 1)

    def collect(self, agg: List[str]) -> Optional[Token]:
        """Produces the single character '('."""
        return ')'


class ExprStart(State):
    """The start of a subexpression.

    Can be followed by:

    - An open parenthesis (which also opens a new expression)
    - A unary prefix operator (the negative and positive marks)
    - A number
    """
    starters = State._recognized
    consumes = 0

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (OpenParen, UnaryPrefix, Integer)


class ExprEnd(State):
    """The end of a subexpression.

    Can be followed by:

    - A unary suffix operator (the only existing one is !)
    - A binary operator
    - A die expression (which is a subset of the binary operators)
    - A close parenthesis (which also terminates an enclosing
      subexpression)
    - The end of the input string
    """
    starters = State._recognized
    consumes = 0

    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (UnarySuffix, Binary, Die, CloseParen, InputEnd)


class InputStart(State):
    """The start of the string.

    Can be followed by:

    - The end of the input string, leading to an empty sequence of
      tokens.
    - The start of an expression.
    """
    def __init__(self, expr: str, i: int):
        super().__init__(expr, i)
        self.followers = (ExprStart, InputEnd)


class InputEnd(State):
    """The end of the string."""
    pass
