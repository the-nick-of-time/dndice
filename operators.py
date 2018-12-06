import random


class Arity:
    LEFT = 0b01
    RIGHT = 0b10
    BOTH = 0b11
    NEITHER = 0b00


class Operator:
    def __init__(self, code: str, precedence: int, func: callable, arity: int = Arity.BOTH,
                 associativity: int = Arity.LEFT, cajole: int = Arity.BOTH):
        self.code = code
        self.precedence = precedence
        self.function = func
        self.arity = arity
        self.associativity = associativity
        self.cajole = cajole

    def __ge__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence >= other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __gt__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence > other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __le__(self, other):
        if isinstance(other, str):
            return True
        elif isinstance(other, Operator):
            return self.precedence <= other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __lt__(self, other):
        if isinstance(other, str):
            return False
        elif isinstance(other, Operator):
            return self.precedence < other.precedence
        else:
            raise TypeError('Other must be an operator or string')

    def __eq__(self, other):
        if isinstance(other, Operator):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other
        return False

    def __repr__(self):
        return '{}:{} {}'.format(self.code, self.arity, self.precedence)

    def __str__(self):
        return self.code

    def __call__(self, left, right):
        if self.cajole & Arity.LEFT:
            try:
                left = sum(left)
            except TypeError:
                pass
        if self.cajole & Arity.RIGHT:
            try:
                right = sum(right)
            except TypeError:
                pass
        return self.function(*filter(lambda v: v is not None, [left, right]))


class Roll(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.die = 0
        self.discards = []

    def __str__(self):
        rolls = ', '.join([str(item) for item in self])
        discards = ', '.join([str(item) for item in self.discards])
        formatstr = '[d{die}: {rolls}; ({discards})]' if discards else '[d{die}: {rolls}]'
        return formatstr.format(die=str(self.die), rolls=rolls, discards=discards)

    def __repr__(self):
        return self.__str__()


def threshold_lower(left: Roll, right: int):
    return [1 if v > right else 0 for v in left]


def threshold_upper(left: Roll, right: int):
    return [1 if v < right else 0 for v in left]


def take_low(roll, number):
    if len(roll) > number:
        n = len(roll) - number
        roll.discards.extend(roll[-n:])
        del roll[-n:]
    return roll


def take_high(roll, number):
    if len(roll) > number:
        n = len(roll) - number
        roll.discards.extend(roll[:n])
        del roll[:n]
    return roll


def roll_basic(number, sides):
    """Roll a single set of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    # result.discards = [[] for all in range(number)]
    for all in range(number):
        result.append(single_die(sides))
    result.sort()
    return result


def single_die(sides):
    """Roll a single die."""
    if type(sides) is int:
        return random.randint(1, sides)
    elif type(sides) is list:
        return sides[random.randint(0, len(sides) - 1)]


def roll_critical(number, sides):
    """Roll double the normal number of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    # result.discards = [[] for all in range(number)]
    for all in range(2 * number):
        result.append(single_die(sides))
    result.sort()
    return result


def roll_max(number, sides):
    """Roll double the normal number of dice."""
    # Returns a sorted (ascending) list of all the numbers rolled
    result = Roll()
    result.die = sides
    # result.discards = [[] for all in range(number)]
    if isinstance(sides, list):
        result.extend([max(sides)] * number)
    else:
        result.extend([sides] * number)
    return result


def roll_average(number, sides):
    val = Roll()
    val.die = sides
    # val.discards = [[] for all in range(number)]
    if isinstance(sides, list):
        val.extend([sum(sides) / len(sides)] * number)
        # return (sum(sides) * number) / len(sides)
    else:
        val.extend([(sides + 1) / 2] * number)
        # return (1 + sides) * number / 2
    return val


def reroll_once(original, target, comp):
    modified = original
    i = 0
    while i < len(original):
        if comp(modified[i], target):
            modified.discards.append(modified[i])
            modified[i] = single_die(modified.die)
        i += 1
    modified.sort()
    return modified


def reroll_unconditional(original, target, comp):
    modified = original
    i = 0
    while i < len(original):
        while comp(modified[i], target):
            modified.discards.append(modified[i])
            modified[i] = single_die(modified.die)
        i += 1
    modified.sort()
    return modified


def reroll_once_on(original, target):
    return reroll_once(original, target, lambda x, y: x == y)


def reroll_once_higher(original, target):
    return reroll_once(original, target, lambda x, y: x > y)


def reroll_once_lower(original, target):
    return reroll_once(original, target, lambda x, y: x < y)


def reroll_unconditional_on(original, target):
    return reroll_unconditional(original, target, lambda x, y: x == y)


def reroll_unconditional_higher(original, target):
    return reroll_unconditional(original, target, lambda x, y: x > y)


def reroll_unconditional_lower(original, target):
    return reroll_unconditional(original, target, lambda x, y: x < y)


def floor_val(original, bottom):
    modified = original
    i = 0
    while i < len(original):
        if modified[i] < bottom:
            modified.discards.append(modified[i])
            modified[i] = bottom
        i += 1
    modified.sort()
    return modified


def ceil_val(original, top):
    modified = original
    i = 0
    while i < len(original):
        if modified[i] > top:
            modified.discards.append(modified[i])
            modified[i] = top
        i += 1
    modified.sort()
    return modified


def factorial(number):
    rv = 1
    for i in range(number):
        rv *= i + 1
    return rv


operators = {
    'd': Operator('d', 7, roll_basic, cajole=Arity.LEFT),
    'da': Operator('da', 7, roll_average, cajole=Arity.LEFT),
    'dc': Operator('dc', 7, roll_critical, cajole=Arity.LEFT),
    'dm': Operator('dm', 7, roll_max, cajole=Arity.LEFT),
    'h': Operator('h', 6, take_high, cajole=Arity.RIGHT),
    'l': Operator('l', 6, take_low, cajole=Arity.RIGHT),
    'f': Operator('f', 6, floor_val, cajole=Arity.RIGHT),
    'c': Operator('c', 6, ceil_val, cajole=Arity.RIGHT),
    'r': Operator('r', 6, reroll_once_on, cajole=Arity.RIGHT),
    'R': Operator('R', 6, reroll_unconditional_on, cajole=Arity.RIGHT),
    'r<': Operator('r<', 6, reroll_once_lower, cajole=Arity.RIGHT),
    'R<': Operator('R<', 6, reroll_unconditional_lower, cajole=Arity.RIGHT),
    'rl': Operator('rl', 6, reroll_once_lower, cajole=Arity.RIGHT),
    'Rl': Operator('Rl', 6, reroll_unconditional_lower, cajole=Arity.RIGHT),
    'r>': Operator('r>', 6, reroll_once_higher, cajole=Arity.RIGHT),
    'R>': Operator('R>', 6, reroll_unconditional_higher, cajole=Arity.RIGHT),
    'rh': Operator('rh', 6, reroll_once_higher, cajole=Arity.RIGHT),
    'Rh': Operator('Rh', 6, reroll_unconditional_higher, cajole=Arity.RIGHT),
    't': Operator('t', 6, threshold_lower, cajole=Arity.RIGHT),
    'T': Operator('T', 6, threshold_upper, cajole=Arity.RIGHT),
    '^': Operator('^', 5, lambda x, y: x ** y, associativity=Arity.RIGHT),
    'm': Operator('m', 4, lambda x: -x, arity=Arity.RIGHT, cajole=Arity.RIGHT),
    'p': Operator('p', 4, lambda x: x, arity=Arity.RIGHT, cajole=Arity.RIGHT),
    '!': Operator('!', 3, factorial, arity=Arity.LEFT, cajole=Arity.LEFT),
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
