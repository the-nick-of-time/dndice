class RollError(Exception):
    """A simple base class for all exceptions raised by this module."""
    pass


class ParseError(RollError, ValueError):
    """The roll expression was malformed as to prevent parsing into an expression tree."""
    pass


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
