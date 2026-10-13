#!/usr/bin/env python3
"""Verify every page's visible and physical dimensions (A4 by default)."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

TOLERANCE_PT = 0.2  # pdfinfo rounds PDF coordinates to two decimals
BOX_RE = re.compile(
    r"^Page\s+(\d+)\s+(MediaBox|CropBox):\s+"
    r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+"
    r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)$"
)


def pdfinfo(pdf: Path, *args: str) -> str:
    return subprocess.run(
        ["pdfinfo", *args, str(pdf)],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--width-mm", type=float, default=210)
    parser.add_argument("--height-mm", type=float, default=297)
    args = parser.parse_args()
    pdf = args.pdf
    width_pt = args.width_mm / 25.4 * 72
    height_pt = args.height_mm / 25.4 * 72
    info = pdfinfo(pdf)
    count = re.search(r"^Pages:\s*(\d+)\s*$", info, re.MULTILINE)
    if count is None:
        print("Could not determine PDF page count", file=sys.stderr)
        return 1

    pages = int(count.group(1))
    boxes: set[tuple[int, str]] = set()
    invalid: list[str] = []
    for line in pdfinfo(pdf, "-f", "1", "-l", str(pages), "-box").splitlines():
        match = BOX_RE.match(line)
        if match is None:
            continue
        page, name = int(match[1]), match[2]
        x0, y0, x1, y1 = (float(value) for value in match.groups()[2:])
        boxes.add((page, name))
        width, height = x1 - x0, y1 - y0
        if abs(width - width_pt) > TOLERANCE_PT or abs(height - height_pt) > TOLERANCE_PT:
            invalid.append(f"page {page} {name}: {width:.2f} x {height:.2f} pt")

    missing = [
        f"page {page} {name}"
        for page in range(1, pages + 1)
        for name in ("MediaBox", "CropBox")
        if (page, name) not in boxes
    ]
    if invalid or missing:
        for message in invalid:
            print(f"Wrong page dimensions: {message}", file=sys.stderr)
        for message in missing:
            print(f"Missing page box: {message}", file=sys.stderr)
        return 1

    print(f"{args.width_mm:g} × {args.height_mm:g} mm verified for all {pages} pages (MediaBox and CropBox)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
