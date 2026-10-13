#!/usr/bin/env python3
"""Verify an A4 PDF and its optional paired smartphone PDF before deployment."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(directory, release=None):
    pdfs = sorted(directory.glob("*.pdf"))
    a4 = [pdf for pdf in pdfs if not pdf.name.endswith("-mobile.pdf")]
    mobile = [pdf for pdf in pdfs if pdf.name.endswith("-mobile.pdf")]
    if len(a4) != 1 or len(mobile) > 1:
        raise ValueError("Expected one A4 PDF and at most one smartphone PDF")
    if mobile and mobile[0].name != a4[0].stem + "-mobile.pdf":
        raise ValueError("Smartphone PDF is not paired with the A4 PDF")
    expected = {pdf.name + ".sha256" for pdf in pdfs}
    if {path.name for path in directory.glob("*.pdf.sha256")} != expected:
        raise ValueError("PDFs and checksums do not match")
    api_digests = {asset["name"]: asset.get("digest") for asset in release["assets"]} if release else {}
    for pdf in pdfs:
        data = pdf.read_bytes()
        if not data.startswith(b"%PDF-"):
            raise ValueError(f"Invalid PDF: {pdf}")
        digest = hashlib.sha256(data).hexdigest()
        recorded = pdf.with_suffix(".pdf.sha256").read_text().strip()
        if recorded != f"{digest}  {pdf.name}":
            raise ValueError(f"Incorrect checksum: {pdf}")
        api_digest = api_digests.get(pdf.name)
        if api_digest and api_digest != "sha256:" + digest:
            raise ValueError(f"Incorrect GitHub digest: {pdf}")
        print(f"Verified: {pdf.name} ({digest})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--release-json", type=Path)
    args = parser.parse_args()
    release = json.loads(args.release_json.read_text()) if args.release_json else None
    verify(args.directory, release)


if __name__ == "__main__":
    main()
