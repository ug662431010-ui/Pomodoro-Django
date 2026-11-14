# CS50W Lecture 7 - the same checks using Python's unittest library
# Run:  python tests1.py
import unittest

from prime import is_prime


class Tests(unittest.TestCase):
    def test_1(self):
        """Make sure 1 is not prime"""
        self.assertFalse(is_prime(1))

    def test_2(self):
        """Make sure 2 is prime"""
        self.assertTrue(is_prime(2))

    def test_8(self):
        """Make sure 8 is not prime"""
        self.assertFalse(is_prime(8))

    def test_11(self):
        """Make sure 11 is prime"""
        self.assertTrue(is_prime(11))

    def test_25(self):
        """Make sure 25 is not prime"""
        self.assertFalse(is_prime(25))

    def test_28(self):
        """Make sure 28 is not prime"""
        self.assertFalse(is_prime(28))


if __name__ == "__main__":
    unittest.main()
