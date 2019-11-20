"""Split a string into a list of tokens, meaning operators or values.

Only one name is useful to the outside world: ``tokens``. This is the
function that actually performs the tokenization.
"""
import string
import typing

from .exceptions import ParseError
from .operators import OPERATORS, Operator, Roll, Side

Value = typing.Union[Roll, int, typing.Tuple[float, ...]]
Token = typing.Union[Value, Operator, str]


def _string_to_operator(agg: str, offset: int, expr: str) -> Operator:
    """Converts a string to the corresponding Operator.

    :param agg: The string that should be an operator.
    :param offset: The current position in the string.
    :param expr: The total expression.
    :raises ParseError: On an invalid operator.
    :return: The Operator or, if the input was a parenthesis, the original string.
    """
    if agg not in OPERATORS:
        raise ParseError("Invalid operator.", offset - len(agg), expr)
    return OPERATORS[agg]


def _read_list(s: str, mode=float) -> typing.Tuple[float, ...]:
    """Read a list defined in a string."""
    return tuple(map(mode, map(str.strip, s.split(','))))


def tokens(s: str) -> typing.List[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree and evaluated

    The basic algorithm is as follows:

    The number and operator aggregators are initialized to be empty.
    For each character in the input string,

    #.  If the character is a digit, add the character to the number
        aggregator. If the operator aggregator is nonempty, build an
        operator from it and push that operator onto the token list,
        then empty the operator aggregator.

    #.  If the character is one of the characters that may be part of an
        operator:

        #.  If the number aggregator is nonempty, build a number from it
            and push that number onto the token list.

        #.  If the character is '+' or '-', check if it is in a place
            that makes it look like a sign instead of the arithmetic
            operator. In general, it is a sign if it does not have a
            number to its left. However, the code actually checks if it
            is preceded by nothing (the start of the string) or by an
            operator. If it should be interpreted as a sign, build the
            operator from the aggregator if applicable, then push the
            sign operator directly onto the token list. This leaves the
            operator aggregator empty.

        #.  If the character can be added to the current aggregator and
            be a valid operator, or if the aggregator is empty, add the
            character to the aggregator. This allows us to always build
            the longest operator in cases where any one character could
            be ambiguous like '<='. Otherwise they are two separate
            operators and the aggregator should be built before pushing
            the new character on.

    #.  If the character is '[', it is the start of a list of dice
        sides, which can be floats and must be numbers. Read until the
        corresponding ']' is read and convert the slice into a tuple of
        floats.

    #.  If the character is 'F', it is the fudge die (-1, 0, or 1). It
        also has to appear as the sides of a die.

    #.  If the character is whitespace, it is ignored.

    #.  If the character satisfies none of these, it throws a
        ``ParseError``.

    :param s: The expression to be parsed
    :return: A list of tokens
    """
    # Check for unbalanced parentheses
    opens = s.count('(')
    closes = s.count(')')
    if opens > closes:
        raise ParseError("Unclosed parenthesis detected.", s.find('('), s)
    if closes > opens:
        raise ParseError("Unopened parenthesis detected.", s.rfind(')'), s)
    # Every character that could be part of an operator
    possibilities = set(''.join(OPERATORS)) - set('p')
    nums = set(string.digits)
    curr_num = ''
    curr_op = ''
    tokenlist = []
    i = 0
    while i < len(s):
        char = s[i]
        if char in nums:
            if curr_op:
                op = _string_to_operator(curr_op, i, s)
                tokenlist.append(op)
                curr_op = ''
            curr_num += char
        elif char in possibilities or char in '()':
            # Things that will end up on the operators stack
            if curr_num:
                tokenlist.append(int(curr_num))
                curr_num = ''
            # + and - are the unary operators iff they occur at the beginning of an expression
            # or immediately after another operator
            if char in '+-' and (i == 0 or (curr_op and curr_op != '!') or tokenlist[-1] == '('
                                 or (isinstance(tokenlist[-1], Operator)
                                     and tokenlist[-1].arity & Side.RIGHT)):
                if curr_op:
                    tokenlist.append(_string_to_operator(curr_op, i, s))
                    curr_op = ''
                if char == '+':
                    tokenlist.append(_string_to_operator('p', i, s))
                else:  # char is -
                    tokenlist.append(_string_to_operator('m', i, s))
            else:
                if char in '()':
                    # Parentheses can never be part of an operator, and them occupying space
                    # there can cause false positives when checking for unary operators
                    if curr_op:
                        tokenlist.append(_string_to_operator(curr_op, i, s))
                        if (isinstance(tokenlist[-1], Operator)
                                and ((char == ')' and tokenlist[-1].arity & Side.RIGHT)
                                     or (char == '(' and not tokenlist[
                                                                 -1].arity & Side.RIGHT))):
                            raise ParseError('Unexpectedly terminated expression.', i, s)
                    tokenlist.append(char)
                    curr_op = ''
                elif len(curr_op) == 0:
                    # This is the first time you see an operator since last
                    # time the list was cleared
                    curr_op += char
                elif curr_op + char in OPERATORS:
                    # This means that the current char is part of a
                    # multicharacter operation like <=
                    curr_op += char
                else:
                    # Two separate operators; push out the old one and start
                    # collecting the new one
                    op = _string_to_operator(curr_op, i, s)
                    tokenlist.append(op)
                    curr_op = char
        elif char == '[':
            if curr_op not in ('d', 'da', 'dc', 'dm'):
                raise ParseError("A list can only appear as the sides of a die.", i, s)
            if curr_op:
                tokenlist.append(_string_to_operator(curr_op, i, s))
                curr_op = ''
            # Start a list of floats
            sideList = []
            begin = i
            i += 1
            try:
                while s[i] != ']':
                    sideList.append(s[i])
                    i += 1
            except IndexError as e:
                raise ParseError("Unterminated die side list.", begin, s) from e
            try:
                tokenlist.append(_read_list(''.join(sideList)))
            except ValueError as e:
                raise ParseError("All elements of the side list must be numbers.", i, s) from e
        elif char == 'F':
            if curr_op not in ('d', 'da', 'dc', 'dm'):
                raise ParseError("F is the 'fudge dice' value, and must appear as the side "
                                 "specifier of a roll.", i, s)
            if curr_op:
                tokenlist.append(_string_to_operator(curr_op, i, s))
                curr_op = ''
            # Fudge die
            tokenlist.append((-1, 0, 1))
        elif char.isspace():
            pass
        else:
            raise ParseError("Unrecognized character detected.", i, s)
        i += 1
    # At most one will be occupied
    # And the only time neither will be is when the input string is empty
    if curr_num:
        tokenlist.append(int(curr_num))
    elif curr_op:
        tokenlist.append(_string_to_operator(curr_op, i, s))
    return tokenlist
