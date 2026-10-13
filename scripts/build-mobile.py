#!/usr/bin/env python3
"""Build the smartphone PDF from the A4 manuscript, without copying its body."""
import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "発展-new"
MAIN_TEX = "漸化式の超体系的解説.tex"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "out/mobile")
    args = parser.parse_args()
    output = args.out_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    wrapper = output / "mobile.tex"
    wrapper.write_text(
        "% Generated from the A4 entry point; do not edit.\n"
        "\\def\\BookMobile{1}\n"
        f"\\input{{{MAIN_TEX}}}\n", encoding="utf-8",
    )
    subprocess.run(
        ["latexmk", f"-outdir={output}", str(wrapper)], cwd=BOOK, check=True,
        env={**os.environ, "max_print_line": "1000"},
    )
    print(f"Smartphone PDF: {output / 'mobile.pdf'}")


if __name__ == "__main__":
    main()
