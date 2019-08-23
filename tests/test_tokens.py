import itertools
import unittest

from dndice.lib import exceptions, operators, tokenizer


class TokenTester(unittest.TestCase):
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
            f"1{code}4": [1, op, 4] for code, op in operators.OPERATORS.items() if op.arity == operators.Side.BOTH
        }
        for s, tok in itertools.chain(unary.items(), binary.items()):
            self.assertEqual(tokenizer.tokens(s), tok)

    def test_parentheses(self):
        results = {
            "()": ["(", ")"],
            "(4)": ["(", 4, ")"],
            "(-4)": ["(", operators.OPERATORS['m'], 4, ")"],
            "2d(1d4)": [2, operators.OPERATORS['d'], "(", 1, operators.OPERATORS['d'], 4, ")"],
        }
        for s, tok in results.items():
            self.assertEqual(tokenizer.tokens(s), tok)

    def test_precedence(self):
        results = {
            "2*-1d4": [2, operators.OPERATORS['*'], operators.OPERATORS["m"], 1, operators.OPERATORS['d'], 4],
            "2+-6": [2, operators.OPERATORS['+'], operators.OPERATORS['m'], 6],
            "2+++6": [2, operators.OPERATORS['+'], operators.OPERATORS['p'], operators.OPERATORS['p'], 6]
        }
        for s, tok in results.items():
            self.assertEqual(tokenizer.tokens(s), tok)

    def test_whitespace(self):
        results = {
            "2 + 5": [2, operators.OPERATORS['+'], 5],
            "2 + -  6": [2, operators.OPERATORS['+'], operators.OPERATORS['m'], 6]
        }
        for s, tok in results.items():
            self.assertEqual(tokenizer.tokens(s), tok)

    def test_error(self):
        cases = [
            '(1d4d2',
            '1d[2, 3, 5',
            '1+4)',
            '1+F',
        ]
        for s in cases:
            with self.assertRaises(exceptions.ParseError):
                tokenizer.tokens(s)


if __name__ == '__main__':
    unittest.main()
