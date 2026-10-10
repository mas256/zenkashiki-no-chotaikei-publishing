#!/usr/bin/env python3
"""Exact finite cross-checks; the textbook contains the general proofs."""
from fractions import Fraction as F
from math import comb
import json

counts = {}
# Normalization and subtraction independently recover the same variable-coefficient solution.
for initial in [-3, 0, 2, 3, 7]:
    a = F(initial)
    for n in range(1, 81):
        h = n*(n+1)
        expected = F(h)*((F(initial, 2)-1)+n)
        assert a == expected
        a = F(n+2, n)*a+(n+1)*(n+2)
for initial in [-3, 0, 3, 7]:
    a = F(initial)
    for n in range(1, 81):
        particular = F(n*n*(n-1)*(n+1), 2)
        assert a == particular+F(initial*n*(n+1), 2)
        a = F(n+2, n)*a+n*(n+1)*(n+2)
counts['variable_coefficient_updates'] = 720
# The invariant matches a linear update for varied positive rational initial pairs.
checks = 0
for x0 in [F(1, 2), F(1), F(2), F(3)]:
    for y0 in [F(1, 3), F(1), F(2), F(4)]:
        x, y = x0, y0
        invariant = (x*x+y*y+1)/(x*y)
        for _ in range(30):
            z = (y*y+1)/x
            assert z > 0 and z == invariant*y-x
            assert (y*y+z*z+1)/(y*z) == invariant
            x, y = y, z
            checks += 1
counts['invariant_updates'] = checks
# Boundary propagation, mixed differences, and lattice-path counting.
checks = 0
for c in [-3, -2, 0, 1, 2, 3]:
    table = [[0]*21 for _ in range(21)]
    for n in range(21): table[n][0] = n*n
    for m in range(21): table[0][m] = m*m
    for n in range(1, 21):
        for m in range(1, 21):
            table[n][m] = table[n-1][m]+table[n][m-1]-table[n-1][m-1]+c
            assert table[n][m] == n*n+m*m+c*n*m
            checks += 1
paths = [[1]*31 for _ in range(31)]
for n in range(1, 31):
    for m in range(1, 31):
        paths[n][m] = paths[n-1][m]+paths[n][m-1]
        assert paths[n][m] == comb(n+m, m)
counts['mixed_difference_cells'] = checks
counts['lattice_path_cells'] = 900
# One-period composition versus the original alternating recurrence.
for initial in [-2, 0, 1, 2, 5]:
    a = F(initial)
    for n in range(1, 101):
        k = (n+1)//2
        odd = F(1, 3)+(F(initial)-F(1, 3))*((-2)**(k-1))
        assert a == (odd if n % 2 else -odd)
        a = -a if n % 2 else 2*a+1
counts['periodic_coefficient_updates'] = 500
# Arbitrary rational initial values return the ordered pair, not only one term.
checks = 0
for x in [F(1, 2), F(1), F(2), F(3)]:
    for y in [F(1, 3), F(1), F(2), F(4)]:
        seq = [x, y]
        for _ in range(33): seq.append((1+seq[-1])/seq[-2])
        assert seq[5:7] == [x, y]
        assert all(seq[n+5] == seq[n] for n in range(30))
        checks += 30
counts['nonlinear_period_checks'] = checks
# Pell generation, Newton doubling, and the independently generated continued fractions.
pell = [(1, 0)]
x, y = 1, 0
for k in range(1, 101):
    x, y = 3*x+4*y, 2*x+3*y
    assert x*x-2*y*y == 1
    pell.append((x, y))
for k in range(1, 51):
    x, y = pell[k]
    assert pell[2*k] == (x*x+2*y*y, 2*x*y)
    ratio = F(x, y)
    x2, y2 = pell[2*k]
    assert F(x2, y2) == (ratio+2/ratio)/2
p, q = 1, 1
for j in range(1, 200):
    p, q = p+2*q, p+q
    assert p*p-2*q*q == (-1)**(j+1)
    if j % 2:
        assert (p, q) == pell[(j+1)//2]
counts['pell_updates'] = 100
counts['newton_doubling_checks'] = 50
counts['continued_fraction_updates'] = 199
# Difference identities include the small indices where factorial formulas need conventions.
def choose(n, k): return comb(n, k) if 0 <= k <= n else 0
for n in range(101):
    for k in range(12):
        assert sum(choose(j, k) for j in range(n)) == choose(n, k+1)
    assert sum(j*j for j in range(n)) == 2*choose(n, 3)+choose(n, 2)
    assert sum(j**3 for j in range(n)) == 6*choose(n, 4)+6*choose(n, 3)+choose(n, 2)
    assert sum(j**3 for j in range(n)) == F(n*n*(n-1)*(n-1), 4)
counts['binomial_sum_cases'] = 1212
# The old convolution exercise has an independent exact generating-function coefficient check.
c = [F(1)]
for n in range(100): c.append(F(2*n+1, 2*n+2)*c[-1])
for n in range(101):
    assert sum(c[k]*c[n-k] for k in range(n+1)) == 1
    assert c[n] == F(comb(2*n, n), 4**n)
counts['convolution_coefficients'] = 101
# The area scale and integer invariant are checked using the original transformations.
for t in [F(1, 4), F(1, 2), F(3, 4)]:
    u, v = (F(2), F(1)), (F(1), F(3))
    up = tuple((1-t)*u[i]+t*v[i] for i in range(2))
    vp = tuple(-t*u[i]+(1-t)*v[i] for i in range(2))
    assert up[0]*vp[1]-up[1]*vp[0] == ((1-t)**2+t*t)*(u[0]*v[1]-u[1]*v[0])
x, y = 3, 3
for _ in range(100):
    z = 3*y-x
    assert x*x+y*y+9 == 3*x*y and x*z == y*y+9
    x, y = y, z
counts['area_cases'] = 3
counts['existing_integer_invariant_updates'] = 100
print(json.dumps(counts, indent=2))
