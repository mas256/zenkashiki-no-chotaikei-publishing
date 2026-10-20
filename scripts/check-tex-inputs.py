#!/usr/bin/env python3
"""Resolve stable manuscript file IDs and validate the TeX import graph."""
import argparse
from collections import defaultdict, deque
from pathlib import Path
import re
import sys


COMMAND = re.compile(r'\\(?:[a-zA-Z@]+|.)', re.S)
FILE_ID = re.compile(
    r'(?m)^\ufeff?[ \t]*%[ \t]*BOOK-FILE-ID:[ \t]*([A-Za-z0-9][A-Za-z0-9._-]*)[ \t]*\r?$'
)
GENERATED_MAP = '.book-import-map.tex'
SKIP_DIRS = {'.git', 'out', 'site', 'dist', 'node_modules', '__pycache__'}
LITERAL_ENVIRONMENTS = {
    'verbatim', 'verbatim*', 'Verbatim', 'lstlisting', 'minted', 'comment',
    'tikzpicture',
}


def skip_space_and_comments(text, position):
    while position < len(text):
        if text[position].isspace():
            position += 1
        elif text[position] == '%':
            newline = text.find('\n', position)
            position = len(text) if newline < 0 else newline + 1
        else:
            break
    return position


def read_group(text, position):
    position = skip_space_and_comments(text, position)
    if position >= len(text) or text[position] != '{':
        return None
    start = position + 1
    depth = 1
    position += 1
    while position < len(text):
        if text[position] == '\\':
            match = COMMAND.match(text, position)
            position = match.end() if match else position + 1
            continue
        if text[position] == '%':
            newline = text.find('\n', position)
            position = len(text) if newline < 0 else newline + 1
            continue
        if text[position] == '{':
            depth += 1
        elif text[position] == '}':
            depth -= 1
            if depth == 0:
                return text[start:position], position + 1
        position += 1
    return None


def skip_optional_groups(text, position):
    position = skip_space_and_comments(text, position)
    while position < len(text) and text[position] == '[':
        depth = 1
        position += 1
        while position < len(text) and depth:
            if text[position] == '\\':
                match = COMMAND.match(text, position)
                position = match.end() if match else position + 1
                continue
            if text[position] == '[':
                depth += 1
            elif text[position] == ']':
                depth -= 1
            position += 1
        position = skip_space_and_comments(text, position)
    return position


def references(text):
    """Yield import calls and source spans, ignoring comments and literal TeX."""
    position = 0
    while position < len(text):
        if text[position] == '%':
            newline = text.find('\n', position)
            position = len(text) if newline < 0 else newline + 1
            continue
        if text[position] != '\\':
            position += 1
            continue

        match = COMMAND.match(text, position)
        if not match:
            position += 1
            continue
        command = match[0][1:]
        after = match.end()

        if command == 'verb':
            if after < len(text) and text[after] == '*':
                after += 1
            delimiter = text[after:after + 1]
            end = text.find(delimiter, after + 1) if delimiter else -1
            position = len(text) if end < 0 else end + 1
            continue

        if command in {'url', 'nolinkurl', 'path'}:
            group = read_group(text, after)
            position = group[1] if group else after
            continue
        if command == 'href':
            first = read_group(text, skip_optional_groups(text, after))
            second = read_group(text, first[1]) if first else None
            position = second[1] if second else (first[1] if first else after)
            continue

        if command == 'begin':
            group = read_group(text, after)
            if group and group[0] in LITERAL_ENVIRONMENTS:
                closing = r'\end{' + group[0] + '}'
                end = text.find(closing, group[1])
                position = len(text) if end < 0 else end + len(closing)
                continue

        if command == 'BookImport':
            group = read_group(text, after)
            if group:
                yield position, 'bookimport', '', group[0], group[1]
                position = group[1]
                continue
        elif command == 'subimport':
            directory = read_group(text, after)
            filename = read_group(text, directory[1]) if directory else None
            if directory and filename:
                yield position, 'subimport', directory[0], filename[0], filename[1]
                position = filename[1]
                continue
        elif command in {'input', 'include'}:
            group = read_group(text, after)
            if group:
                yield position, command, '', group[0], group[1]
                position = group[1]
                continue

        position = after


def main_file(book):
    masters = []
    for candidate in book.glob('*.tex'):
        source = candidate.read_text(encoding='utf-8')
        if re.search(r'(?m)^\s*\\documentclass\b', source):
            masters.append(candidate.resolve())
    if len(masters) != 1:
        raise RuntimeError(f'Expected one main TeX file in {book}, found {len(masters)}')
    return masters[0]


def file_id_index(repository):
    found = defaultdict(list)
    for path in repository.rglob('*.tex'):
        if any(part in SKIP_DIRS for part in path.relative_to(repository).parts):
            continue
        if path.name == GENERATED_MAP:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for identifier in FILE_ID.findall(text):
            found[identifier].append(path.resolve())
    return found


def tex_import_command(identifier, target, book):
    relative = Path(__import__('os').path.relpath(target, book)).as_posix()
    directory, filename = relative.rsplit('/', 1) if '/' in relative else ('', relative)
    if any(char in relative for char in '#%{}\\'):
        raise ValueError(f'TeX import path contains an unsupported special character: {relative}')
    directory = f'{directory}/' if directory else './'
    return (
        f'\\expandafter\\def\\csname BookImport@{identifier}\\endcsname'
        f'{{\\import{{{directory}}}{{{filename}}}}}'
    )


def render_map(index, book):
    lines = [
        '% Generated by scripts/check-tex-inputs.py; do not edit.',
        r'\providecommand{\BookImport}[1]{%',
        r'  \ifcsname BookImport@#1\endcsname',
        r'    \csname BookImport@#1\endcsname',
        r'  \else',
        r'    \PackageError{book-imports}{Unknown manuscript file ID: #1}{Add a unique BOOK-FILE-ID comment to the target TeX file.}%',
        r'  \fi%',
        r'}',
    ]
    for identifier in sorted(index):
        paths = index[identifier]
        if len(paths) == 1:
            lines.append(tex_import_command(identifier, paths[0], book))
    return '\n'.join(lines) + '\n'


def validate(book, output):
    book = book.resolve()
    repository = book.parent.resolve()
    root = main_file(book)
    index = file_id_index(repository)
    errors = []
    for identifier, paths in sorted(index.items()):
        if len(paths) > 1:
            locations = ', '.join(str(path) for path in paths)
            errors.append(f'duplicate BOOK-FILE-ID {identifier!r}: {locations}')

    pending = deque([root])
    seen = set()
    while pending:
        source_path = pending.popleft().resolve()
        if source_path in seen:
            continue
        seen.add(source_path)
        if not source_path.is_relative_to(repository):
            errors.append(f'{source_path}: imported source escapes the repository root')
            continue
        try:
            source = source_path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as error:
            errors.append(f'{source_path}: cannot read imported source ({error})')
            continue

        for position, command, directory, value, _ in references(source):
            line = source.count('\n', 0, position) + 1
            if command == 'bookimport':
                paths = index.get(value, [])
                if len(paths) != 1:
                    errors.append(
                        f'{source_path}:{line}: unknown or ambiguous BOOK-FILE-ID {value!r}'
                    )
                    continue
                target = paths[0]
                if not target.is_relative_to(repository):
                    errors.append(f'{source_path}:{line}: import escapes the repository root: {target}')
                else:
                    pending.append(target)
            elif command == 'input' and Path(value).name == GENERATED_MAP:
                continue
            else:
                errors.append(
                    f'{source_path}:{line}: use \\BookImport{{stable-id}} instead of '
                    f'\\{command}{{{directory}{value}}}'
                )

    if not errors:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        generated = render_map(index, book)
        if not output.exists() or output.read_text(encoding='utf-8') != generated:
            output.write_text(generated, encoding='utf-8', newline='')
    else:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('book', type=Path, help='manuscript directory containing the main TeX file')
    parser.add_argument(
        '--output', type=Path,
        help=f'generated TeX import map (default: BOOK/{GENERATED_MAP})',
    )
    args = parser.parse_args()
    output = args.output if args.output else args.book / GENERATED_MAP
    return validate(args.book, output)


if __name__ == '__main__':
    raise SystemExit(main())
