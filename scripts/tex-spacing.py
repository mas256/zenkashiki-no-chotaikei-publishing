#!/usr/bin/env python3
"""Add punctuation spacing in generated TeX inputs, keeping manuscript sources clean."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def discover_book(root=ROOT):
    """Find the manuscript directory whose latexmkrc invokes this script."""
    current = Path.cwd().resolve()
    candidates = [current]
    candidates.extend(path.resolve() for path in root.iterdir() if path.is_dir())
    for candidate in candidates:
        config = candidate / '.latexmkrc'
        if config.is_file() and Path(__file__).name in config.read_text(encoding='utf-8'):
            return candidate
    raise FileNotFoundError(f'Cannot find a manuscript using {Path(__file__).name}')


def main_tex(book):
    """Return the top-level TeX document, independent of its filename."""
    candidates = sorted(book.glob('*.tex'))
    masters = []
    for path in candidates:
        source = path.read_text(encoding='utf-8')
        if re.search(r'(?m)^\s*\\documentclass\b', source):
            masters.append(path)
    matches = masters or candidates
    if len(matches) != 1:
        raise RuntimeError(f'Expected one top-level TeX document in {book}, found {len(matches)}')
    return matches[0].resolve()


BOOK = discover_book()
CACHE = ROOT / 'out/tex-spacing/book'
MATH_ENVIRONMENTS = {
    'math', 'displaymath', 'equation', 'equation*', 'align', 'align*',
    'alignat', 'alignat*', 'aligned', 'gather', 'gather*', 'multline', 'multline*',
    'array', 'cases', 'matrix', 'pmatrix', 'bmatrix', 'split',
}
LITERAL_ENVIRONMENTS = {'verbatim', 'verbatim*', 'Verbatim', 'lstlisting', 'minted', 'comment', 'tikzpicture'}
LITERAL_ARGUMENTS = {
    'url', 'nolinkurl', 'path', 'href', 'label', 'ref', 'pageref', 'eqref',
    'autoref', 'sectionref', 'chapterref', 'headingref', 'input', 'include',
    'includegraphics', 'bookeqref', 'bookeqbackref',
}
COMMAND = re.compile(r'\\(?:[a-zA-Z@]+|.)', re.S)
REFERENCE = re.compile(r'\\(?:ref|sectionref|chapterref|headingref)\*?\s*(?=\{)')
MANUAL_GAP = re.compile(r'(?:\\,[ \t]*)+(?=\$|[0-9]|\\\(|' + REFERENCE.pattern + ')')


def group_end(text, start, *, comments=True):
    """Skip a balanced argument, including nested braces and escaped delimiters."""
    pairs = {'{': '}', '[': ']'}
    stack = [pairs[text[start]]]
    i = start + 1
    while i < len(text) and stack:
        if text[i] == '\\':
            match = COMMAND.match(text, i)
            i = match.end() if match else i + 1
            continue
        if comments and text[i] == '%':
            end = text.find('\n', i)
            i = len(text) if end < 0 else end + 1
            continue
        if text[i] in pairs:
            stack.append(pairs[text[i]])
        elif text[i] == stack[-1]:
            stack.pop()
        i += 1
    return i


def rewrite(text, *, insert=True, clean=False):
    """Handle text punctuation while preserving math, URLs, options, and diagrams."""
    output = []
    math_end = None
    i = 0
    while i < len(text):
        if text[i] == '%':
            end = text.find('\n', i)
            end = len(text) if end < 0 else end
            output.append(text[i:end])
            i = end
            continue
        if math_end and text.startswith(math_end, i):
            output.append(math_end)
            i += len(math_end)
            math_end = None
            continue
        if text[i] == '\\':
            match = COMMAND.match(text, i)
            if not match:
                output.append(text[i])
                i += 1
                continue
            command = match[0][1:]
            if not math_end and clean and command == ',':
                gap = MANUAL_GAP.match(text, i)
                if gap:
                    output.append(gap[0].replace(r'\,', ''))
                    i = gap.end()
                    continue
            end = match.end()
            if not math_end and command in ['[', '(']:
                math_end = r'\]' if command == '[' else r'\)'
            elif not math_end and command == 'begin' and end < len(text) and text[end] == '{':
                argument_end = group_end(text, end)
                name = text[end + 1:argument_end - 1]
                end = argument_end
                if name in MATH_ENVIRONMENTS:
                    math_end = r'\end{' + name + '}'
                elif name in LITERAL_ENVIRONMENTS:
                    closing = r'\end{' + name + '}'
                    last = text.find(closing, end)
                    end = len(text) if last < 0 else last + len(closing)
            elif not math_end and command in LITERAL_ARGUMENTS:
                if end < len(text) and text[end] == '*':
                    end += 1
                while end < len(text) and text[end].isspace():
                    end += 1
                while end < len(text) and text[end] == '[':
                    end = group_end(text, end)
                    while end < len(text) and text[end].isspace():
                        end += 1
                if end < len(text) and text[end] == '{':
                    end = group_end(text, end, comments=command not in {'url', 'nolinkurl', 'href', 'path'})
            elif command == 'verb' and end < len(text):
                if text[end] == '*':
                    end += 1
                delimiter = text[end:end + 1]
                last = text.find(delimiter, end + 1) if delimiter else -1
                end = len(text) if last < 0 else last + 1
            output.append(text[i:end])
            i = end
            continue
        if not math_end and text[i] == '$':
            math_end = '$$' if text.startswith('$$', i) else '$'
            output.append(math_end)
            i += len(math_end)
            continue
        if not math_end and text[i] == '[':
            end = group_end(text, i)
            output.append(text[i:end])
            i = end
            continue
        output.append(text[i])
        if insert and not math_end and text[i] in ',.':
            following = text[i + 1:i + 2]
            inline = (following == '$' and not text.startswith('$$', i + 1)) or text.startswith(r'\(', i + 1)
            reference = REFERENCE.match(text, i + 1)
            digit = following in '0123456789' and bool(following)
            decimal = digit and text[i] == '.' and i > 0 and text[i - 1] in '0123456789'
            thousands = digit and text[i] == ',' and i > 0 and text[i - 1] in '0123456789' and re.match(r'[0-9]{3}(?![0-9])', text[i + 1:])
            if inline or reference or (digit and not decimal and not thousands):
                output.append(r'\,')
        i += 1
    return ''.join(output)


def atomic_write(path, data):
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def source_files(book=BOOK):
    found = {}

    def visit(path):
        path = path.resolve()
        if path in found:
            return
        text = path.read_bytes().decode('utf-8')
        found[path] = text
        uncommented = re.sub(r'(?<!\\)%[^\n]*', '', text)
        for name in re.findall(r'\\input\{([^{}#]+)\}', uncommented):
            visit(book / name)

    visit(main_tex(book))
    return found


def generated_input_paths(text, book=BOOK, cache=CACHE):
    def replace(match):
        path = (book / match[1]).resolve()
        if path.is_relative_to(book.resolve()):
            target = cache / path.relative_to(book.resolve())
        elif path.is_relative_to(ROOT / 'tex'):
            target = cache.parent / 'tex' / path.relative_to(ROOT / 'tex')
        else:
            return match[0]
        return r'\input{' + target.as_posix() + '}'
    return re.sub(r'\\input\{([^{}#]+)\}', replace, text)


def prepare(book=BOOK, cache=CACHE):
    book = book.resolve()
    main = main_tex(book)
    names = {}
    for path, source in source_files(book).items():
        if path.is_relative_to(book):
            target = cache / path.relative_to(book)
            processed = source if path == main or path.is_relative_to(book / 'figures') else rewrite(source)
        elif path.is_relative_to(ROOT / 'tex'):
            target = cache.parent / 'tex' / path.relative_to(ROOT / 'tex')
            processed = source
        else:
            raise ValueError(f'Unsupported input outside the manuscript: {path}')
        atomic_write(target, generated_input_paths(processed, book, cache).encode('utf-8'))
        names[target.relative_to(cache.parent).as_posix()] = path.as_posix()
    manifest = cache.parent / 'inputs.json'
    if manifest.exists():
        for old in set(json.loads(manifest.read_text(encoding='utf-8'))) - set(names):
            path = (cache.parent / old).resolve()
            if path.is_relative_to(cache.resolve()) or path.is_relative_to((cache.parent / 'tex').resolve()):
                path.unlink(missing_ok=True)
    atomic_write(manifest, (json.dumps(names, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8'))
    (cache / 'inputs.json').unlink(missing_ok=True)


def decode_tex(data):
    try:
        return data.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        # TeX on Windows can write UTF-8 and CP932 paths on different lines
        # of the same recorder file. Decode each line independently and
        # normalize the rewritten recorder to UTF-8 for latexmk.
        lines = []
        for line in data.splitlines(keepends=True):
            try:
                lines.append(line.decode('utf-8'))
            except UnicodeDecodeError:
                try:
                    lines.append(line.decode('cp932'))
                except UnicodeDecodeError:
                    lines.append(line.decode('utf-8', errors='replace'))
        return ''.join(lines), 'utf-8'


def original_path(name, book=BOOK, cache=CACHE):
    path = Path(name).resolve()
    if path.is_relative_to(cache.resolve()):
        return (book / path.relative_to(cache.resolve())).as_posix()
    common = (cache.parent / 'tex').resolve()
    if path.is_relative_to(common):
        return (ROOT / 'tex' / path.relative_to(common)).as_posix()
    return name


def repair_anchors(data):
    """SyncTeX anchors count bytes since the preceding anchor's start."""
    result = []
    position = previous = 0
    for line in data.splitlines(keepends=True):
        if re.fullmatch(rb'![0-9]+\r?\n', line):
            ending = b'\r\n' if line.endswith(b'\r\n') else b'\n'
            line = b'!' + str(position - previous).encode('ascii') + ending
            previous = position
        result.append(line)
        position += len(line)
    return b''.join(result)


def restore_source_paths(base, extra_paths=None):
    extra_paths = extra_paths or {}

    def source_path(name):
        return extra_paths.get(Path(name).resolve(), original_path(name))

    recorder = base.with_suffix('.fls')
    if recorder.exists():
        text, encoding = decode_tex(recorder.read_bytes())
        # The compiler runs in the generated tree. Record absolute paths so
        # latexmk and editors can resolve dependencies from their own directory.
        text = re.sub(r'(?m)^INPUT ([^\r\n]+)', lambda m: 'INPUT ' + Path(m[1]).resolve().as_posix(), text)
        inputs = {line[6:] for line in text.splitlines() if line.startswith('INPUT ')}
        dependencies = {source_path(name) for name in inputs} | {Path(__file__).resolve().as_posix()}
        missing = sorted(dependencies - inputs)
        atomic_write(recorder, (text + ''.join('INPUT ' + name + '\n' for name in missing)).encode(encoding))
    for suffix in ['.synctex.gz', '.synctex']:
        path = base.with_suffix(suffix)
        if not path.exists():
            continue
        compressed = suffix.endswith('.gz')
        data = gzip.decompress(path.read_bytes()) if compressed else path.read_bytes()
        text, encoding = decode_tex(data)
        text = re.sub(r'(?m)^(Input:[0-9]+:)([^\r\n]+)', lambda m: m[1] + source_path(m[2]), text)
        restored = repair_anchors(text.encode(encoding))
        atomic_write(path, gzip.compress(restored, mtime=0) if compressed else restored)


def compile_tex(arguments):
    working_directory = Path.cwd()
    directory = working_directory
    name = None
    arguments = list(arguments)
    output_option = False
    extra_paths = {}
    for i, argument in enumerate(arguments):
        if argument.startswith('-output-directory='):
            directory = (working_directory / argument.split('=', 1)[1]).resolve()
            arguments[i] = '-output-directory=' + directory.as_posix()
            output_option = True
        elif argument == '-output-directory':
            directory = (working_directory / arguments[i + 1]).resolve()
            arguments[i + 1] = directory.as_posix()
            output_option = True
        elif argument.startswith('-jobname='):
            name = argument.split('=', 1)[1]
        elif argument.endswith('.tex'):
            path = (working_directory / argument).resolve()
            if path.is_relative_to(BOOK):
                generated = CACHE / path.relative_to(BOOK)
            else:
                # The mobile entry point is a generated wrapper outside BOOK.
                # Give its inputs the same explicit paths as the manuscript.
                key = hashlib.sha256(path.as_posix().encode('utf-8')).hexdigest()[:16]
                generated = CACHE.parent / 'wrappers' / key / path.name
                text = generated_input_paths(path.read_bytes().decode('utf-8'), BOOK, CACHE)
                atomic_write(generated, text.encode('utf-8'))
                extra_paths[generated.resolve()] = path.as_posix()
            arguments[i] = generated.as_posix()
    if name is None:
        name = next(Path(arg).stem for arg in reversed(arguments) if arg.endswith('.tex'))
    if not output_option:
        arguments.insert(0, '-output-directory=' + directory.as_posix())
    # Absolute input paths avoid LaTeX's preference for files in the output
    # directory while retaining the original working/output directories.
    run = subprocess.run(['uplatex', *arguments])
    if run.returncode:
        return run.returncode
    restore_source_paths(directory / name, extra_paths)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.compile:
        return compile_tex(args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments)
    prepare()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
