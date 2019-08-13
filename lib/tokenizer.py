import string
import typing

from .exceptions import ParseError
from .operators import OPERATORS, Operator, Roll

Value = typing.Union[Roll, int, typing.Tuple[float, ...]]
Token = typing.Union[Value, Operator, str]


def _string_to_operator(agg: str) -> typing.Union[str, Operator]:
    return OPERATORS.get(agg, agg)


def _read_list(s: str, mode=float) -> typing.Tuple[float, ...]:
    """Read a list defined in a string."""
    return tuple(map(mode, map(str.strip, s.split(','))))


def tokens(s: str) -> typing.List[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree and evaluated

    The basic algorithm is as follows:

    The number and operator aggregators are initialized to be empty.
    For each character in the input string,
    #.  If the character is a digit, add the character to the number aggregator. If the operator aggregator is nonempty,
        build an operator from it and push that operator onto the token list, then empty the operator aggregator.
    #.  If the character is one of the characters that may be part of an operator:
        #.  If the number aggregator is nonempty, build a number from it and push that number onto the token list.
        #.  If the character is '+' or '-', check if it is in a place that makes it look like a sign instead of the
            arithmetic operator. In general, it is a sign if it does not have a number to its left. However, the code
            actually checks if it is preceded by nothing (the start of the string) or by an operator. If it should be
            interpreted as a sign, build the operator from the aggregator if applicable, then push the sign operator
            directly onto the token list. This leaves the operator aggregator empty.
        #.  If the character can be added to the current aggregator and be a valid operator, or if the aggregator is
            empty, add the character to the aggregator. This allows us to always build the longest operator in cases
            where any one character could be ambiguous like '<='. Otherwise they are two separate operators and the
            aggregator should be built before pushing the new character on.
    #.  If the character is '[', it is the start of a list of dice sides, which can be floats and must be numbers. Read
        until the corresponding ']' is read and convert the slice into a tuple of floats.
    #.  If the character is 'F', it is the fudge die (-1, 0, or 1). It also has to appear as the sides of a die.
    #.  If the character satisfies none of these, it is ignored. This does have the weird effect that something like
        '24zzzz5' is interpreted as the number 245. This behavior may be dealt with in future. Perhaps throw a
        ``ParseError`` on any non-whitespace character encountered.

    :param s: The expression to be parsed
    :return: A list of tokens
    """
    # Every character that could be part of an operator
    possibilities = set(''.join(OPERATORS)) - set('p')
    nums = set(string.digits)
    curr_num: str = ''
    curr_op: str = ''
    tokenlist: typing.List[Token] = []
    i = 0
    while i < len(s):
        char = s[i]
        if char in nums:
            if curr_op:
                op = _string_to_operator(curr_op)
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
            if char in '+-' and (i == 0 or curr_op or tokenlist[-1] == '(' or isinstance(tokenlist[-1], Operator)):
                if curr_op:
                    tokenlist.append(_string_to_operator(curr_op))
                    curr_op = ''
                if char == '+':
                    tokenlist.append(_string_to_operator('p'))
                else:  # char is -
                    tokenlist.append(_string_to_operator('m'))
            else:
                if len(curr_op) == 0:
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
                    op = _string_to_operator(curr_op)
                    tokenlist.append(op)
                    curr_op = char
        elif char == '[':
            if curr_op not in ('d', 'da', 'dc', 'dm'):
                raise ParseError(f"A list can only appear as the sides of a die. Error at character {i}")
            if curr_op:
                tokenlist.append(_string_to_operator(curr_op))
                curr_op = ''
            # Start a list of floats
            sideList = []
            begin = i
            i += 1
            try:
                while s[i] != ']':
                    sideList.append(s[i])
                    i += 1
            except IndexError:
                raise ParseError("Unterminated die side list starting at character {start}: {slice}".format(
                    start=begin, slice=s[i - 5 if i - 5 >= 0 else 0:i + 5 if i + 5 < len(s) else len(s)]
                ))
            try:
                tokenlist.append(_read_list(''.join(sideList)))
            except ValueError:
                raise ParseError("All elements of the side list must be numbers.")
        elif char == 'F':
            if curr_op not in ('d', 'da', 'dc', 'dm'):
                raise ParseError("F is the 'fudge dice' value, and must appear as the side specifier of a roll. "
                                 "Error at character {}".format(i))
            if curr_op:
                tokenlist.append(_string_to_operator(curr_op))
                curr_op = ''
            # Fudge die
            tokenlist.append((-1, 0, 1))
        else:
            # Ignore all other characters
            # This includes whitespace and all printing characters that do not occur in at least
            # one operator expression
            pass
        i += 1
    # At most one will be occupied
    # And the only time neither will be is when the input string is empty
    if curr_num:
        tokenlist.append(int(curr_num))
    elif curr_op:
        tokenlist.append(_string_to_operator(curr_op))
    opens = tokenlist.count('(')
    closes = tokenlist.count(')')
    if opens > closes:
        raise ParseError("Unclosed parentheses detected.")
    if closes > opens:
        raise ParseError("Unopened parentheses detected.")
    return tokenlist
