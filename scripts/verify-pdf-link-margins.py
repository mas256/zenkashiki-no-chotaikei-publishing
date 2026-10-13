#!/usr/bin/env python3
"""Detect body link annotations that accidentally include running heads/feet.

Poppler's XML associates a visible text span with any overlapping annotation.
This checks the rendered PDF, rather than assuming resolved destinations also
imply correctly bounded clickable regions. Only poppler-utils is required.
"""
import argparse
import subprocess
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf')
    parser.add_argument('--header-height', type=float, default=50)
    parser.add_argument('--footer-height', type=float, default=25)
    args = parser.parse_args()
    result = subprocess.run(
        ['pdftohtml', '-q', '-i', '-xml', '-hidden', '-zoom', '1', '-stdout', args.pdf],
        check=True, text=True, capture_output=True,
    )
    document = ET.fromstring(result.stdout)
    failures = []
    links = 0
    pages = document.findall('page')
    for page in pages:
        height = float(page.attrib['height'])
        for span in page.findall('text'):
            anchors = span.findall('.//a')
            links += len(anchors)
            top = float(span.attrib['top'])
            bottom = top + float(span.attrib['height'])
            if anchors and (top < args.header_height or bottom > height - args.footer_height):
                failures.append(f"page {page.attrib['number']}: {''.join(span.itertext())}")
    if failures:
        raise SystemExit('Linked running head/footer text:\n' + '\n'.join(failures))
    if not pages or not links:
        raise SystemExit('No pages or body links were found')
    print(f'PDF link margins verified: {len(pages)} pages, {links} linked text spans')


if __name__ == '__main__':
    main()
