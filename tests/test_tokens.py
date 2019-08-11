import itertools
import unittest

from exceptions import ParseError
from operators import OPERATORS, Side
from tokenizer import tokens


class TokenTester(unittest.TestCase):
    def test_literal(self):
        results = {
            "1": [1],
            "": [],
            "20": [20],
        }
        for s, tok in results.items():
            self.assertEqual(tokens(s), tok)

    def test_single_ops(self):
        unary = {
            "4!": [4, OPERATORS['!']],
            "-4": [OPERATORS['m'], 4],
            "+4": [OPERATORS['p'], 4],
        }
        binary = {f"1{code}4": [1, op, 4] for code, op in OPERATORS.items() if op.arity == Side.BOTH}
        for s, tok in itertools.chain(unary.items(), binary.items()):
            self.assertEqual(tokens(s), tok)

    def test_parentheses(self):
        results = {
            "()": ["(", ")"],
            "(4)": ["(", 4, ")"],
            "(-4)": ["(", OPERATORS['m'], 4, ")"],
            "2d(1d4)": [2, OPERATORS['d'], "(", 1, OPERATORS['d'], 4, ")"],
        }
        for s, tok in results.items():
            self.assertEqual(tokens(s), tok)

    def test_precedence(self):
        results = {
            "2*-1d4": [2, OPERATORS['*'], OPERATORS["m"], 1, OPERATORS['d'], 4],
            "2+-6": [2, OPERATORS['+'], OPERATORS['m'], 6],
            "2+++6": [2, OPERATORS['+'], OPERATORS['p'], OPERATORS['p'], 6]
        }
        for s, tok in results.items():
            self.assertEqual(tokens(s), tok)

    def test_whitespace(self):
        results = {
            "2 + 5": [2, OPERATORS['+'], 5],
            "2 + -  6": [2, OPERATORS['+'], OPERATORS['m'], 6]
        }
        for s, tok in results.items():
            self.assertEqual(tokens(s), tok)

    def test_error(self):
        cases = [
            '(1d4d2',
            '1d[2, 3, 5',
            '1+4)',
            '1+F',
        ]
        for s in cases:
            with self.assertRaises(ParseError):
                tokens(s)


if __name__ == '__main__':
    unittest.main()
