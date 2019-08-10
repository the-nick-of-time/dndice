import enum
import random
import typing

from exceptions import ArgumentTypeError
from helpers import check_simple_types

Number = typing.Union[int, float]


class Side(enum.Flag):
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

    def __init__(self, code: str, precedence: int, func: callable, arity: Side = Side.BOTH,
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
            if isinstance(left, Roll):
                left = left.sum()
        if self.cajole & Side.RIGHT:
            if isinstance(right, Roll):
                right = right.sum()
        return self.function(*filter(lambda v: v is not None, [left, right]))


class Roll:
    """A set of rolls."""

    def __init__(self, rolls=None):
        self.rolls = rolls or []
        self.die = 0
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

    def sum(self):
        return sum(self.rolls)

    def copy(self) -> 'Roll':
        rv = Roll(self.rolls[:])
        rv.die = self.die
        rv.discards = self.discards[:]
        return rv


@check_simple_types
def threshold_lower(roll: Roll, threshold: int) -> Roll:
    """Count the number of rolls that are equal to or above the given threshold.

    :param roll: The set of rolls.
    :param threshold: The number to compare against.
    :return: A list of ones and zeros that indicate which rolls met the threshold.
    """
    modified = Roll([1 if v >= threshold else 0 for v in roll])
    modified.die = roll.die
    modified.discards = roll.discards[:] + roll[:]
    return modified


@check_simple_types
def threshold_upper(roll: Roll, threshold: int) -> Roll:
    """Count the number of rolls that are equal to or below the given threshold.

    :param roll: The set of rolls.
    :param threshold: The number to compare against.
    :return: A list of ones and zeros that indicate which rolls met the threshold.
    """
    modified = Roll([1 if v <= threshold else 0 for v in roll])
    modified.die = roll.die
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


def roll_basic(number: int, sides: typing.Union[int, typing.List[float]]) -> Roll:
    """Roll a single set of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    for all in range(number):
        result.append(single_die(sides))
    result.sort()
    return result


def single_die(sides: typing.Union[int, typing.List[float]]) -> typing.Union[int, float]:
    """Roll a single die."""
    if type(sides) is int:
        return random.randint(1, sides)
    elif type(sides) is list:
        return random.choice(sides)


def roll_critical(number: int, sides: typing.Union[int, typing.List[float]]) -> Roll:
    """Roll double the normal number of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    for all in range(2 * number):
        result.append(single_die(sides))
    result.sort()
    return result


def roll_max(number: int, sides: typing.Union[int, typing.List[float]]) -> Roll:
    """Roll double the normal number of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    if isinstance(sides, list):
        result.extend([max(sides)] * number)
    else:
        result.extend([sides] * number)
    return result


def roll_average(number: int, sides: typing.Union[int, typing.List[float]]) -> Roll:
    val = Roll()
    val.die = sides
    if isinstance(sides, list):
        val.extend([sum(sides) / len(sides)] * number)
    else:
        val.extend([(sides + 1) / 2] * number)
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


def factorial(number: Number) -> Number:
    """Calculate the factorial of a number.

    :param number: The argument.
    :return: number!
    """
    rv = 1
    for i in range(number):
        rv *= i + 1
    return rv


operators = {
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
    'm': Operator('m', 4, lambda x: -x, arity=Side.RIGHT, cajole=Side.RIGHT),
    'p': Operator('p', 4, lambda x: x, arity=Side.RIGHT, cajole=Side.RIGHT),
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
