import string
import typing

from exceptions import ParseError
from operators import OPERATORS, Operator, Roll

Value = typing.Union[Roll, int, typing.Tuple[float, ...]]
Token = typing.Union[Value, Operator, str]


def _aggregator_to_operator(agg: typing.List[str]) -> typing.Union[str, Operator]:
    s = ''.join(agg)
    return OPERATORS.get(s, s)


def _read_list(s: str, mode=float) -> typing.Tuple[float, ...]:
    """Read a list defined in a string."""
    return tuple(map(mode, map(str.strip, s.split(','))))


def tokens(s: str) -> typing.List[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree and evaluated

    The basic algorithm is as follows:

    :param s: The expression to be parsed
    :return: A list of tokens
    """
    # Every character that could be part of an operator
    possibilities = set(''.join(OPERATORS))
    nums = set(string.digits)
    curr_num: typing.List[str] = []
    curr_op: typing.List[str] = []
    tokenlist: typing.List[Token] = []
    i = 0
    while i < len(s):
        char = s[i]
        if char in nums:
            if curr_op:
                op = _aggregator_to_operator(curr_op)
                tokenlist.append(op)
                curr_op = []
            curr_num.append(char)
        elif char in possibilities or char in '()':
            # Things that will end up on the operators stack
            if curr_num:
                tokenlist.append(int(''.join(curr_num)))
                curr_num = []
            # + and - are the unary operators iff they occur at the beginning of an expression
            # or immediately after another operator
            if char in '+-' and (i == 0 or tokenlist[-1] == '(' or curr_op or isinstance(tokenlist[-1], Operator)):
                if curr_op:
                    tokenlist.append(_aggregator_to_operator(curr_op))
                    curr_op = []
                if char == '+':
                    tokenlist.append(_aggregator_to_operator(['p']))
                else:  # char is -
                    tokenlist.append(_aggregator_to_operator(['m']))
            else:
                if len(curr_op) == 0:
                    # This is the first time you see an operator since last
                    # time the list was cleared
                    curr_op.append(char)
                elif ''.join(curr_op + [char]) in OPERATORS:
                    # This means that the current char is part of a
                    # multicharacter operation like <=
                    curr_op.append(char)
                else:
                    # Two separate operators; push out the old one and start
                    # collecting the new one
                    op = _aggregator_to_operator(curr_op)
                    tokenlist.append(op)
                    curr_op = [char]
        elif char == '[':
            if curr_op:
                tokenlist.append(_aggregator_to_operator(curr_op))
                curr_op = []
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
            tokenlist.append(_read_list(''.join(sideList)))
        elif char == 'F':
            if ''.join(curr_op) not in ('d', 'da', 'dc', 'dm'):
                raise ParseError("F is the 'fudge dice' value, and must appear as the side specifier of a roll. "
                                 "Error at {}".format(i))
            if curr_op:
                tokenlist.append(_aggregator_to_operator(curr_op))
                curr_op = []
            # Fudge die
            tokenlist.append((-1, 0, 1))
        else:
            # Ignore all other characters
            # This includes whitespace and all printing characters that do not occur in at least
            # one operator expression
            pass
        i += 1
    if curr_num:
        tokenlist.append(int(''.join(curr_num)))
    elif curr_op:
        tokenlist.append(_aggregator_to_operator(curr_op))
    opens = tokenlist.count('(')
    closes = tokenlist.count(')')
    if opens > closes:
        raise ParseError("Unclosed parentheses detected.")
    if closes > opens:
        raise ParseError("Unopened parentheses detected.")
    return tokenlist
