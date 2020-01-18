"""Exceptions to cover error cases that may be encountered in this package.

A base class for all of them is ``RollError``, which means that any
function ever thrown by this package can be caught by catching
``RollError``.

A ``ParseError`` is thrown when the initial expression cannot be parsed
into an expression tree. Most of these errors occur at the initial
tokenization step, but ones that are harder to catch there may be
tokenized then fail to construct a valid tree.

An ``InputTypeError`` indicate that the wrong type of element was passed
into one of the main entry point functions like ``roll``.

An ``EvaluationError`` happen when something goes wrong while evaluating
the expression tree. These can be split into ``ArgumentTypeError`` and
``ArgumentValueError``, with the same semantics as the builtin
``TypeError`` and ``ValueError``.
"""


class RollError(Exception):
    """A simple base class for all exceptions raised by this module."""
    pass


# This would instead inherit from SyntaxError but that produces much
# unwanted behavior in how the traceback is constructed and printed
class ParseError(RollError, ValueError):
    """The roll expression cannot be parsed into an expression tree."""

    def __init__(self, msg, offset, expr):
        self.msg = msg
        self.character = offset
        self.expr = expr
        self.indent = 4

    def __str__(self):
        fmt = "{msg}\n{indent}{expr}\n{indent}{spaces}^"
        return fmt.format(expr=self.expr, msg=self.msg, spaces=" " * self.character,
                          indent=" " * self.indent)

    def __repr__(self):
        return self.__str__()


class InputTypeError(RollError, TypeError):
    """You passed the wrong thing into the entry point function."""
    pass


class EvaluationError(RollError, RuntimeError):
    """The roll could not be evaluated."""
    pass


class ArgumentValueError(EvaluationError, ValueError):
    """The value of an expression cannot be used."""
    pass


class ArgumentTypeError(EvaluationError, TypeError):
    """An expression in the roll is of the wrong type."""
    pass
