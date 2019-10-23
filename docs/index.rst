Roll dice with Python
=====================

This is a python package aimed at performing rolls in a syntax that extends that used by D&D.
The full list of allowed operators is given by the page :ref:`operators` but most of the time you will use one of a few:

- "1d20" means "roll one 20-sided die." These get evaluated before any of the common operations like addition or multiplication.
- "+", "-", and the other simple arithmetic operators work as expected.
- Parentheses can be used as expected to force some expressions to be evaluated first.
- "2d20h1" means a d20 roll with advantage. More formally, it means "roll two 20-sided dice, then take the highest one." Similarly, "2d20l1" is disadvantage, as it takes the lowest one.
- "1d20r1" means a d20 roll with the halfling's "lucky" trait. It specifically means "roll a 20-sided die, then if the roll is a 1, reroll it and take the new result."

Installing this package through PyPI also installs the script ``roll`` that allows you to perform rolls from the command line.
It provides a variety of switches to explore the full functionality of this package.
The source of this script is found at ``dndice/roller.py`` in the repository.
If all you want is a way to roll dice with code, there you go. If you instead want to integrate this with something you're making, read on.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   entrypoint
   usage
   libraries

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
