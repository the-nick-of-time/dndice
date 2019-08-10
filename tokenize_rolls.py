import typing

from pyparsing import ParserElement, Word, nums, PrecededBy, opAssoc, StringStart, oneOf

from operators import OPERATORS, Operator, Side


def string_to_operator(s: str) -> typing.Union[str, Operator]:
    return OPERATORS.get(s, s)


def _convert_operator_on_parse(toks):
    return string_to_operator(toks[0])


def _convert_num_on_parse(toks):
    return int(toks[0])


# def create_operator_matches() -> ParserElement:
#     # Sorted from longest to shortest (2-length before 1-length) because the 2s need a chance to match before the 1s do
#     opcodes = sorted([key for key in operators], key=lambda code: len(code), reverse=True)
#     # Filter out the placeholders for the unary operators
#     opcodes.remove('m')
#     opcodes.remove('p')
#     # Catch ( and )
#     opcodes.append('(')
#     opcodes.append(')')
#     # TODO: URGENT: Create special matchers (regex?) to distinguish unary plus and minus from binary
#     literalMatches = [Literal(code) for code in opcodes]
#     composite = literalMatches[0]
#     for matcher in literalMatches[1:]:
#         composite = composite | matcher
#     return composite


def create_number_matches() -> ParserElement:
    number = Word(nums)
    number.setParseAction(lambda toks: int(toks[0]))
    # Fudge dice and lists are going to be deprecated as possible values
    # fudge = PrecededBy('d') + Literal('F')
    return number


def _format_operator_match(operator: Operator) -> typing.Tuple[str, int, opAssoc, typing.Callable]:
    if operator.associativity == Side.LEFT:
        ass = opAssoc.LEFT
    else:
        ass = opAssoc.RIGHT
    action = _convert_operator_on_parse
    match = operator.code
    possibilities = oneOf([op.code for op in OPERATORS] + ['('])
    determinant = PrecededBy(StringStart() | possibilities)
    if operator == 'm':
        match = determinant + '-'
    elif operator == 'p':
        match = determinant + '+'
    return match, operator.arity, ass, action


def create_operator_matches():
    ops = [op for op in OPERATORS.values()]
    # sort by precedence highest to lowest then by length from longest to shortest
    ops.sort(key=lambda op: (op.precedence, len(op.code)), reverse=True)
    prec = ops[0].precedence
    group = []
    groups = []
    for op in ops:
        if op.precedence == prec:
            group.append(op)
        else:
            prec = op.precedence
            groups.append(group)
            group = [op]


def create_grammar() -> ParserElement:
    pass
