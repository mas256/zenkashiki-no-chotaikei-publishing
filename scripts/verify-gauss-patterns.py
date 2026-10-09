#!/usr/bin/env python3
"""Verify the ten floor-function examples with exact finite checks.

These checks supplement the proofs in the textbook; they are not proofs for
all indices. No floating-point arithmetic or external packages are used.
"""
from fractions import Fraction
from math import isqrt
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / '発展-new/第3章 漸化式の解説/06_発展パターン/01_ガウス型'
N = 10000
report = {}

def verify_sources():
    files = sorted(DIR.glob('[0-9][0-9]_*.tex'))
    assert len(files) == 10, f'expected 10 pattern files, got {len(files)}'
    overview = (DIR / 'ガウス型.tex').read_text(encoding='utf-8')
    all_source = '\n'.join(p.read_text(encoding='utf-8')
                           for p in (ROOT / '発展-new').rglob('*.tex'))
    labels = re.findall(r'\\label\{([^}]+)\}', all_source)
    ids = []
    for i,path in enumerate(files,1):
        source = path.read_text(encoding='utf-8')
        pid = f'example-gauss-role-{i}'
        assert f'/{path.name}' in overview
        assert source.count('\\subsubsection{') == 1
        assert source.count('\\begin{enumerate}') == 4
        assert len(re.findall(r'^\s*\\item\b',source,re.M)) == 4
        for role,dest in [('problem','answer'),('hint','problem'),
                          ('answer','problem'),('solution','problem')]:
            assert f'\\bookblocklink{{{pid}}}{{{role}}}{{{dest}}}' in source
            assert f'\\bookitemlink{{{pid}}}{{{role}}}{{{dest}}}' in source
            ids.append(f'{pid}:{role}')
        for label in re.findall(r'\\(?:sectionref|chapterref)\{([^}]+)\}',source):
            assert labels.count(label) == 1, f'unresolved or duplicated {label}'
        environments = []
        for kind,name in re.findall(r'\\(begin|end)\{([^}]+)\}',source):
            if kind == 'begin':
                environments.append(name)
            else:
                assert environments and environments.pop() == name, path.name
        assert not environments, path.name
    assert len(set(ids)) == 40
    assert '例題草案.tex' not in overview
    report['structure'] = {'patterns':10,'examples':10,'blocks':40,'links':80}

def verify_math():
    a = 1
    for n in range(1,N+1):
        assert a == 2*n-1
        a = isqrt(a*a+4*a+5)
    report['01_integer_interval'] = N

    a = 2
    for n in range(1,N+1):
        m = isqrt(n+1)
        assert a == m*(n+2)-m*(m+1)*(2*m+1)//6
        a += isqrt(n+2)
    report['02_groups'] = N

    a,terms = 1,[]
    for n in range(1,N+1):
        terms.append(a)
        assert a == (1 if n%4 in (0,1) else 3)
        x = a*a+n*n+n
        a = x-4*(x//4)
    assert all(any(terms[i] != terms[i+p] for i in range(12))
               for p in range(1,4))
    report['03_remainders'] = N

    a = 0
    for n in range(1,N+1):
        d = n//4-(n-1)//4-n//6+(n-1)//6
        assert d == int(n%4 == 0)-int(n%6 == 0)
        a += d
        assert a == n//4-n//6
    report['04_boundary_detection'] = N

    a,T0,T1 = 1,2,2
    previous = None
    for n in range(1,257):
        assert 2+T1 == 4*a
        next_a = a+isqrt(2*a*a)
        if previous is not None:
            assert next_a == 2*a+previous-1
        previous,a = a,next_a
        T0,T1 = T1,2*T1+T0
    report['05_rounding_error_Qsqrt2'] = 256

    for M in range(101):
        a = M
        for n in range(1,17):
            assert a == 6+(M-6)//(2**(n-1))
            a = (a+6)//2
        assert a == (5 if M<6 else 6)
    report['06_fixed_points'] = {'initials':101,'terms':16}

    terms = [None,2]
    for n in range(2,N+1):
        terms.append(terms[(n+1)//2]+terms[n//2]+n-1)
    for n in range(1,N+1):
        m = n.bit_length()-1
        assert terms[n] == (m+3)*n-2**(m+1)+1
        if n<N:
            assert terms[n+1]-terms[n] == m+3
    report['07_split_indices'] = N

    terms = [0]
    for n in range(1,N+1):
        terms.append(terms[n//3]+n-3*(n//3))
        q,digit_sum = n,0
        while q:
            q,r = divmod(q,3)
            digit_sum += r
        assert terms[n] == digit_sum
    assert terms[14] == 4
    report['08_ternary_digits'] = N

    # a_n = B*sqrt(2)+A. The floor is exact using integer square root.
    A,B = 0,0
    for n in range(N+1):
        assert (A,B) == (-isqrt(2*n*n),n)
        assert (-A)**2 <= 2*B*B < (1-A)**2
        floor_next = A-1+isqrt(2*(B+1)**2)
        assert floor_next in (0,1)
        A,B = A-1-floor_next,B+1
    # Rational comparison, also using exact arithmetic.
    for p,q in [(1,2),(2,3),(3,7),(5,8)]:
        x,alpha,seq = Fraction(0),Fraction(p,q),[]
        for _ in range(2*q):
            seq.append(x)
            x = x+alpha-(x+alpha).__floor__()
        assert len(set(seq[:q])) == q and seq[:q] == seq[q:]
    report['09_fractional_rotation'] = {'irrational_terms':N+1,'rational_cases':4}

    a = 0
    for n in range(1,N+1):
        a += (5*n)//2
        assert a == n*(n+1)+(n*n)//4
    for n in range(31):
        actual = sum(1 for x in range(1,n+1) for y in range(1,3*n+1)
                     if 2*y <= 5*x)
        assert actual == n*(n+1)+(n*n)//4
    report['10_lattice_count'] = {'terms':N,'geometric_cases':31}

if __name__ == '__main__':
    verify_sources()
    verify_math()
    print(json.dumps(report,ensure_ascii=False,indent=2))
