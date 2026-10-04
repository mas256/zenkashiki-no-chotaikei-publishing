#!/usr/bin/env python3
"""Publish named PDFs and metadata together, then render their landing page."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from render_index import parse_book


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp(value):
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        raise ValueError("Invalid release version")
    title = parse_book(Path("book.at-tag.yml").read_text(encoding="utf-8"))["title"]
    if not title or re.search(r'[\\/<>:"|?*\x00-\x1f]', title):
        raise ValueError("Title cannot be used as a PDF filename")
    releases = read_json(Path("releases.json"))
    published = next(row["publishedAt"] for row in releases if row["tagName"] == args.tag)
    site = Path("site")

    def publish(source, name, updated_at, **extra):
        data = source.read_bytes()
        if not data.startswith(b"%PDF-"):
            raise ValueError(f"Invalid PDF: {source}")
        digest = hashlib.sha256(data).hexdigest()
        shutil.copyfile(source, site / name)
        (site / (name + ".sha256")).write_text(f"{digest}  {name}\n", encoding="utf-8")
        return dict(version=args.tag, updated_at=timestamp(updated_at), pdf=name,
                    sha256=digest, **extra)

    catalog = dict(schema_version=1, title=title,
                   release=publish(site / "book.pdf", f"{title}-{args.tag}.pdf", published),
                   latest=None)
    if (site / "latest.pdf").is_file():
        info = None
        for candidate in [Path("latest-dist/build-info.json"),
                          Path("latest-dist/latest-build.json"),
                          Path("fallback-dist/legacy/latest-build.json")]:
            if candidate.is_file():
                source = candidate.parent / "main.pdf"
                if not source.is_file() or source.read_bytes() != (site / "latest.pdf").read_bytes():
                    continue
                info = read_json(candidate)
                break
        if info:
            updated_at, commit = info["built_at"], info["commit"]
        else:
            previous = read_json(Path("fallback-dist/catalog.json"))["latest"]
            actual = hashlib.sha256((site / "latest.pdf").read_bytes()).hexdigest()
            if previous["sha256"] != actual:
                raise ValueError("Preserved PDF does not match its metadata")
            updated_at, commit = previous["updated_at"], previous["commit"]
        catalog["latest"] = publish(site / "latest.pdf", f"latest-{title}-{args.tag}.pdf",
                                    updated_at, commit=commit)
    (site / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    root = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(root / "scripts/render_index.py"),
                    "--book", "book.at-tag.yml", "--releases", "releases.json",
                    "--template", str(root / ".github/pages/index.template.html"),
                    "--tag", args.tag, "--repo", args.repo,
                    "--catalog", "site/catalog.json", "--out", "site/index.html"], check=True)


if __name__ == "__main__":
    main()
