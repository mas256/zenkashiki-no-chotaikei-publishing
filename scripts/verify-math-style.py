#!/usr/bin/env python3
"""Check the textbook math rules in all current TeX manuscripts."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPTS = ('基本-new', '発展-new', '新解釈')
TOKEN = re.compile(r'\\(?:[A-Za-z]+|.)', re.S)
FRACTION = re.compile(r'\\(?:[dtc]?frac)(?![A-Za-z])')
LEXEME = re.compile(
    r'\\(?:begin|end)\{[^}]+\}|\\(?:[A-Za-z]+|.)|\$\$|\$|/', re.S,
)


def without_comments(source):
    # Preserve positions and newlines for diagnostics, and keep escaped percent signs.
    return re.sub(r'\\(?:[A-Za-z]+|.)|%[^\n]*',
                  lambda m: ' ' * len(m[0]) if m[0].startswith('%') else m[0],
                  source)


def argument(source, position):
    while source[position].isspace():
        position += 1
    start = position
    if source[start] != '{':
        token = TOKEN.match(source, start)
        return start, token.end() if token else start + 1
    depth = 1
    position += 1
    while depth:
        token = TOKEN.match(source, position)
        if token:
            position = token.end()
            continue
        depth += (source[position] == '{') - (source[position] == '}')
        position += 1
    return start, position


def violations(source):
    source = without_comments(source)
    for token in re.finditer(
        r'\$\$|\\begin\{(?:equation\*?|align|gather\*?|multline\*?|displaymath|eqnarray\*?)\}'
        r'|\\(?:textstyle|tfrac)(?![A-Za-z])', source,
    ):
        yield token.start(), 'Use \\[ ... \\] or align* and keep inline math in displaystyle'

    for fraction in FRACTION.finditer(source):
        position = fraction.end()
        if fraction[0] == r'\cfrac':
            option = re.match(r'\s*\[[lrc]\]', source[position:])
            if option:
                position += option.end()
        start, end = argument(source, position)
        _, end = argument(source, end)
        children = list(FRACTION.finditer(source, start, end))
        if children and (fraction[0] != r'\cfrac' or
                         any(child[0] != r'\cfrac' for child in children)):
            yield fraction.start(), 'Use \\cfrac for both outer and inner nested fractions'

    math = False
    for token in LEXEME.finditer(source):
        value = token[0]
        if value == '$':
            math = not math
        elif value in (r'\(', r'\[', r'\begin{align*}', r'\balign'):
            math = True
        elif value in (r'\)', r'\]', r'\end{align*}', r'\ealigin'):
            math = False
        elif value == '/' and math:
            yield token.start(), 'Use \\frac or \\cfrac instead of / in math'


def main():
    failures = []
    files = [path for directory in MANUSCRIPTS
             for path in sorted((ROOT / directory).rglob('*.tex'))]
    for path in files:
        source = path.read_text()
        for position, message in violations(source):
            line = source.count('\n', 0, position) + 1
            failures.append(f'{path.relative_to(ROOT)}:{line}: {message}')
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    print(f'Math style verified: {len(files)} TeX files; display environments, '
          'nested fractions, inline style, and slash fractions checked')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
