"""Defines code representations of arithmetic and rolling operators.

The single most important export from this module is the ``OPERATORS``
constant. It is a dictionary mapping from the operator codes (think '+',
'>=', 'd', etc.) to the actual operator objects.

You might also want to pull out the ``Side`` enum and ``Operator`` class
if you want to define your own or otherwise do some customization with
the operators.

The ``Roll`` object could be useful if you are trying to extend the
rolling functionality.

All the various functions are not really worth talking about, they just
implement the operations defined here.
"""
import enum
import random
import typing
from contextlib import contextmanager
from copy import deepcopy

from .exceptions import ArgumentTypeError, ArgumentValueError
from .helpers import check_simple_types, wrap_exceptions_with

Number = typing.Union[int, float]


class Side(enum.IntEnum):
    """Represents which side an operation is applicable to.

    Note that checking if an operation includes one side is as simple as
    checking ``Operator.arity & Side.LEFT`` or
    ``Operator.arity & Side.RIGHT``, whichever one you want.
    """
    RIGHT = 0b01
    LEFT = 0b10
    BOTH = 0b11
    NEITHER = 0b00


class Operator:
    """An operator like + or d that can be applied to values.

    This class implements a full ordering, but ``==`` has very different
    semantics. The ordering operators (``>``, ``<``, ``>=``, ``<=``) all
    compare the precedence of two given operators. ``==`` on the other
    hand compares value/identity, so it is intended to match when
    comparing two instances of the same operator or, more importantly,
    comparing an ``Operator`` to the string that should produce it. For
    instance, the ``Operator`` instance for addition should return
    ``True`` for ``addition == '+'``.
    """

    def __init__(self, code: str, precedence: int, func: typing.Callable,
                 arity: Side = Side.BOTH,
                 associativity: Side = Side.LEFT, cajole: Side = Side.BOTH, viewAs: str = None):
        """Create a new operator.

        :param code: The string that represents this operation. For
            instance, addition is '+' and greater than or equal to is
            '>='. Since the negative sign and minus operator would be
            identical in this respect, the sign's ``code`` differs and
            is 'm' instead. Similar with positive sign and 'p'.
        :param precedence: A higher number means greater precedence.
            Currently the numbers 1-8 are in use though maybe you can
            think of more.
        :param func: The function performed by this operation. It must
            take one or two arguments and return one result, with no
            side effects.
        :param arity: Which side(s) this operator draws operands from.
            For instance, '+' takes arguments on left and right, while
            '!' takes only one argument on its left.
        :param associativity: Which direction the associativity goes.
            Basically, when precedence is tied, should this be evaluated
            left to right or right to left. Exponentiation is the only
            common operation that does the latter.
        :param cajole: Which operand(s) should be collapsed into a
            single value before operation.
        :param viewAs: If the code is different than the actual
            operation string, fill viewAs with the real string.
        """
        self.code = code
        self.precedence = precedence
        self.function = func
        self.arity = arity
        self.associativity = associativity
        self.cajole = cajole
        self.viewAs = viewAs

    def __ge__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence >= other.precedence
        else:
            raise ArgumentTypeError('Other must be an operator or string')

    def __gt__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence > other.precedence
        else:
            raise ArgumentTypeError('Other must be an operator or string')

    def __le__(self, other):
        if isinstance(other, str):
            return True
        elif isinstance(other, Operator):
            return self.precedence <= other.precedence
        else:
            raise ArgumentTypeError('Other must be an operator or string')

    def __lt__(self, other):
        if isinstance(other, str):
            return True
        elif isinstance(other, Operator):
            return self.precedence < other.precedence
        else:
            raise ArgumentTypeError('Other must be an operator or string')

    def __eq__(self, other):
        if isinstance(other, Operator):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other
        return False

    def __repr__(self):
        return '{}:{}{} {}'.format(self.code,
                                   'l' if self.arity & Side.LEFT else '',
                                   'r' if self.arity & Side.RIGHT else '',
                                   self.precedence)

    def __str__(self):
        return self.viewAs or self.code

    def __call__(self, left, right):
        """Evaluate the function associated with this operator.

        Most operator functions are binary and will consume both
        ``left`` and ``right``. For unary operators the caller **must**
        pass in None to fill the unused operand slot. This may be
        changed in future to be cleverer.

        The ``cajole`` field of this object is used at this stage to
        collapse one or both operands into a single value. If one of the
        sides is targeted by the value of ``cajole``, and the
        corresponding operand is a ``Roll`` or other iterator, it will
        be replaced by its sum.

        :param left: The left operand. Usually an int or a Roll.
        :param right: The right operand. Even more likely to be an int.
        """
        if self.cajole & Side.LEFT:
            if isinstance(left, (Roll, tuple)):
                left = sum(left)
        if self.cajole & Side.RIGHT:
            if isinstance(right, (Roll, tuple)):
                right = sum(right)
        return self.function(*filter(lambda v: v is not None, [left, right]))


class Roll:
    """A set of rolls.

    This tracks the active rolls (those that are actually counted) as
    well as what die was rolled to get this and any discarded values.

    The active rolls are assumed by many of the associated functions to
    always be sorted ascending. To effect this, a Roll instance will
    automatically sort the active roll list every time there is an
    update to it. However, sometimes the index of a particular element
    does matter, like with the ``reroll_unconditional`` class of
    functions that repeatedly perform in-place replacements on those
    elements. Therefore you have the chance to temporarily disable
    sorting for the duration of these modifications.

    This object can be treated like a list in many ways, implementing
    get/set/delitem methods, len, and iter.
    """

    def __init__(self, rolls=None, die=0):
        """Create a new roll.

        :param rolls: The starting list of values to be used.
        :param die: The number of sides of the die that was rolled to
            get those values.
        """
        self.__disableSorting = False
        self.rolls = rolls or []  # type: typing.List[Number]
        self.die = die  # type: typing.Union[int, typing.Tuple[float, ...]]
        self.discards = []  # type: typing.List[Number]

    def __str__(self):
        rolls = ', '.join([str(item) for item in self.rolls])
        discards = ', '.join([str(item) for item in self.discards])
        formatstr = '[d{die}: {rolls}; ({discards})]' if discards else '[d{die}: {rolls}]'
        return formatstr.format(die=str(self.die), rolls=rolls, discards=discards)

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        return iter(self.rolls)

    def __len__(self):
        return len(self.rolls)

    def __getitem__(self, item):
        return self.rolls[item]

    def __setitem__(self, key, value):
        self.rolls[key] = value
        if not self.__disableSorting:
            self.rolls.sort()

    def __delitem__(self, key):
        del self.rolls[key]

    @property
    def rolls(self) -> typing.List[Number]:
        return self.__rolls

    @rolls.setter
    def rolls(self, val: typing.List[Number]):
        self.__rolls = val
        if not self.__disableSorting:
            self.__rolls.sort()

    @contextmanager
    def sorting_disabled(self):
        """Temporarily disable auto-sorting.

        This is a context manager, so is used with the ``with``
        statement. For example: ::

            with roll.sorting_disabled():
                while i < len(original):
                    while comp(roll[i], target):
                        roll.replace(i, single_die(roll.die))
                    i += 1

        The example is taken straight from ``reroll_unconditional`` below.
        """
        try:
            self.__disableSorting = True
            yield self
        finally:
            self.__disableSorting = False
            self.__rolls.sort()

    @wrap_exceptions_with(ArgumentValueError, 'Index out of bounds', IndexError)
    def discard(self, index: typing.Union[int, slice]):
        """Discard a roll or slice of rolls by index.

        :param index: The indexing object (int or slice) to select
            values to discard.
        :raises ArgumentTypeError: When something other than int or
            slice is used.
        """
        if isinstance(index, int):
            self.discards.append(self.rolls[index])
        elif isinstance(index, slice):
            self.discards.extend(self.rolls[index])
        else:
            raise ArgumentTypeError('You can only index with an int or a slice.')
        del self.rolls[index]

    @typing.overload
    def replace(self, index: int, new: Number) -> None:
        ...

    @typing.overload
    def replace(self, index: slice, new: typing.Iterable) -> None:
        ...

    @wrap_exceptions_with(ArgumentValueError, 'Index out of bounds', IndexError)
    def replace(self, index, new):
        """Discard a roll or slice of rolls and replace with new values.

        If you are discarding a slice, you must replace it with a
        sequence of equal length.

        :param index: An indexing object, an int or a slice.
        :param new: The new value or values to replace the old with.
        :raises ArgumentTypeError: When something other than int or
            slice is used for indexing.
        :raises ArgumentValueError: When the size of the replacement
            doesn't match the size of the slice.
        """
        if isinstance(index, int):
            self.discards.append(self.rolls[index])
        elif isinstance(index, slice):
            self.discards.extend(self.rolls[index])
            start, stop, step = index.indices(len(self.rolls))
            if stop - start != len(new):
                raise ArgumentValueError('You have to replace a slice with the same number of '
                                         'items.')
        else:
            raise ArgumentTypeError('You can only index with an int or a slice.')
        self.rolls[index] = new

    def copy(self) -> 'Roll':
        """Create a copy of this object to avoid mutating an original."""
        rv = Roll(deepcopy(self.rolls), self.die)
        # discards won't contain any mutable objects
        rv.discards = self.discards[:]
        return rv


@check_simple_types
def threshold_lower(roll: Roll, threshold: int) -> Roll:
    """Count the rolls that are equal to or above the given threshold.

    :param roll: The set of rolls.
    :param threshold: The number to compare against.
    :return: A list of ones and zeros that indicate which rolls met the
        threshold.
    """
    modified = Roll([1 if v >= threshold else 0 for v in roll], roll.die)
    modified.discards = roll.discards[:] + roll[:]
    return modified


@check_simple_types
def threshold_upper(roll: Roll, threshold: int) -> Roll:
    """Count the rolls that are equal to or below the given threshold.

    :param roll: The set of rolls.
    :param threshold: The number to compare against.
    :return: A list of ones and zeros that indicate which rolls met the
        threshold.
    """
    modified = Roll([1 if v <= threshold else 0 for v in roll], roll.die)
    modified.discards = roll.discards[:] + roll[:]
    return modified


@check_simple_types
def take_low(roll: Roll, number: int) -> Roll:
    """Preserve the lowest [number] rolls and discard the rest.

    This is used to implement disadvantage in D&D 5e.

    :param roll: The set of rolls.
    :param number: The number of rolls to take.
    :return: A roll with the lowest rolls preserved and the rest
        discarded.
    """
    copy = roll.copy()
    if len(copy) > number:
        n = len(copy) - number
        copy.discard(slice(-n, None))
    return copy


@check_simple_types
def take_high(roll: Roll, number: int) -> Roll:
    """Preserve the highest [number] rolls and discard the rest.

    This is used to implement advantage in D&D 5e.

    :param roll: The set of rolls.
    :param number: The number of rolls to take.
    :return: A roll with the highest rolls preserved and the rest
        discarded.
    """
    copy = roll.copy()
    if len(copy) > number:
        n = len(copy) - number
        copy.discard(slice(None, n))
    return copy


Sides = typing.Union[int, typing.Tuple[float, ...], Roll]


def roll_basic(number: int, sides: Sides) -> Roll:
    """Roll a single set of dice.

    :param number: The number of dice to be rolled.
    :param sides: Roll a ``sides``-sided die. Or, if given a collection
        of side values, pick one from there.
    :return: A ``Roll`` holding all the dice rolls.
    """
    return Roll([single_die(sides) for _ in range(number)], sides)


def single_die(sides: Sides) -> Number:
    """Roll a single die.

    The behavior is different based on what gets passed in. Given an
    int, it rolls a die with that many sides (precisely, it returns a
    random number between 1 and ``sides`` inclusive). Given a tuple,
    meaning the user specified a particular set of values for the sides
    of the die, it returns one of those values selected at random. Given
    a ``Roll``, which can happen in weird cases like 2d(1d4), it will
    take the sum of that roll and use it as the number of sides of a
    die.

    :param sides: The number of sides, or specific side values.
    :return: The random value that was rolled.
    """
    if isinstance(sides, int):
        return random.randint(1, sides)
    elif isinstance(sides, tuple):
        return random.choice(sides)
    elif isinstance(sides, Roll):
        # Yeah this can happen, see 2d(1d4)
        return random.randint(1, sum(sides))
    raise ArgumentTypeError("You can't roll a die with sides: {sides}".format(sides=sides))


def roll_critical(number: int, sides: Sides) -> Roll:
    """Roll double the normal number of dice."""
    rolls = [single_die(sides) for _ in range(2 * number)]
    return Roll(rolls, sides)


def roll_max(number: int, sides: Sides) -> Roll:
    """Roll a maximum value on every die."""
    if isinstance(sides, (tuple, Roll)):
        # For rolls, this does go by the highest value that got rolled
        # rather than that die's sides
        rolls = [max(sides)] * number
    elif isinstance(sides, (int, float)):
        rolls = [sides] * number
    else:
        raise ArgumentTypeError("roll_max can't be called with a {}-sided die", type(sides))
    return Roll(rolls, sides)


def roll_average(number: int, sides: Sides) -> Roll:
    """Roll an average value on every die.

    On most dice this will have a .5 in the result.
    """
    if isinstance(sides, (tuple, Roll)):
        rolls = [sum(sides) / len(sides)] * number
    elif isinstance(sides, int):
        rolls = [(sides + 1) / 2] * number
    else:
        raise ArgumentTypeError("roll_average can't be called with a {}-sided die", type(sides))
    return Roll(rolls, sides)


def reroll_once(original: Roll, target: Number,
                comp: typing.Callable[[Number, Number], bool]) -> Roll:
    """Take the roll and reroll values that meet the comparison, taking the new result.

    :param original: The set of rolls to inspect.
    :param target: The target to compare against.
    :param comp: The comparison function, that should return true if
        the value should be rerolled.
    :return: The roll after performing the rerolls.
    """
    modified = original.copy()
    i = 0
    with modified.sorting_disabled():
        while i < len(original):
            if comp(modified[i], target):
                modified.replace(i, single_die(modified.die))
            i += 1
    return modified


def reroll_unconditional(original: Roll, target: Number,
                         comp: typing.Callable[[Number, Number], bool]) -> Roll:
    """Reroll values that meet the comparison, and keep on rerolling until they don't.

    :param original: The set of rolls to inspect.
    :param target: The target to compare against.
    :param comp: The comparison function, that should return true if the
        value should be rerolled.
    :return: The roll after performing the rerolls.
    """
    modified = original.copy()
    i = 0
    with modified.sorting_disabled():
        while i < len(original):
            while comp(modified[i], target):
                modified.replace(i, single_die(modified.die))
            i += 1
    return modified


def reroll_once_on(original: Roll, target: Number) -> Roll:
    """Reroll and take the new result when a roll is equal to the given number."""
    return reroll_once(original, target, lambda x, y: x == y)


def reroll_once_higher(original: Roll, target: Number) -> Roll:
    """Reroll and take the new result when a roll is greater than the given number."""
    return reroll_once(original, target, lambda x, y: x > y)


def reroll_once_lower(original: Roll, target: Number) -> Roll:
    """Reroll and take the new result when a roll is less than the given number."""
    return reroll_once(original, target, lambda x, y: x < y)


def reroll_unconditional_on(original: Roll, target: Number) -> Roll:
    """Reroll and keep on rerolling when a roll is equal to the given number."""
    return reroll_unconditional(original, target, lambda x, y: x == y)


def reroll_unconditional_higher(original: Roll, target: Number) -> Roll:
    """Reroll and keep on rerolling when a roll is greater than the given number."""
    try:
        min_ = min(original.die)
    except TypeError:
        min_ = 1
    if target < min_:
        raise ArgumentValueError("A die with sides {die} can never be less than {target}. "
                                 "This would create an infinite loop.".format(die=original.die,
                                                                              target=target))
    return reroll_unconditional(original, target, lambda x, y: x > y)


def reroll_unconditional_lower(original: Roll, target: Number) -> Roll:
    """Reroll and keep on rerolling when a roll is less than the given number."""
    try:
        max_ = max(original.die)
    except TypeError:
        max_ = original.die
    if target > max_:
        raise ArgumentValueError("A die with sides {die} can never be greater than {target}. "
                                 "This would create an infinite loop.".format(die=original.die,
                                                                              target=target))
    return reroll_unconditional(original, target, lambda x, y: x < y)


def floor_val(original: Roll, bottom: Number) -> Roll:
    """Replace any rolls less than the given floor with that value.

    :param original: The set of rolls.
    :param bottom: The floor to truncate to.
    :return: The modified roll set.
    """
    modified = original.copy()
    i = 0
    with modified.sorting_disabled():
        while i < len(original):
            if modified[i] < bottom:
                modified.replace(i, bottom)
            i += 1
    return modified


def ceil_val(original: Roll, top: Number) -> Roll:
    """Replace any rolls greater than the given ceiling with that value.

    :param original: The set of rolls.
    :param top: The ceiling to truncate to.
    :return: The modified roll set.
    """
    modified = original.copy()
    i = 0
    with modified.sorting_disabled():
        while i < len(original):
            if modified[i] > top:
                modified.replace(i, top)
            i += 1
    return modified


@check_simple_types
def factorial(number: int) -> int:
    """Calculate the factorial of a number.

    :param number: The argument.
    :return: number!
    """
    if number < 0:
        raise ArgumentValueError("Factorial is undefined for negative numbers.")
    rv = 1
    for i in range(number):
        rv *= i + 1
    return rv


#: This contains all of the operators that are actually defined by this module.
#: It is a map between the codes used to represent the operators, and the actual
#: ``Operator`` instances that hold the functionality. Visually, it is sorted
#: in descending order of precedence. Obviously, as dictionaries are unsorted,
#: this doesn't actually matter.
OPERATORS = {
    '!': Operator('!', 8, factorial, arity=Side.LEFT, cajole=Side.LEFT),
    'd': Operator('d', 7, roll_basic, cajole=Side.LEFT),
    'da': Operator('da', 7, roll_average, cajole=Side.LEFT),
    'dc': Operator('dc', 7, roll_critical, cajole=Side.LEFT),
    'dm': Operator('dm', 7, roll_max, cajole=Side.LEFT),
    'h': Operator('h', 6, take_high, cajole=Side.RIGHT),
    'l': Operator('l', 6, take_low, cajole=Side.RIGHT),
    'f': Operator('f', 6, floor_val, cajole=Side.RIGHT),
    'c': Operator('c', 6, ceil_val, cajole=Side.RIGHT),
    'r': Operator('r', 6, reroll_once_on, cajole=Side.RIGHT),
    'R': Operator('R', 6, reroll_unconditional_on, cajole=Side.RIGHT),
    'r<': Operator('r<', 6, reroll_once_lower, cajole=Side.RIGHT),
    'R<': Operator('R<', 6, reroll_unconditional_lower, cajole=Side.RIGHT),
    'rl': Operator('rl', 6, reroll_once_lower, cajole=Side.RIGHT),
    'Rl': Operator('Rl', 6, reroll_unconditional_lower, cajole=Side.RIGHT),
    'r>': Operator('r>', 6, reroll_once_higher, cajole=Side.RIGHT),
    'R>': Operator('R>', 6, reroll_unconditional_higher, cajole=Side.RIGHT),
    'rh': Operator('rh', 6, reroll_once_higher, cajole=Side.RIGHT),
    'Rh': Operator('Rh', 6, reroll_unconditional_higher, cajole=Side.RIGHT),
    't': Operator('t', 6, threshold_lower, cajole=Side.RIGHT),
    'T': Operator('T', 6, threshold_upper, cajole=Side.RIGHT),
    '^': Operator('^', 5, lambda x, y: x ** y, associativity=Side.RIGHT),
    'm': Operator('m', 4, lambda x: -x, arity=Side.RIGHT, cajole=Side.RIGHT, viewAs='-'),
    'p': Operator('p', 4, lambda x: x, arity=Side.RIGHT, cajole=Side.RIGHT, viewAs='+'),
    '*': Operator('*', 3, lambda x, y: x * y),
    '/': Operator('/', 3, lambda x, y: x / y),
    '%': Operator('%', 3, lambda x, y: x % y),
    '-': Operator('-', 2, lambda x, y: x - y),
    '+': Operator('+', 2, lambda x, y: x + y),
    '>': Operator('>', 1, lambda x, y: x > y),
    'gt': Operator('gt', 1, lambda x, y: x > y),
    '>=': Operator('>=', 1, lambda x, y: x >= y),
    'ge': Operator('ge', 1, lambda x, y: x >= y),
    '<': Operator('<', 1, lambda x, y: x < y),
    'lt': Operator('lt', 1, lambda x, y: x < y),
    '<=': Operator('<=', 1, lambda x, y: x <= y),
    'le': Operator('le', 1, lambda x, y: x <= y),
    '=': Operator('=', 1, lambda x, y: x == y),
    '|': Operator('|', 1, lambda x, y: x or y),
    '&': Operator('&', 1, lambda x, y: x and y),
}
