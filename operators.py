import copy
import enum
import random
import typing

from exceptions import ArgumentTypeError, ArgumentValueError
from helpers import check_simple_types, wrap_exceptions_with

Number = typing.Union[int, float]


class Side(enum.IntFlag):
    """Represents which side an operation is applicable to.

    Note that checking if an operation includes one side is as simple as checking
    `Operator.arity & Side.LEFT` or `Operator.arity & Side.RIGHT`,
    whichever one you want
    """
    RIGHT = 0b01
    LEFT = 0b10
    BOTH = 0b11
    NEITHER = 0b00


class Operator:
    """An operator like + or d that can be applied to values."""

    def __init__(self, code: str, precedence: int, func: typing.Callable, arity: Side = Side.BOTH,
                 associativity: Side = Side.LEFT, cajole: Side = Side.BOTH, viewAs: str = None):
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
        return '{}:{} {}'.format(self.code, self.arity, self.precedence)

    def __str__(self):
        return self.viewAs or self.code

    def __call__(self, left, right):
        if self.cajole & Side.LEFT:
            if isinstance(left, (Roll, tuple)):
                left = sum(left)
        if self.cajole & Side.RIGHT:
            if isinstance(right, (Roll, tuple)):
                right = sum(right)
        return self.function(*filter(lambda v: v is not None, [left, right]))


class Roll:
    """A set of rolls."""

    def __init__(self, rolls=None, die=0):
        # TODO: make rolls a property that is always sorted at set time
        self.rolls: typing.List[Number] = rolls or []
        self.die: typing.Union[int, typing.Tuple[float, ...]] = die
        self.discards = []

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

    def __delitem__(self, key):
        del self.rolls[key]

    def append(self, obj):
        self.rolls.append(obj)

    def extend(self, iterable):
        self.rolls.extend(iterable)

    def sort(self):
        self.rolls.sort()

    # TODO: move to using Roll.discard & Roll.replace instead of manually doing it in the op functions
    @wrap_exceptions_with(ArgumentValueError, 'Index out of bounds', IndexError)
    def discard(self, index: typing.Union[int, slice]):
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
        if isinstance(index, int):
            self.discards.append(self.rolls[index])
        elif isinstance(index, slice):
            self.discards.extend(self.rolls[index])
            start, stop, step = index.indices(len(self.rolls))
            if stop - start != len(new):
                raise ArgumentValueError('You have to replace a slice with the same number of items.')
        else:
            raise ArgumentTypeError('You can only index with an int or a slice.')
        self.rolls[index] = new

    # TODO: move to using copy and keeping the roll immutable
    # try renaming the internal fields and fix broken parts
    def copy(self) -> 'Roll':
        rv = Roll(copy.deepcopy(self.rolls), self.die)
        # discards won't contain any mutable objects
        rv.discards = self.discards[:]
        return rv


@check_simple_types
def threshold_lower(roll: Roll, threshold: int) -> Roll:
    """Count the number of rolls that are equal to or above the given threshold.

    :param roll: The set of rolls.
    :param threshold: The number to compare against.
    :return: A list of ones and zeros that indicate which rolls met the threshold.
    """
    modified = Roll([1 if v >= threshold else 0 for v in roll], roll.die)
    modified.discards = roll.discards[:] + roll[:]
    return modified


@check_simple_types
def threshold_upper(roll: Roll, threshold: int) -> Roll:
    """Count the number of rolls that are equal to or below the given threshold.

    :param roll: The set of rolls.
    :param threshold: The number to compare against.
    :return: A list of ones and zeros that indicate which rolls met the threshold.
    """
    modified = Roll([1 if v <= threshold else 0 for v in roll], roll.die)
    modified.discards = roll.discards[:] + roll[:]
    return modified


@check_simple_types
def take_low(roll: Roll, number: int) -> Roll:
    """Preserve the lowest [number] rolls and discard the rest. Used to implement disadvantage in D&D 5e.

    :param roll: The set of rolls.
    :param number: The number of rolls to take.
    :return: A roll with the lowest rolls preserved and the rest discarded.
    """
    if len(roll) > number:
        n = len(roll) - number
        roll.discards.extend(roll[-n:])
        del roll[-n:]
    return roll


@check_simple_types
def take_high(roll: Roll, number: int) -> Roll:
    """Preserve the highest [number] rolls and discard the rest. Used to implement advantage in D&D 5e.

    :param roll: The set of rolls.
    :param number: The number of rolls to take.
    :return: A roll with the highest rolls preserved and the rest discarded.
    """
    if len(roll) > number:
        n = len(roll) - number
        roll.discards.extend(roll[:n])
        del roll[:n]
    return roll


def roll_basic(number: int, sides: typing.Union[int, typing.Tuple[float, ...], Roll]) -> Roll:
    """Roll a single set of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    for all in range(number):
        result.append(single_die(sides))
    result.sort()
    return result


def single_die(sides: typing.Union[int, typing.Tuple[float, ...], Roll]) -> Number:
    """Roll a single die."""
    # TODO: isinstance
    if type(sides) is int:
        return random.randint(1, sides)
    elif type(sides) is tuple:
        return random.choice(sides)
    elif type(sides) is Roll:
        # Yeah this can happen, see 2d(1d4)
        return random.randint(1, sum(sides))
    raise ArgumentTypeError("You can't roll a die with sides: {sides}".format(sides=sides))


def roll_critical(number: int, sides: typing.Union[int, typing.Tuple[float, ...], Roll]) -> Roll:
    """Roll double the normal number of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    for all in range(2 * number):
        result.append(single_die(sides))
    result.sort()
    return result


def roll_max(number: int, sides: typing.Union[int, typing.Tuple[float, ...], Roll]) -> Roll:
    """Roll double the normal number of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    if isinstance(sides, (tuple, Roll)):
        # For rolls, this does go by the highest value that got rolled rather than that die's sides
        result.extend([max(sides)] * number)
    elif isinstance(sides, (int, float)):
        result.extend([sides] * number)
    else:
        raise ArgumentTypeError("roll_max can't be called with a {}-sided die", type(sides))
    return result


def roll_average(number: int, sides: typing.Union[int, typing.Tuple[float, ...], Roll]) -> Roll:
    val = Roll()
    val.die = sides
    if isinstance(sides, (tuple, Roll)):
        val.extend([sum(sides) / len(sides)] * number)
    elif isinstance(sides, int):
        val.extend([(sides + 1) / 2] * number)
    else:
        raise ArgumentTypeError("roll_average can't be called with a {}-sided die", type(sides))
    return val


def reroll_once(original: Roll, target: Number, comp: typing.Callable[[Number, Number], bool]) -> Roll:
    """Take the roll and reroll values that meet the comparison, taking the new result.

    :param original: The set of rolls to inspect.
    :param target: The target to compare against.
    :param comp: The comparison function, that should return true if the value should be rerolled.
    :return: The roll after performing the rerolls.
    """
    modified = original.copy()
    i = 0
    while i < len(original):
        if comp(modified[i], target):
            modified.discards.append(modified[i])
            modified[i] = single_die(modified.die)
        i += 1
    modified.sort()
    return modified


def reroll_unconditional(original: Roll, target: Number, comp: typing.Callable[[Number, Number], bool]):
    """Take the roll and reroll values that meet the comparison, and keep on rerolling until they don't.

    :param original: The set of rolls to inspect.
    :param target: The target to compare against.
    :param comp: The comparison function, that should return true if the value should be rerolled.
    :return: The roll after performing the rerolls.
    """
    modified = original.copy()
    i = 0
    while i < len(original):
        while comp(modified[i], target):
            modified.discards.append(modified[i])
            modified[i] = single_die(modified.die)
        i += 1
    modified.sort()
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
    return reroll_unconditional(original, target, lambda x, y: x > y)


def reroll_unconditional_lower(original: Roll, target: Number) -> Roll:
    """Reroll and keep on rerolling when a roll is less than the given number."""
    return reroll_unconditional(original, target, lambda x, y: x < y)


def floor_val(original: Roll, bottom: Number) -> Roll:
    """Replace any rolls less than the given floor with that floor value.

    :param original: The set of rolls.
    :param bottom: The floor to truncate to.
    :return: The modified roll set.
    """
    modified = original.copy()
    i = 0
    while i < len(original):
        if modified[i] < bottom:
            modified.discards.append(modified[i])
            modified[i] = bottom
        i += 1
    modified.sort()
    return modified


def ceil_val(original: Roll, top: Number) -> Roll:
    """Replace any rolls greater than the given ceiling with that ceiling value.

    :param original: The set of rolls.
    :param top: The ceiling to truncate to.
    :return: The modified roll set.
    """
    modified = original.copy()
    i = 0
    while i < len(original):
        if modified[i] > top:
            modified.discards.append(modified[i])
            modified[i] = top
        i += 1
    modified.sort()
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
