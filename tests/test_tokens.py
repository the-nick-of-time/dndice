import itertools
import unittest

from .context import operators
from .context import tokenizer

tokens = tokenizer.tokens
OPERATORS = operators.OPERATORS
Side = operators.Side


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
        binary = {f"1{op}4": [1, OPERATORS[op], 4] for op in OPERATORS if OPERATORS[op].arity == Side.BOTH}
        for s, tok in itertools.chain(unary.items(), binary.items()):
            self.assertEqual(tokens(s), tok)

    def test_parentheses(self):
        results = {
            "()": ["(", ")"],
            "(4)": ["(", 4, ")"],
            "(-4)": ["(", OPERATORS['m'], 4, ")"],
            "2d(1d4)": [2, OPERATORS['d'], "(", OPERATORS['m'], 4, ")"],
        }

    def test_precedence(self):
        results = {
            "2*-1d4": [2, OPERATORS['*'], OPERATORS["m"], 1, OPERATORS['d'], 4]
        }


if __name__ == '__main__':
    unittest.main()
