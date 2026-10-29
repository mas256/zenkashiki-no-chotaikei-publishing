#!/usr/bin/env python3
"""Build both TOC layouts and check heading depth and actual PDF line positions."""
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"x": "http://www.w3.org/1999/xhtml"}


def run(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def verify(variant):
    output = ROOT / "out/toc-tests" / variant
    output.mkdir(parents=True, exist_ok=True)
    prefix = r"\def\BookMobile{1}" if variant == "mobile" else ""
    for _ in range(3):
        run("uplatex", "-halt-on-error", "-interaction=nonstopmode",
            "-jobname=toc", f"-output-directory={output}",
            prefix + r"\input{tests/tex/book-toc.tex}")
    run("dvipdfmx", "-o", str(output / "toc.pdf"), str(output / "toc.dvi"))
    toc = (output / "toc.toc").read_text()
    entries = re.findall(r"\\contentsline\s*\{bookparagraph([^}]+)\}\s*\{【([^】]+)】\}", toc)
    assert entries == [
        ("section", "章直下"), ("subsection", "節直下"),
        ("subsubsection", "項直下"), ("paragraph", "小項直下"),
        ("paragraph", "続く小見出し"), ("paragraph", "2つの解の和で表せる理由"),
        ("paragraph", "目次用の短い題"), ("subsection", "番号なしの節直下"),
        ("subsection", "次の節直下"), ("section", "次の章直下"),
    ], entries
    bookmarks = re.findall(r"\\BOOKMARK\s*\[(\d+)\]", (output / "toc.out").read_text())
    assert list(map(int, bookmarks)) == [0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 4, 1, 2, 1, 2, 0, 1], bookmarks
    log = (output / "toc.log").read_text()
    assert "Overfull" not in log, log
    bbox = ET.fromstring(run("pdftotext", "-bbox-layout", str(output / "toc.pdf"), "-"))
    # 最終ページは幅を制限した目次項目だけ。折り返し行をPDFの座標で比較する。
    page = bbox.findall(".//x:page", NS)[-1]
    lines = page.findall(".//x:line", NS)
    text = ["".join(word.text or "" for word in line.findall("x:word", NS)) for line in lines]
    title_lines = [line for line, value in zip(lines, text) if any(char in value for char in "【和で理由】")]
    assert len(title_lines) == 2, text
    assert abs(float(title_lines[0].get("xMin")) - float(title_lines[1].get("xMin"))) < 1, text
    assert "【2つの解の和" in text[0], text
    assert "で表せる理由】" in "".join(text[1:]), text
    print(f"{variant}: heading hierarchy, bookmarks, and wrapped PDF lines OK ({output / 'toc.pdf'})")


if __name__ == "__main__":
    verify("a4")
    verify("mobile")
