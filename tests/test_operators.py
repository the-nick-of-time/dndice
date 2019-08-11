import unittest
from unittest import mock

import exceptions
import operators


class TestOperator(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass


class TestRoll(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass


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
        self.assertEqual(result.rolls, [1, 1, 0, 0, 0, 0])
        self.assertEqual(result.discards, [1, 2, 3, 4, 5, 6])
        self.assertEqual(result.die, self.roll.die)

    def test_take_low(self):
        # the current implementation mutates the input
        result = operators.take_low(self.roll, 2)
        self.assertEqual(result.rolls, [1, 2])
        self.assertEqual(result.discards, [3, 4, 5, 6])

    def test_take_high(self):
        # the current implementation mutates the input
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
        patcher = mock.patch('operators.random')
        self.addCleanup(patcher.stop)
        self.randomMocker = patcher.start()
        # The most random number (https://xkcd.com/221/)
        self.randomMocker.randint = lambda start, end: 4
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

    def test_roll_critical(self):
        result = operators.roll_critical(2, 6)
        self.assertEqual(result.rolls, [4, 4, 4, 4])
        self.assertEqual(result.die, 6)
        result = operators.roll_critical(2, (1, 2, 3))
        self.assertEqual(result.rolls, [1190, 1190, 1190, 1190])
        self.assertEqual(result.die, (1, 2, 3))

    def test_roll_max(self):
        # actually deterministic anyway
        result = operators.roll_max(2, 6)
        self.assertEqual(result.rolls, [6, 6])
        self.assertEqual(result.die, 6)
        result = operators.roll_max(2, (1, 2, 3))
        self.assertEqual(result.rolls, [3, 3])
        self.assertEqual(result.die, (1, 2, 3))

    def test_roll_average(self):
        # actually deterministic anyway
        result = operators.roll_average(2, 6)
        self.assertEqual(result.rolls, [3.5, 3.5])
        self.assertEqual(result.die, 6)
        result = operators.roll_average(2, (1, 1, 3, 5, 10))
        self.assertEqual(result.rolls, [4., 4.])
        self.assertEqual(result.die, (1, 1, 3, 5, 10))

    def test_reroll_once_on(self):
        result = operators.reroll_once_on(self.roll, 2)
        self.assertEqual(result.rolls, [1, 3, 4, 4, 5, 6])
        self.assertEqual(result.discards, [2])

    # TODO: make the mock randint() return a few different values in sequence to show what these do
    def test_reroll_once_higher(self):
        result = operators.reroll_once_higher(self.roll, 2)
        self.assertEqual(result.rolls, [1, 2, 4, 4, 4, 4])
        self.assertEqual(result.discards, [3, 4, 5, 6])

    def test_reroll_once_lower(self):
        result = operators.reroll_once_lower(self.roll, 2)
        self.assertEqual(result.rolls, [2, 3, 4, 4, 5, 6])
        self.assertEqual(result.discards, [1])

    # Also randint needs to return something else eventually for these to work
    def test_reroll_unconditional_on(self):
        pass


if __name__ == '__main__':
    unittest.main()
