#!/usr/bin/env python3
"""Typeset repeated term links across headings, sections, pages, and math."""
from collections import Counter
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/tex/book-term-first-use.tex'
EXPECTED_CUES = {
    'chapter-intro', 'section-first', 'text-after-math', 'after-heading',
    'footnote-first', 'next-section-first', 'next-section-gamma',
    'next-chapter-intro', 'next-chapter-section',
}


def main():
    expected_links = dict(re.findall(
        r'\\TestTerm\{([^{}]+)\}\{([^{}]+)\}\{[^{}]+\}',
        FIXTURE.read_text(),
    ))
    with tempfile.TemporaryDirectory(prefix='book-term-first-use-') as directory:
        for _ in range(2):
            run = subprocess.run([
                'uplatex', '-halt-on-error', '-interaction=nonstopmode',
                '-file-line-error', '-output-directory=' + directory,
                str(FIXTURE.relative_to(ROOT)),
            ], cwd=ROOT, text=True, capture_output=True)
            if run.returncode:
                raise RuntimeError(run.stdout[-5000:] + run.stderr)
        log = (Path(directory) / 'book-term-first-use.log').read_text()
        cues = Counter(re.findall(r'^TERM-CUE:([^\s]+)$', log, re.M))
        assert cues == Counter(EXPECTED_CUES), f'Incorrect first-use marks: {cues}'
        links = Counter(re.findall(r'^TERM-LINK:([^\s:]+):term:([^\s]+)$', log, re.M))
        for context, term in expected_links.items():
            assert links[context, term] == 1, f'Term link was lost: {context}'
        print(f'Term first-use verified: {len(cues)} dotted occurrences, '
              f'{len(expected_links)} preserved body links; '
              'headings, math, subsections, page breaks, and footnotes checked')


if __name__ == '__main__':
    main()
