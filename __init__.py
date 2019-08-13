import sys as __sys
import os as __os

# Access whole modules
from .lib import operators
from .lib import exceptions
from .lib import evaltree
from .lib import helpers
from .lib import tokenizer

# rolling.py's imports work for running it as a script but not importing as a module
# So here we correct that
__sys.path.insert(0, __os.path.dirname(__file__))

# Hoist some core names straight into the public namespace
from .rolling import roll, compile, tokenize, basic, verbose, Mode
