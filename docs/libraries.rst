Library modules
===============

These libraries are mainly for internal use, but are exposed at the top level to be used elsewhere if needed.


``exceptions``
--------------

This is most likely to be used as external applications may want to catch any errors raised by this package.

.. automodule:: dndice.lib.exceptions
    :members:
    :show-inheritance:


``operators``
-------------

This module holds the operator definitions, and may be worth importing if any extensions are desired.

.. automodule:: dndice.lib.operators
    :members:
    :special-members: __init__, __call__,


``evaltree``
------------

This module implements an expression tree for use by the algorithms in this package, and may be imported to extend build on existing functionality.

.. automodule:: dndice.lib.evaltree
    :members:
    :special-members:


``helpers``
-----------

This module is for a few helpful decorators, which have probably been implemented elsewhere already.

.. automodule:: dndice.lib.helpers
    :members:


``tokenizer``
-------------

.. automodule:: dndice.lib.tokenizer
    :members:
    :member-order: bysource


