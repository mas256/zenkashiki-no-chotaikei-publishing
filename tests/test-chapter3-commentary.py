#!/usr/bin/env python3
"""Exact checks for the alternative routes added to chapter 3."""
from fractions import Fraction
from itertools import permutations
from math import factorial


def derangements(n):
    return [p for p in permutations(range(n))
            if all(p[i] != i for i in range(n))]


# Standard 42: multiplying the coefficients and summing logarithmic increments.
a, exponent = 2, 1
for n in range(1, 16):
    assert a == 2 ** exponent == 2 ** (n * n)
    a *= 2 ** (2 * n + 1)
    exponent += 2 * n + 1

# Standard 29: direct powers and the ratio of the logarithms agree.
for n in range(1, 13):
    a = 2 ** (n * (n + 1) // 2)
    b = 2 ** ((n + 1) * (n + 2) // 2)
    assert b ** n == a ** (n + 2)

# Standard 49: remove 2^n before squaring, or subtract n after taking logs.
a, exponent = 4, 2
for n in range(1, 13):
    assert a == 2 ** exponent
    assert exponent == n + 2 ** (n - 1)
    b = Fraction(a, 2 ** n)
    next_a = Fraction(a * a, 2 ** (n - 1))
    assert Fraction(next_a, 2 ** (n + 1)) == b * b
    exponent = 2 * exponent - n + 1
    a = next_a

# Applied 3: taking ratios removes one layer of the triangular product weights.
values = [1]
for n in range(1, 10):
    next_a = 2 ** n
    for k, a in enumerate(values, 1):
        next_a *= a ** (n - k + 1)
    values.append(next_a)
    product = 1
    for a in values[:-1]:
        product *= a
    assert Fraction(values[-1], values[-2]) == 2 * product
for i in range(len(values) - 2):
    assert values[i + 2] * values[i] == values[i + 1] ** 3

# Research 10: verify both the inclusion-exclusion count and the reconnection
# bijection, including its inverse, rather than just matching total counts.
for n in range(0, 8):
    original = derangements(n)
    formula = factorial(n) * sum(
        (Fraction((-1) ** k, factorial(k)) for k in range(n + 1)), Fraction(0)
    )
    assert formula == len(original)
    if n < 2:
        continue
    images = set()
    for p in original:
        j = p[0]
        if p[j] == 0:
            continue
        k = p.index(0)
        q = tuple(j if i == k else p[i] for i in range(1, n))
        assert set(q) == set(range(1, n))
        assert all(q[i - 1] != i for i in range(1, n))
        assert (j, q) not in images
        images.add((j, q))
        inverse = [j] + list(q)
        inverse[q.index(j) + 1] = 0
        assert tuple(inverse) == p
    assert len(images) == (n - 1) * len(derangements(n - 1))

print("Chapter 3 alternative routes verified: powers, logarithms, products, and derangement bijection/counts")
