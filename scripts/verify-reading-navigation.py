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
        text = re.sub(r'(?<!\\)%[^\n]*', '', path.read_text(encoding='utf-8'))
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

    tags = Counter(re.findall(r'\\booktag\{([^{}#]+)\}\{[^{}]+\}', text))
    returns = Counter(re.findall(r'\\bookeqbackref\{([^{}#]+)\}', text))
    equation_uses = re.findall(r'\\bookeq(?:back)?ref\{([^{}#]+)\}', text)
    assert len(tags) == 15 and all(n == 1 for n in tags.values()), \
        'Manual equation tags must have distinct destinations'
    assert tags == returns, 'An equation tag has no unique return link'
    assert not set(equation_uses) - tags.keys(), 'An equation reference has no tag'

    checks = next(t for p, t in files.items() if p.name == '03_計算と検算.tex')
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
        required |= {f'eqcite:{tag}' for tag in tags}
        aux = pdf.with_suffix('.aux').read_text(encoding='utf-8')
        tag_destinations = dict(re.findall(
            r'\\newlabel\{eqtag:([^{}]+)\}[^\n]*\{(AMS\.[^{}]+)\}\{\}\}', aux
        ))
        assert tags.keys() == tag_destinations.keys(), \
            'An equation tag has no resolved equation label'
        required |= set(tag_destinations.values())
        assert required <= named, f'Missing PDF destinations: {sorted(required - named)}'

    print(json.dumps({
        'input_files': len(files),
        'glossary_destinations': len(terms),
        'linked_term_occurrences': len(uses),
        'exercise_heading_destinations': len(destinations),
        'preserved_reading_checks': 5,
        'manual_equation_tags': len(tags),
        'equation_reference_occurrences': len(equation_uses),
        'pdf_destinations_verified': bool(pdf),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path)
    args = parser.parse_args()
    check(args.pdf)
