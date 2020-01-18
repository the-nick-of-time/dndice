import unittest
from unittest import mock

from dndice.lib import exceptions, operators


class TestOperator(unittest.TestCase):

    @staticmethod
    def echo(x, y):
        return x, y

    @staticmethod
    def echo_one(x):
        return x

    def test_sorting(self):
        highPrecedence = operators.Operator('^', 10, TestOperator.echo)
        lowPrecedence = operators.Operator('=', 1, TestOperator.echo)
        otherLowPrecedence = operators.Operator('|', 1, TestOperator.echo)
        self.assertGreater(highPrecedence, lowPrecedence)
        self.assertGreaterEqual(highPrecedence, lowPrecedence)
        self.assertLess(lowPrecedence, highPrecedence)
        self.assertLessEqual(lowPrecedence, highPrecedence)
        self.assertGreaterEqual(lowPrecedence, otherLowPrecedence)
        self.assertLessEqual(lowPrecedence, otherLowPrecedence)
        nonOperator = '('
        self.assertLess(highPrecedence, nonOperator)
        self.assertLessEqual(highPrecedence, nonOperator)
        self.assertFalse(highPrecedence > nonOperator)
        self.assertFalse(highPrecedence >= nonOperator)
        other = 5
        with self.assertRaises(exceptions.ArgumentTypeError):
            highPrecedence < other
        with self.assertRaises(exceptions.ArgumentTypeError):
            highPrecedence <= other
        with self.assertRaises(exceptions.ArgumentTypeError):
            highPrecedence > other
        with self.assertRaises(exceptions.ArgumentTypeError):
            highPrecedence >= other

    def test_equals(self):
        plus = operators.Operator('+', 2, lambda x, y: x + y)
        positive = operators.Operator('p', 4, lambda x: x, arity=operators.Side.RIGHT,
                                      cajole=operators.Side.RIGHT, viewAs='+')
        self.assertNotEqual(plus, positive)
        self.assertEqual(plus, '+')
        self.assertEqual(plus, plus)
        self.assertNotEqual(plus, 2)

    def test_cajole(self):
        cajoleRight = operators.Operator('h', 0, TestOperator.echo, cajole=operators.Side.RIGHT)
        cajoleLeft = operators.Operator('d', 0, TestOperator.echo, cajole=operators.Side.LEFT)
        cajoleBoth = operators.Operator('=', 1, TestOperator.echo)
        bothOperands = ((1, 2, 3), (4, 5, 6))
        self.assertEqual(cajoleBoth(*bothOperands), (6, 15))
        self.assertEqual(cajoleLeft(*bothOperands), (6, (4, 5, 6)))
        self.assertEqual(cajoleRight(*bothOperands), ((1, 2, 3), 15))

    def test_arity(self):
        arityLeft = operators.Operator('!', 8, TestOperator.echo_one, arity=operators.Side.LEFT,
                                       cajole=operators.Side.NEITHER)
        arityRight = operators.Operator('m', 4, TestOperator.echo_one,
                                        arity=operators.Side.RIGHT,
                                        cajole=operators.Side.NEITHER)
        arityBoth = operators.Operator('+', 2, TestOperator.echo, cajole=operators.Side.NEITHER)
        bothOperands = ((1, 2, 3), (4, 5, 6))
        # The decision to pass in None for unnecessary arguments is made at the higher level
        leftOperand = ((1, 2, 3), None)
        rightOperand = (None, (4, 5, 6))
        self.assertEqual(arityBoth(*bothOperands), ((1, 2, 3), (4, 5, 6)))
        self.assertEqual(arityLeft(*leftOperand), (1, 2, 3))
        self.assertEqual(arityRight(*rightOperand), (4, 5, 6))


class TestRoll(unittest.TestCase):

    def setUp(self) -> None:
        self.roll = operators.Roll([1, 2, 3], 4)

    def test_construction(self):
        single = operators.Roll([1], 5)
        self.assertEqual(single.rolls, [1])
        self.assertEqual(single.die, 5)
        self.assertEqual(single.discards, [])

    def test_len(self):
        none = operators.Roll([], 2)
        self.assertEqual(len(none), 0)
        one = operators.Roll([1], 5)
        self.assertEqual(len(one), 1)
        long = operators.Roll([3] * 10, 6)
        self.assertEqual(len(long), 10)

    def test_get(self):
        self.assertEqual(self.roll[0], 1)
        self.assertEqual(self.roll[2], 3)
        self.assertRaises(IndexError, lambda: self.roll[3])

    def test_set(self):
        self.roll[2] = 10
        self.assertEqual(self.roll[2], 10)
        with self.assertRaises(IndexError):
            self.roll[3] = 3

    def test_del(self):
        del self.roll[0]
        self.assertEqual(self.roll.rolls, [2, 3])

    def test_discard(self):
        self.roll.discard(1)
        self.assertEqual(self.roll.rolls, [1, 3])
        self.assertEqual(self.roll.discards, [2])
        slicyboi = operators.Roll([1, 2, 3, 4, 5, 6, 7, 8], 10)
        slicyboi.discard(slice(0, 3))
        self.assertEqual(slicyboi.rolls, [4, 5, 6, 7, 8])
        self.assertEqual(slicyboi.discards, [1, 2, 3])
        testy = operators.Roll([1, 2, 3], 6)
        with self.assertRaises(exceptions.ArgumentValueError):
            testy.discard(10)
        with self.assertRaises(exceptions.ArgumentTypeError):
            testy.discard('string')

    def test_replace(self):
        self.roll.replace(2, 5)
        self.assertEqual(self.roll.rolls, [1, 2, 5])
        self.assertEqual(self.roll.discards, [3])
        slicyboi = operators.Roll([1, 2, 3, 4, 5, 6, 7, 8], 10)
        slicyboi.replace(slice(5, len(slicyboi)), [20, 21, 22])
        self.assertEqual(slicyboi.rolls, [1, 2, 3, 4, 5, 20, 21, 22])
        self.assertEqual(slicyboi.discards, [6, 7, 8])
        with self.assertRaises(exceptions.ArgumentValueError):
            slicyboi.replace(slice(0, 3), [1, 2])
        with self.assertRaises(exceptions.ArgumentTypeError):
            slicyboi.replace('abc', [2, 3])

    def test_copy(self):
        copy = self.roll.copy()
        self.assertEqual(self.roll.rolls, copy.rolls)
        self.assertEqual(self.roll.discards, copy.discards)
        self.assertEqual(self.roll.die, copy.die)
        copy.discard(0)
        self.assertNotEqual(self.roll.rolls, copy.rolls)
        self.assertNotEqual(self.roll.discards, copy.discards)


class TestDeterministicFunctions(unittest.TestCase):

    def setUp(self) -> None:
        self.roll = operators.Roll([1, 2, 3, 4, 5, 6], 6)

    def test_threshold_lower(self):
        result = operators.threshold_lower(self.roll, 5)
        self.assertEqual(result.rolls, [0, 0, 0, 0, 1, 1])
        self.assertEqual(result.discards, [1, 2, 3, 4, 5, 6])
        self.assertEqual(result.die, self.roll.die)

    def test_threshold_upper(self):
        result = operators.threshold_upper(self.roll, 2)
        self.assertEqual(result.rolls, [0, 0, 0, 0, 1, 1])
        self.assertEqual(result.discards, [1, 2, 3, 4, 5, 6])
        self.assertEqual(result.die, self.roll.die)

    def test_take_low(self):
        result = operators.take_low(self.roll, 2)
        self.assertEqual(result.rolls, [1, 2])
        self.assertEqual(result.discards, [3, 4, 5, 6])

    def test_take_high(self):
        result = operators.take_high(self.roll, 2)
        self.assertEqual(result.rolls, [5, 6])
        self.assertEqual(result.discards, [1, 2, 3, 4])

    def test_floor_val(self):
        result = operators.floor_val(self.roll, 3)
        self.assertEqual(result.rolls, [3, 3, 3, 4, 5, 6])
        self.assertEqual(result.discards, [1, 2])

    def test_ceil_val(self):
        result = operators.ceil_val(self.roll, 3)
        self.assertEqual(result.rolls, [1, 2, 3, 3, 3, 3])
        self.assertEqual(result.discards, [4, 5, 6])

    def test_factorial(self):
        self.assertEqual(operators.factorial(0), 1)
        self.assertEqual(operators.factorial(1), 1)
        self.assertEqual(operators.factorial(5), 120)
        with self.assertRaises(exceptions.ArgumentValueError):
            operators.factorial(-1)


class TestRollFunctions(unittest.TestCase):

    def setUp(self) -> None:
        i = -1
        rands = [4, 4, 4, 4, 4, 10, 10, 10, 10, 1, 1, 1]

        def randint(start, end):
            nonlocal i
            i += 1
            return rands[i]

        patcher = mock.patch('dndice.lib.operators.random')
        self.addCleanup(patcher.stop)
        self.randomMocker = patcher.start()
        self.randomMocker.randint = randint
        self.randomMocker.choice = lambda iterable: 1190
        self.roll = operators.Roll([1, 2, 3, 4, 5, 6], 6)

    def test_basic_roll(self):
        result = operators.roll_basic(2, 6)
        self.assertEqual(result.rolls, [4, 4])
        self.assertEqual(result.die, 6)
        self.assertEqual(result.discards, [])
        result = operators.roll_basic(2, (1, 2, 3))
        self.assertEqual(result.rolls, [1190, 1190])
        self.assertEqual(result.die, (1, 2, 3))
        self.assertEqual(result.discards, [])
        with self.assertRaises(exceptions.ArgumentTypeError):
            operators.roll_basic(2, 'abc')

    def test_roll_critical(self):
        result = operators.roll_critical(2, 6)
        self.assertEqual(result.rolls, [4, 4, 4, 4])
        self.assertEqual(result.die, 6)
        result = operators.roll_critical(2, (1, 2, 3))
        self.assertEqual(result.rolls, [1190, 1190, 1190, 1190])
        self.assertEqual(result.die, (1, 2, 3))
        with self.assertRaises(exceptions.ArgumentTypeError):
            operators.roll_critical(2, 'abc')

    def test_roll_max(self):
        # actually deterministic anyway
        result = operators.roll_max(2, 6)
        self.assertEqual(result.rolls, [6, 6])
        self.assertEqual(result.die, 6)
        result = operators.roll_max(2, (1, 2, 3))
        self.assertEqual(result.rolls, [3, 3])
        self.assertEqual(result.die, (1, 2, 3))
        with self.assertRaises(exceptions.ArgumentTypeError):
            operators.roll_max(2, 'abc')

    def test_roll_average(self):
        # actually deterministic anyway
        result = operators.roll_average(2, 6)
        self.assertEqual(result.rolls, [3.5, 3.5])
        self.assertEqual(result.die, 6)
        result = operators.roll_average(2, (1, 1, 3, 5, 10))
        self.assertEqual(result.rolls, [4., 4.])
        self.assertEqual(result.die, (1, 1, 3, 5, 10))
        with self.assertRaises(exceptions.ArgumentTypeError):
            operators.roll_average(2, 'abc')

    def test_reroll_once_on(self):
        result = operators.reroll_once_on(self.roll, 2)
        self.assertEqual(result.rolls, [1, 3, 4, 4, 5, 6])
        self.assertEqual(result.discards, [2])

    def test_reroll_once_higher(self):
        result = operators.reroll_once_higher(self.roll, 2)
        self.assertEqual(result.rolls, [1, 2, 4, 4, 4, 4])
        self.assertEqual(result.discards, [3, 4, 5, 6])

    def test_reroll_once_lower(self):
        result = operators.reroll_once_lower(self.roll, 3)
        self.assertEqual(result.rolls, [3, 4, 4, 4, 5, 6])
        self.assertEqual(result.discards, [1, 2])

    def test_reroll_unconditional_on(self):
        result = operators.reroll_unconditional_on(self.roll, 4)
        self.assertEqual(result.rolls, [1, 2, 3, 5, 6, 10])
        self.assertEqual(result.discards, [4, 4, 4, 4, 4, 4])

    def test_reroll_unconditional_higher(self):
        result = operators.reroll_unconditional_higher(self.roll, 3)
        self.assertEqual(result.rolls, [1, 1, 1, 1, 2, 3])
        self.assertEqual(result.discards, [4, 4, 4, 4, 4, 4, 10, 10, 10, 10, 5, 6])
        with self.assertRaises(exceptions.ArgumentValueError):
            operators.reroll_unconditional_higher(self.roll, 0)

    def test_reroll_unconditional_lower(self):
        result = operators.reroll_unconditional_lower(self.roll, 5)
        self.assertEqual(result.rolls, [5, 6, 10, 10, 10, 10])
        self.assertEqual(result.discards, [1, 4, 4, 4, 4, 4, 2, 3, 4])
        with self.assertRaises(exceptions.ArgumentValueError):
            operators.reroll_unconditional_lower(self.roll, 7)


if __name__ == '__main__':
    unittest.main()
