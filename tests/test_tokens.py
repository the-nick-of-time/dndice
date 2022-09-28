import itertools

import pytest

from dndice.lib import exceptions, operators, tokenizer


def compare_result(string, token):
    assert tokenizer.tokens(string) == token, '{} was supposed to parse into {}'.format(string, token)


def token_conversions_mass_test(items):
    for string, token in items:
        yield compare_result, string, token


@pytest.mark.parametrize("expr,expected", {
    "1": [1],
    "": [],
    "20": [20],
}.items())
def test_literal(expr, expected):
    compare_result(expr, expected)


@pytest.mark.parametrize("expr,expected", itertools.chain(
    {
        "4!": [4, operators.OPERATORS['!']],
        "-4": [operators.OPERATORS['m'], 4],
        "+4": [operators.OPERATORS['p'], 4],
    }.items(),
    {
        "1" + code + "4": [1, op, 4]
        for code, op in operators.OPERATORS.items()
        if op.arity == operators.Side.BOTH
    }.items()
))
def test_single_ops(expr, expected):
    compare_result(expr, expected)


@pytest.mark.parametrize("expr,expected", {
    "(4)": ["(", 4, ")"],
    "(-4)": ["(", operators.OPERATORS['m'], 4, ")"],
    "2d(1d4)": [2, operators.OPERATORS['d'], "(", 1, operators.OPERATORS['d'], 4, ")"],
    "2*(4+8)": [2, operators.OPERATORS['*'], '(', 4, operators.OPERATORS['+'], 8, ')'],
    "(2)*((4)+(8))": ["(", 2, ")", operators.OPERATORS['*'], "(", "(", 4, ")",
                      operators.OPERATORS['+'], "(", 8, ")", ")"]
}.items())
def test_parentheses(expr, expected):
    compare_result(expr, expected)


@pytest.mark.parametrize("expr,expected", {
    "2*-1d4": [2, operators.OPERATORS['*'], operators.OPERATORS["m"], 1,
               operators.OPERATORS['d'], 4],
    "2+-6": [2, operators.OPERATORS['+'], operators.OPERATORS['m'], 6],
    "2+++6": [2, operators.OPERATORS['+'], operators.OPERATORS['p'],
              operators.OPERATORS['p'], 6]
}.items())
def test_precedence(expr, expected):
    compare_result(expr, expected)


@pytest.mark.parametrize("expr,expected", {
    "2 + 5": [2, operators.OPERATORS['+'], 5],
    "2 + -  6": [2, operators.OPERATORS['+'], operators.OPERATORS['m'], 6],
    "( 2d[1, 4,  6] ) ": ['(', 2, operators.OPERATORS['d'], (1, 4, 6), ')'],
    "     \t  \n ": [],
}.items())
def test_whitespace(expr, expected):
    compare_result(expr, expected)


@pytest.mark.parametrize("expr", [
    '(1d4d2',
    '1d[2, 3, 5',
    '1+4)',
    '1+F',
    '1a4',
    '1x4',
])
def test_error(expr):
    with pytest.raises(exceptions.ParseError):
        tokenizer.tokens(expr)


@pytest.mark.parametrize("expr,expected", {
    "1d[1,5,9]": [1, operators.OPERATORS['d'], (1, 5, 9)],
    "1d[1.5,5,9]": [1, operators.OPERATORS['d'], (1.5, 5, 9)],
}.items())
def test_list(expr, expected):
    compare_result(expr, expected)


def test_list_misplaced():
    with pytest.raises(exceptions.ParseError):
        tokenizer.tokens("[4,5,6]+3")


def test_list_wrong_value():
    with pytest.raises(exceptions.ParseError):
        tokenizer.tokens("1d[4, 5, b]")


@pytest.mark.parametrize("expr,expected", {
    "2dF": [2, operators.OPERATORS['d'], (-1, 0, 1)]
}.items())
def test_fudge(expr, expected):
    compare_result(expr, expected)


def test_fudge_misplaced():
    with pytest.raises(exceptions.ParseError):
        tokenizer.tokens('Fd6')


@pytest.mark.parametrize("expr,expected", {
    "(1d4d2": "Unclosed parenthesis detected.\n    (1d4d2\n    ^",
    "1+F": "F is the 'fudge dice' value, and must appear as the side specifier of a "
           "roll.\n    1+F\n      ^",
    "1+4)": "Unopened parenthesis detected.\n    1+4)\n       ^",
    "2*((4+)8)": "Unexpectedly terminated expression.\n    2*((4+)8)\n          ^",
    "1 > = 4": "Token is already broken.\n    1 > = 4\n        ^",
    "4d6rhl6": "l is not allowed in this position.\n    4d6rhl6\n         ^",
    "1d[1.4.4,2]": "1.4.4 cannot be interpreted as a decimal number.\n"
                   "    1d[1.4.4,2]\n       ^",
}.items())
def test_parse_error(expr, expected):
    try:
        tokenizer.tokens(expr)
        pytest.fail("{} should have failed to parse".format(expr))
    except exceptions.ParseError as e:
        assert str(e) == expected


@pytest.mark.parametrize("expr,expected", {
    "4!-4": [4, operators.OPERATORS['!'], operators.OPERATORS['-'], 4],
}.items())
def test_double_operator(expr, expected):
    compare_result(expr, expected)


@pytest.mark.parametrize("expr,expected", {
    '10 >= 5': [10, operators.OPERATORS['>='], 5]
}.items())
def test_multi_character(expr, expected):
    compare_result(expr, expected)
