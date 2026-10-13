#!/usr/bin/env python3
"""Report overflow with its manuscript file/line, and reject unresolved refs."""
import argparse
import re
from pathlib import Path

OVERFULL = re.compile(r"Overfull \\([hv])box \((\d+(?:\.\d+)?)pt too (?:wide|high)\)")
UNRESOLVED = re.compile(r"There were undefined references|(?:Citation|Reference) .* undefined")


def layout_errors(text, tolerance=0.5):
    stack = []
    errors = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("BOOK-BEGIN:"):
            stack.append(line.removeprefix("BOOK-BEGIN:"))
        elif line.startswith("BOOK-END:"):
            if stack:
                stack.pop()
        overflow = OVERFULL.search(line)
        if overflow and float(overflow[2]) > tolerance:
            context = " ".join(lines[i:i + 3])
            location = re.search(r"at lines? (\d+)(?:--(\d+))?", context)
            source = stack[-1] if stack else "main/TOC"
            if location:
                source += ":" + location[1]
            direction = "horizontal" if overflow[1] == "h" else "vertical"
            errors.append(f"{source}: {direction} overflow {overflow[2]}pt")
        if UNRESOLVED.search(line):
            errors.append(line.strip())
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", type=Path, nargs="+")
    args = parser.parse_args()
    failed = False
    for log in args.logs:
        errors = layout_errors(log.read_text(encoding="utf-8", errors="replace"))
        for error in errors:
            print(f"::error file={log}::{error}")
        failed |= bool(errors)
        if not errors:
            print(f"Layout verified: {log}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
