# CS50W Lecture 7 - the simplest possible test helper
# Try it:  python -c "from tests0 import test_prime; test_prime(25, False)"
from prime import is_prime


def test_prime(n, expected):
    if is_prime(n) != expected:
        print(f"ERROR on is_prime({n}), expected {expected}")
