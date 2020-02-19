"""Parse and evaluate roll expressions.

The functions "basic" and "verbose" are two ways of performing rolls,
depending on whether you want just the end result or a detailed record
of what dice were actually rolled. These are pulled into the top level
of this package for convenience.
The core functionality is held within the "lib" subpackage. That
contains the code to break expressions into tokens then parse them into
an expression tree for evaluation.
"""

# Hoist some core names straight into the public namespace
from .core import basic, verbose, Mode, compile, tokenize, tokenize_lazy
from .lib.exceptions import RollError, ParseError, EvaluationError
