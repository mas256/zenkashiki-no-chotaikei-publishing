#!/usr/bin/env python3
"""Check the proposal's glossary and exercise navigation in source and PDF."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / '発展-new'


def source_files():
    seen = {}

    def visit(path):
        path = path.resolve()
        if path in seen:
            return
        text = re.sub(r'(?<!\\)%[^\n]*', '', path.read_text())
        seen[path] = text
        for name in re.findall(r'\\input\{([^{}]+)\}', text):
            visit(BOOK / name)

    visit(BOOK / '漸化式の超体系的解説.tex')
    return seen


def check(pdf=None):
    files = source_files()
    text = '\n'.join(files.values())
    terms = Counter(re.findall(r'\\hypertarget\{term:([^{}#]+)\}', text))
    assert terms, 'No glossary destinations'
    assert all(n == 1 for n in terms.values()), 'Duplicate glossary destination'
    uses = re.findall(r'\\bookterm\{([^{}#]+)\}\{[^{}]+\}', text)
    assert not set(uses) - terms.keys(), 'A term has no glossary destination'

    blocks = re.findall(
        r'\\bookblocklink\{([^{}#]+)\}\{([^{}#]+)\}\{([^{}#]+)\}', text
    )
    destinations = {f'book:{group}:{role}' for group, role, _ in blocks}
    assert all(f'book:{group}:{target}' in destinations for group, _, target in blocks), \
        'An exercise heading points to a missing block'

    checks = next(t for p, t in files.items() if p.name == '計算と検算の確認.tex')
    for role in ('problem', 'answer'):
        pattern = (
            r'\\begin\{enumerate\}\[[^\n]*\\bookitemlink\{reading-check\}\{'
            + role + r'\}[^\n]*\](.*?)\\end\{enumerate\}'
        )
        match = re.search(pattern, checks, re.S)
        assert match and len(re.findall(r'\\item\b', match.group(1))) == 5, \
            f'The five reading checks were not preserved: {role}'

    if pdf:
        output = subprocess.check_output(['pdfinfo', '-dests', str(pdf)], text=True)
        named = set(re.findall(r'"([^"\n]+)"', output))
        required = {f'term:{term}' for term in terms} | destinations
        assert required <= named, f'Missing PDF destinations: {sorted(required - named)}'

    print(json.dumps({
        'input_files': len(files),
        'glossary_destinations': len(terms),
        'linked_term_occurrences': len(uses),
        'exercise_heading_destinations': len(destinations),
        'preserved_reading_checks': 5,
        'pdf_destinations_verified': bool(pdf),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path)
    args = parser.parse_args()
    check(args.pdf)
