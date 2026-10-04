#!/usr/bin/env python3
"""Pagesのトップページ(index.html)を生成する。標準ライブラリのみ使用。

book.yml は次の単純な形式だけを読む(未対応の記法はエラーにする)。
    key: value
    key:
      - item
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from string import Template
from urllib.parse import quote

SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def parse_book(text: str) -> dict:
    data: dict = {}
    current_list = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m_item = re.match(r"^\s+-\s+(.*)$", raw)
        if m_item and current_list is not None:
            current_list.append(unquote(m_item.group(1).strip()))
            continue
        m_kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", raw)
        if not m_kv:
            raise ValueError(f"book.yml:{lineno}: 未対応の記法です: {raw!r}")
        key, value = m_kv.group(1), m_kv.group(2).strip()
        if value == "":
            current_list = []
            data[key] = current_list
        else:
            if value[0] in "[{|>&*!%@`" :
                raise ValueError(f"book.yml:{lineno}: 未対応の記法です(フロー形式・ブロックスカラー等): {raw!r}")
            current_list = None
            data[key] = unquote(value)
    return data


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def semver_key(tag: str):
    m = SEMVER.match(tag)
    return tuple(int(x) for x in m.groups()) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    ap.add_argument("--releases", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--catalog")
    args = ap.parse_args()

    if not SEMVER.match(args.tag):
        print(f"正式版Tagの形式ではありません: {args.tag}", file=sys.stderr)
        return 1

    book = parse_book(Path(args.book).read_text(encoding="utf-8"))
    releases = json.loads(Path(args.releases).read_text(encoding="utf-8"))

    rows = []
    for r in releases:
        key = semver_key(r["tagName"])
        if key is not None:
            rows.append((key, r["tagName"], (r.get("publishedAt") or "")[:10]))
    rows.sort(reverse=True)

    published = {tag: date for _, tag, date in rows}
    if args.tag not in published:
        print(f"公開済みReleaseに {args.tag} がありません", file=sys.stderr)
        return 1

    repo_url = f"https://github.com/{args.repo}"
    items = []
    for _, tag, date in rows:
        cur = ' <span class="cur">現在の版</span>' if tag == args.tag else ""
        items.append(
            f'<li><a href="{html.escape(repo_url)}/releases/tag/{html.escape(tag)}">'
            f"{html.escape(tag)}</a> <time>{html.escape(date)}</time>{cur}</li>"
        )

    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8")) if args.catalog else None
    filename = f"{book['title']}-{args.tag}.pdf"
    latest_link = ""
    if catalog and catalog.get("latest"):
        latest = catalog["latest"]
        url = quote(latest["pdf"]) + "?sha=" + latest["sha256"]
        latest_link = (f'<p><a href="{html.escape(url)}">最新版（開発中）のPDF</a>'
                       f' <time datetime="{html.escape(latest["updated_at"])}">'
                       f'{html.escape(latest["updated_at"])}</time></p>')
    authors = book.get("author", [])
    if isinstance(authors, str):
        authors = [authors]
    if not isinstance(authors, list) or any(not isinstance(author, str) for author in authors):
        raise ValueError("book.yml の author は文字列または文字列リストで指定してください")

    esc = html.escape
    page = Template(Path(args.template).read_text(encoding="utf-8")).substitute(
        lang=esc(str(book.get("language", "ja")), quote=True),
        title=esc(str(book.get("title", ""))),
        authors=esc("、".join(authors)),
        description=esc(book.get("description", "")),
        pdf_url=esc(quote(filename), quote=True),
        latest_link=latest_link,
        tag=esc(args.tag),
        date=esc(published[args.tag]),
        release_items="\n      ".join(items),
        repo_url=esc(repo_url),
        releases_url=esc(f"{repo_url}/releases"),
        current_release_url=esc(f"{repo_url}/releases/tag/{args.tag}"),
    )
    Path(args.out).write_text(page, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
