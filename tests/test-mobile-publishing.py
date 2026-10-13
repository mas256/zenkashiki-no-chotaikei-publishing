#!/usr/bin/env python3
"""Regression tests for paired PDFs, legacy releases, and overflow diagnostics."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assets = load("verify-release-assets")
layout = load("verify-tex-layout")


def write_pdf(directory, name, data=b"%PDF-test"):
    path = directory / name
    path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    path.with_suffix(".pdf.sha256").write_text(f"{digest}  {name}\n")
    return digest


class PublishingTests(unittest.TestCase):
    def test_overflow_points_to_nested_manuscript_and_line(self):
        log = "BOOK-BEGIN:chapter/a.tex\nBOOK-BEGIN:chapter/b.tex\nBOOK-END:chapter/b.tex\n"
        log += "Overfull \\hbox (12.4pt too wide) in paragraph\nat lines 37--42\n"
        self.assertEqual(layout.layout_errors(log), ["chapter/a.tex:37: horizontal overflow 12.4pt"])

    def test_rounding_and_underfull_are_not_overflow(self):
        self.assertFalse(layout.layout_errors("Overfull \\hbox (0.01pt too wide)\nUnderfull \\hbox (badness 10000)"))
        self.assertTrue(layout.layout_errors("LaTeX Warning: Reference `foo' undefined."))

    def test_legacy_and_paired_assets_pass_but_missing_or_bad_sha_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_pdf(directory, "book-v2.0.0.pdf")
            assets.verify(directory)
            write_pdf(directory, "book-v2.0.0-mobile.pdf", b"%PDF-smartphone")
            assets.verify(directory)
            (directory / "book-v2.0.0-mobile.pdf.sha256").unlink()
            with self.assertRaisesRegex(ValueError, "checksums"):
                assets.verify(directory)
            write_pdf(directory, "book-v2.0.0-mobile.pdf")
            (directory / "book-v2.0.0-mobile.pdf").write_bytes(b"%PDF-tampered")
            with self.assertRaisesRegex(ValueError, "Incorrect checksum"):
                assets.verify(directory)

    def test_formal_release_filter_keeps_legacy_and_rejects_partial_or_unrelated_pair(self):
        expression = re.search(r"--jq '(.*?)'", (ROOT / "scripts/lib/common.sh").read_text(), re.S)[1]
        rows = []
        for tag, names in [
            ("v1.0.0", ["book.pdf", "book.pdf.sha256"]),
            ("v2.0.0", ["book.pdf", "book.pdf.sha256", "book-mobile.pdf", "book-mobile.pdf.sha256"]),
            ("v3.0.0", ["book.pdf", "book.pdf.sha256", "book-mobile.pdf"]),
            ("v4.0.0", ["book.pdf", "book.pdf.sha256", "other-mobile.pdf", "other-mobile.pdf.sha256"]),
        ]:
            rows.append(dict(tag_name=tag, draft=False, prerelease=False,
                             published_at="2026-10-13T00:00:00Z", assets=[dict(name=name) for name in names]))
        result = subprocess.run(["jq", "-c", expression], input=json.dumps(rows), text=True, capture_output=True, check=True)
        self.assertEqual([json.loads(line)["tagName"] for line in result.stdout.splitlines()], ["v1.0.0", "v2.0.0"])

    def test_catalog_pair_and_wrong_build(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            site = directory / "site"
            build = directory / "latest-dist"
            site.mkdir()
            build.mkdir()
            (directory / "book.at-tag.yml").write_text("title: Test book\nauthor: Author\n", encoding="utf-8")
            (directory / "releases.json").write_text(json.dumps([dict(tagName="v2.0.1", publishedAt="2026-10-13T00:00:00Z")]))
            for name in ("book.pdf", "book-mobile.pdf", "latest.pdf", "latest-mobile.pdf"):
                (site / name).write_bytes(b"%PDF-" + name.encode())
            (build / "main.pdf").write_bytes((site / "latest.pdf").read_bytes())
            (build / "mobile.pdf").write_bytes((site / "latest-mobile.pdf").read_bytes())
            info = dict(commit="a" * 40, built_at="2026-10-13T00:00:00Z", pdfs={
                "mobile": {"sha256": hashlib.sha256((build / "mobile.pdf").read_bytes()).hexdigest()}})
            (build / "build-info.json").write_text(json.dumps(info))
            command = ["python3", str(ROOT / "scripts/pages-catalog.py"), "--tag", "v2.0.1", "--repo", "owner/book"]
            subprocess.run(command, cwd=directory, check=True, capture_output=True)
            catalog = json.loads((site / "catalog.json").read_text())
            self.assertEqual(catalog["release"]["mobile"]["pdf"], "Test book-スマホ版-v2.0.1.pdf")
            self.assertEqual(catalog["latest"]["commit"], "a" * 40)
            self.assertIn("スマホ版で読む", (site / "index.html").read_text())
            (site / "latest-mobile.pdf").write_bytes(b"%PDF-different-build")
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("same build", result.stderr)

    def test_legacy_catalog_does_not_offer_unpublished_mobile(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "site").mkdir()
            (directory / "book.at-tag.yml").write_text("title: Test\n")
            (directory / "releases.json").write_text(json.dumps([dict(tagName="v1.0.0", publishedAt="2026-10-13T00:00:00Z")]))
            (directory / "site/book.pdf").write_bytes(b"%PDF-old")
            subprocess.run(["python3", str(ROOT / "scripts/pages-catalog.py"), "--tag", "v1.0.0", "--repo", "owner/book"], cwd=directory, check=True)
            self.assertNotIn("mobile", json.loads((directory / "site/catalog.json").read_text())["release"])
            self.assertNotIn("スマホ版で読む", (directory / "site/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
