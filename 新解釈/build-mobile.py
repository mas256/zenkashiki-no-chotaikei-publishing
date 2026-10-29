#!/usr/bin/env python3
"""Build the smartphone edition from this booklet's A4 entry point."""
import os
import subprocess
from pathlib import Path

BOOK = Path(__file__).resolve().parent
OUTPUT = BOOK.parent / 'out/new-interpretation-mobile'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    wrapper = OUTPUT / 'mobile.tex'
    wrapper.write_text(
        '% Generated from the A4 manuscript.\n'
        '\\def\\BookMobile{1}\n'
        '\\input{漸化式の新解釈.tex}\n', encoding='utf-8',
    )
    subprocess.run(
        ['latexmk', '-cd-', f'-outdir={OUTPUT}', f'-auxdir={OUTPUT}', str(wrapper)],
        cwd=BOOK, env={**os.environ, 'max_print_line': '1000'}, check=True,
    )
    print(f'Smartphone PDF: {OUTPUT / "mobile.pdf"}')


if __name__ == '__main__':
    main()
