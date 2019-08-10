import string
import typing

from operators import OPERATORS, Operator, Roll

Value = typing.Union[Roll, int, typing.List[float]]
Token = typing.Union[Value, Operator]


def _string_to_operator(s: str) -> typing.Union[str, Operator]:
    return OPERATORS.get(s, s)


def _read_list(s: str, mode=float) -> typing.Iterable[float]:
    """Read a list defined in a string."""
    return list(map(mode, map(str.strip, s.split(','))))


def tokens(s: str) -> typing.List[Token]:
    """Splits an expression into tokens that can be parsed into an expression tree and evaluated

    :param s: The expression to be parsed
    :return: A list of tokens
    """
    # Every character that could be part of an operator
    possibilities = set(''.join(OPERATORS))
    curr_num = []
    curr_op = []
    tokenlist = []
    i = 0
    while i < len(s):
        char = s[i]
        if char in string.digits:
            if curr_op:
                op = _string_to_operator(''.join(curr_op))
                tokenlist.append(op)
                curr_op = []
            curr_num.append(char)
        elif char in possibilities or char in '()':
            # Things that will end up on the operators stack
            if curr_num:
                tokenlist.append(int(''.join(curr_num)))
                curr_num = []
            if char == '+' and (i == 0 or s[i - 1] in possibilities or s[i - 1] == '('):
                tokenlist.append(_string_to_operator('p'))
                curr_op = []
            elif char == '-' and (i == 0 or s[i - 1] in possibilities or s[i - 1] == '('):
                tokenlist.append(_string_to_operator('m'))
                curr_op = []
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
                    op = _string_to_operator(''.join(curr_op))
                    tokenlist.append(op)
                    curr_op = [char]
        elif char == '[':
            if curr_op:
                tokenlist.append(_string_to_operator(''.join(curr_op)))
                curr_op = []
            # Start a list of floats
            sidelist = []
            i += 1
            while s[i] != ']':
                sidelist.append(s[i])
                i += 1
            tokenlist.append(_read_list(''.join(sidelist)))
        elif char == 'F':
            if curr_op:
                tokenlist.append(_string_to_operator(''.join(curr_op)))
                curr_op = []
            # Fudge die
            tokenlist.append([-1, 0, 1])
        i += 1
    if curr_num:
        tokenlist.append(int(''.join(curr_num)))
    elif curr_op:
        tokenlist.append(_string_to_operator(''.join(curr_op)))
    return tokenlist
