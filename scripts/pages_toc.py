#!/usr/bin/env python3
"""catalog.json に載せる目次(toc)と正式版の履歴(history)を作る。標準ライブラリのみ使用。

目次はPDFのしおり(アウトライン)の上位2階層から作る。しおりは poppler-utils の
pdftohtml で読み取る。しおりのないPDFでは、TeX原稿の \\section / \\subsection を使う。
目次を作れなくてもPDFの公開は止めず、警告だけを出す。
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_DEPTH = 2
SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def warn(message):
    print(f"::warning::{message}", file=sys.stderr)


def _entries(node, level, max_depth):
    entries = []
    for child in node:
        if child.tag == "item":
            title = " ".join("".join(child.itertext()).split())
            if not title:
                continue
            entry = {"title": title}
            page = child.get("page", "")
            if page.isdigit() and int(page) > 0:
                entry["page"] = int(page)
            entries.append(entry)
        elif child.tag == "outline" and entries and level < max_depth:
            sections = _entries(child, level + 1, max_depth)
            if sections:
                entries[-1]["sections"] = sections
    return entries


def parse_outline_xml(text, max_depth=MAX_DEPTH):
    """pdftohtml -xml の出力から、最上位の <outline> を目次の配列にする。"""
    start = text.find("<outline>")
    if start < 0:
        return []
    depth = 0
    end = None
    for match in re.finditer(r"<outline>|</outline>", text[start:]):
        depth += 1 if match.group(0) == "<outline>" else -1
        if depth == 0:
            end = start + match.end()
            break
    if end is None:
        raise ValueError("PDFのしおりが閉じていません")
    return _entries(ET.fromstring(text[start:end]), 1, max_depth)


def outline_from_pdf(pdf):
    try:
        result = subprocess.run(
            ["pdftohtml", "-xml", "-i", "-q", "-stdout", "-enc", "UTF-8", "-f", "1", "-l", "1", str(pdf)],
            capture_output=True, check=True, timeout=300)
        return parse_outline_xml(result.stdout.decode("utf-8", "replace"))
    except (OSError, subprocess.SubprocessError, ValueError, ET.ParseError) as error:
        warn(f"PDFのしおりを読み取れませんでした: {pdf}: {error}")
        return []


def _plain_tex(title):
    title = re.sub(r"\\[A-Za-z]+\*?", "", title)
    return " ".join(title.replace("$", "").replace("{", "").replace("}", "").replace("~", " ").split())


def toc_from_tex(source):
    """しおりのないPDF用に、TeX原稿の \\section と \\subsection から目次を作る(ページ番号なし)。"""
    path = Path(source)
    if not path.is_file():
        return []
    entries = []
    pattern = re.compile(r"^\s*\\(section|subsection)\*?\{(.+)\}\s*(?:%.*)?$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        title = _plain_tex(match.group(2))
        if not title:
            continue
        if match.group(1) == "section":
            entries.append({"title": title})
        elif entries:
            entries[-1].setdefault("sections", []).append({"title": title})
    return entries


def release_history(rows):
    """releases.json の正式版を新しい順に並べる。"""
    history = []
    for row in rows:
        match = SEMVER.match(row.get("tagName", ""))
        if match and row.get("publishedAt"):
            history.append((tuple(int(x) for x in match.groups()),
                            {"version": row["tagName"], "published_at": row["publishedAt"]}))
    history.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in history]
