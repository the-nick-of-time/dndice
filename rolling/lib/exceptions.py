class RollError(Exception):
    """A simple base class for all exceptions raised by this module."""
    pass


class ParseError(RollError, ValueError):
    """The roll expression was malformed as to prevent parsing into an expression tree."""

    def __init__(self, msg, offset=None, expr=None):
        self.msg = msg
        self.character = offset
        self.expr = expr
        self.indent = 4

    def __str__(self):
        if self.character and self.expr:
            fmt = "{msg}\n{indent}{expr}\n{spaces}^"
            return fmt.format(expr=self.expr, msg=self.msg, spaces=" " * (self.character + self.indent),
                              indent=" " * self.indent)
        else:
            return self.msg

    def __repr__(self):
        return self.__str__()


class EvaluationError(RollError, RuntimeError):
    """The roll could not be evaluated."""
    pass


class ArgumentValueError(EvaluationError):
    """The value of an expression cannot be used."""
    pass


class ArgumentTypeError(EvaluationError):
    """An expression in the roll is of the wrong type."""
    pass


class InputTypeError(EvaluationError):
    """You passed the wrong thing into the entry point function."""
    pass
