# CS50W Lecture 7 - the function we want to test
import math


def is_prime(n):
    """Determines if a number is prime"""
    if n < 2:
        return False
    # In the lecture this started as range(2, int(math.sqrt(n))), which forgot the
    # last divisor and made 8 and 25 look prime. The tests found it; "+ 1" is the fix.
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True
