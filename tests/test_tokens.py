import itertools
import unittest

from dndice.lib import exceptions, operators, tokenizer


class TokenTester(unittest.TestCase):
    def compare_result(self, string, token):
        self.assertEqual(tokenizer.tokens(string), token,
                         '{} was supposed to parse into {}'.format(string, token))

    def token_conversions_mass_test(self, items):
        for string, token in items:
            yield self.compare_result, string, token

    def test_literal(self):
        results = {
            "1": [1],
            "": [],
            "20": [20],
        }
        for s, tok in results.items():
            self.assertEqual(tokenizer.tokens(s), tok)

    def test_single_ops(self):
        unary = {
            "4!": [4, operators.OPERATORS['!']],
            "-4": [operators.OPERATORS['m'], 4],
            "+4": [operators.OPERATORS['p'], 4],
        }
        binary = {
            "1" + code + "4": [1, op, 4]
            for code, op in operators.OPERATORS.items()
            if op.arity == operators.Side.BOTH
        }
        yield from self.token_conversions_mass_test(itertools.chain(unary.items(), binary.items()))

    def test_parentheses(self):
        results = {
            "(4)": ["(", 4, ")"],
            "(-4)": ["(", operators.OPERATORS['m'], 4, ")"],
            "2d(1d4)": [2, operators.OPERATORS['d'], "(", 1, operators.OPERATORS['d'], 4, ")"],
            "2*(4+8)": [2, operators.OPERATORS['*'], '(', 4, operators.OPERATORS['+'], 8, ')'],
            "(2)*((4)+(8))": ["(", 2, ")", operators.OPERATORS['*'], "(", "(", 4, ")",
                              operators.OPERATORS['+'], "(", 8, ")", ")"]
        }
        yield from self.token_conversions_mass_test(results.items())

    def test_precedence(self):
        results = {
            "2*-1d4": [2, operators.OPERATORS['*'], operators.OPERATORS["m"], 1,
                       operators.OPERATORS['d'], 4],
            "2+-6": [2, operators.OPERATORS['+'], operators.OPERATORS['m'], 6],
            "2+++6": [2, operators.OPERATORS['+'], operators.OPERATORS['p'],
                      operators.OPERATORS['p'], 6]
        }
        yield from self.token_conversions_mass_test(results.items())

    def test_whitespace(self):
        results = {
            "2 + 5": [2, operators.OPERATORS['+'], 5],
            "2 + -  6": [2, operators.OPERATORS['+'], operators.OPERATORS['m'], 6],
            "( 2d[1, 4,  6] ) ": ['(', 2, operators.OPERATORS['d'], (1, 4, 6), ')'],
            "     \t  \n ": [],
        }
        yield from self.token_conversions_mass_test(results.items())

    def test_error(self):
        cases = [
            '(1d4d2',
            '1d[2, 3, 5',
            '1+4)',
            '1+F',
            '1a4',
            '1x4',
        ]
        for s in cases:
            with self.assertRaises(exceptions.ParseError):
                tokenizer.tokens(s)

    def test_list(self):
        results = {
            "1d[1,5,9]": [1, operators.OPERATORS['d'], (1, 5, 9)],
            "1d[1.5,5,9]": [1, operators.OPERATORS['d'], (1.5, 5, 9)],
        }
        yield from self.token_conversions_mass_test(results.items())
        with self.assertRaises(exceptions.ParseError):
            tokenizer.tokens("[4,5,6]+3")
        with self.assertRaises(exceptions.ParseError):
            tokenizer.tokens("1d[4, 5, b]")

    def test_fudge(self):
        results = {
            "2dF": [2, operators.OPERATORS['d'], (-1, 0, 1)]
        }
        yield from self.token_conversions_mass_test(results.items())
        with self.assertRaises(exceptions.ParseError):
            tokenizer.tokens('Fd6')

    def test_parse_error(self):
        results = {
            "(1d4d2": "Unclosed parenthesis detected.\n    (1d4d2\n    ^",
            "1+F": "F is the 'fudge dice' value, and must appear as the side specifier of a "
                   "roll.\n    1+F\n      ^",
            "1+4)": "Unopened parenthesis detected.\n    1+4)\n       ^",
            "2*((4+)8)": "Unexpectedly terminated expression.\n    2*((4+)8)\n          ^",
            "1 > = 4": "Token is already broken.\n    1 > = 4\n        ^",
            "4d6rhl6": "l is not allowed in this position.\n    4d6rhl6\n         ^",
            "1d[1.4.4,2]": "1.4.4 cannot be interpreted as a decimal number.\n"
                           "    1d[1.4.4,2]\n       ^",
        }
        for expr, expected in results.items():
            try:
                tokenizer.tokens(expr)
            except exceptions.ParseError as e:
                self.assertEqual(str(e), expected)

    def test_double_operator(self):
        results = {
            "4!-4": [4, operators.OPERATORS['!'], operators.OPERATORS['-'], 4],
        }
        yield from self.token_conversions_mass_test(results.items())

    def test_multi_character(self):
        results = {
            '10 >= 5': [10, operators.OPERATORS['>='], 5]
        }
        yield from self.token_conversions_mass_test(results.items())


if __name__ == '__main__':
    unittest.main()
