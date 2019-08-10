import typing
from itertools import groupby

from pyparsing import ParserElement, PrecededBy, opAssoc, StringStart, oneOf, Literal, infixNotation, pyparsing_common

from operators import OPERATORS, Operator, Side

ParserElement.enablePackrat()
OperatorDef = typing.Tuple[str, int, typing.Any, typing.Callable]


def string_to_operator(s: str) -> typing.Union[str, Operator]:
    return OPERATORS.get(s, s)


def _convert_operator_on_parse(toks):
    return string_to_operator(toks[0])


def _convert_num_on_parse(toks):
    return int(toks[0])


def create_number_matches() -> ParserElement:
    number = pyparsing_common.integer
    number.setParseAction(_convert_num_on_parse)
    # Fudge dice and lists are going to be deprecated as possible values
    # fudge = PrecededBy('d') + Literal('F')
    return number


def _format_operator_match(operators: typing.List[Operator]) -> OperatorDef:
    # Prerequisite: all operators in the group have the same precedence and associativity and arity
    if operators[0].associativity == Side.LEFT:
        ass = opAssoc.LEFT
    else:
        ass = opAssoc.RIGHT
    action = _convert_operator_on_parse
    # SPECIAL CASE: precedence level 4 is the unary sign operators
    if operators[0].precedence == 4:
        possibilities = oneOf([op.code for op in OPERATORS.values()] + ['('])
        determinant = PrecededBy(StringStart() | possibilities, retreat=1)
        negative = determinant + Literal('-')
        positive = determinant + Literal('+')
        match = negative | positive
    else:
        match = oneOf([(op.viewAs or op.code) for op in operators])
    # Assume no 0-arity operators
    arity = 2 if operators[0].arity == Side.BOTH else 1
    return match, arity, ass, action


def create_operator_matches() -> typing.List[OperatorDef]:
    ops = [op for op in OPERATORS.values()]
    # sort by precedence highest to lowest then by length from longest to shortest
    # grouping associativity along the way
    ops.sort(key=lambda op: (op.precedence, op.associativity, op.arity, len(op.code)), reverse=True)
    groups_gen = groupby(ops, key=lambda op: (op.precedence, op.associativity, op.arity))
    operatorDefs = [_format_operator_match(list(group)) for _, group in groups_gen]
    return operatorDefs


def create_grammar() -> ParserElement:
    return infixNotation(create_number_matches(), create_operator_matches())


grammar = create_grammar()

if __name__ == '__main__':
    tokens = grammar.parseString("1d4")
    print(tokens)
    # grammar.parseString("-3d6")
    print(grammar.parseString("1d6d4"))
    print(grammar.parseString("1d4+2"))
    print(grammar.parseString("4d6*3+2*4"))
    print(grammar.parseString("4d6*(-3+2*4)"))
