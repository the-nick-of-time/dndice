Library modules
===============

These libraries are mainly for internal use, but are exposed at the top level to be used elsewhere if needed.



``exceptions``
==============

This is most likely to be used as external applications may want to catch any errors raised by this package.

.. automodule:: rolling.exceptions


``operators``
=============

This module holds the operator definitions, and may be worth importing if any extensions are desired.

.. automodule:: rolling.operators


``evaltree``
============

This module implements an expression tree for use by the algorithms in this package, and may be imported to extend build on existing functionality.

.. automodule:: rolling.evaltree


``helpers``
=============

This module is for a few helpful decorators, which have probably been implemented elsewhere already.

.. automodule:: rolling.helpers


``tokenizer``
=============

.. automodule:: rolling.tokenizer

