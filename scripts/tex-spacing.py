#!/usr/bin/env python3
"""Add punctuation spacing in generated TeX inputs, keeping manuscript sources clean."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('book_imports', ROOT / 'scripts/check-tex-inputs.py')
imports = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(imports)


def main_tex(book):
    """Return the top-level TeX document, independent of its filename."""
    candidates = sorted(path for path in book.glob('*.tex') if path.name != imports.GENERATED_MAP)
    masters = []
    for path in candidates:
        source = path.read_text(encoding='utf-8')
        if re.search(r'\\begin\s*\{document\}', imports_skip_comments(source)):
            masters.append(path)
    if len(masters) != 1:
        raise ValueError(f'Expected one top-level TeX document in {book}, found {len(masters)}')
    return masters[0].resolve()


def imports_skip_comments(text):
    return re.sub(r'\\(?:[A-Za-z@]+|.)|%[^\n]*',
                  lambda match: ' ' * len(match[0]) if match[0].startswith('%') else match[0], text)


MATH_ENVIRONMENTS = {
    'math', 'displaymath', 'equation', 'equation*', 'align', 'align*',
    'alignat', 'alignat*', 'aligned', 'gather', 'gather*', 'multline', 'multline*',
    'array', 'cases', 'matrix', 'pmatrix', 'bmatrix', 'split', 'eqnarray', 'eqnarray*',
}
LITERAL_ENVIRONMENTS = {'verbatim', 'verbatim*', 'Verbatim', 'lstlisting', 'minted', 'comment', 'tikzpicture'}
LITERAL_ARGUMENTS = {
    'url', 'nolinkurl', 'path', 'href', 'label', 'ref', 'pageref', 'eqref',
    'autoref', 'sectionref', 'chapterref', 'headingref', 'input', 'include',
    'includegraphics', 'bookeqref', 'bookeqbackref', 'BookImport', 'ensuremath',
}
COMMAND = re.compile(r'\\(?:[a-zA-Z@]+|.)', re.S)
REFERENCE = re.compile(r'\\(?:ref|sectionref|chapterref|headingref)\*?\s*(?=\{)')
MANUAL_GAP = re.compile(r'[ \t]*(?:\\,[ \t]*)+')


def spacing_target(text, position, punctuation):
    """Keep decimal points, digit group separators, and display math intact."""
    following = text[position:position + 1]
    inline = (following == '$' and not text.startswith('$$', position)) or text.startswith(r'\(', position)
    reference = REFERENCE.match(text, position)
    digit = bool(following) and following in '0123456789'
    previous = text[punctuation - 1:punctuation]
    numeric = bool(previous) and previous in '0123456789'
    decimal = digit and text[punctuation] == '.' and numeric
    thousands = digit and text[punctuation] == ',' and numeric and re.match(r'[0-9]{3}(?![0-9])', text[position:])
    return bool(inline or reference or (digit and not decimal and not thousands))


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
            end = match.end()
            if not math_end and command in ['[', '(']:
                math_end = r'\]' if command == '[' else r'\)'
            elif not math_end and command == 'balign':
                math_end = r'\ealigin'
            elif not math_end and command == 'begin':
                start = imports.skip_space_and_comments(text, end)
                if start < len(text) and text[start] == '{':
                    end = group_end(text, start)
                    name = text[start + 1:end - 1]
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
        if not math_end and text[i] in ',.':
            gap = MANUAL_GAP.match(text, i + 1) if clean else None
            if gap and spacing_target(text, gap.end(), i):
                spaces = gap[0].replace(r'\,', '')
                output.append(spaces)
                if insert and not spaces:
                    output.append(r'\,')
                i = gap.end()
                continue
            if insert and spacing_target(text, i + 1, i):
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


def cache_directory(book):
    return book.parent / 'out/tex-spacing' / book.name


def generated_path(path, book, cache):
    path = path.resolve()
    if not path.is_relative_to(book.parent):
        raise ValueError(f'Imported TeX source escapes the repository: {path}')
    return cache / 'tree' / path.relative_to(book.parent)


def id_index(book, cache):
    return {identifier: [path for path in paths if not path.is_relative_to(cache)]
            for identifier, paths in imports.file_id_index(book.parent).items()}


def input_target(command, directory, value, source, book, index):
    if command == 'bookimport':
        paths = index.get(value, [])
        if len(paths) != 1:
            raise ValueError(f'{source}: unknown or ambiguous BOOK-FILE-ID {value!r}')
        return paths[0]
    if command == 'input' and Path(value).name == imports.GENERATED_MAP:
        return book / imports.GENERATED_MAP
    if '#' in value or '#' in directory:
        raise ValueError(f'{source}: dynamic TeX input cannot be resolved: {value!r}')
    relative = Path(directory) / value
    if not relative.suffix:
        relative = relative.with_suffix('.tex')
    bases = [source.parent, book] if command == 'subimport' else [book, source.parent]
    for base in bases:
        candidate = (base / relative).resolve()
        if candidate.is_file():
            return candidate
    raise ValueError(f'{source}: imported TeX source not found: {relative}')


def source_files(book, cache):
    """Follow the actual import graph, including stable IDs and legacy inputs."""
    index = id_index(book, cache)
    found = {}

    def visit(path):
        path = path.resolve()
        generated_path(path, book, cache)  # Validate before reading.
        if path in found or path.name == imports.GENERATED_MAP:
            return
        text = path.read_bytes().decode('utf-8')
        found[path] = text
        for _, command, directory, value, _ in imports.references(text):
            visit(input_target(command, directory, value, path, book, index))

    visit(main_tex(book))
    return found, index


def generated_input_paths(text, source, book, cache, index):
    output = []
    previous = 0
    for position, command, directory, value, end in imports.references(text):
        if command == 'bookimport':
            continue
        path = input_target(command, directory, value, source, book, index)
        target = generated_path(path, book, cache)
        output.append(text[previous:position])
        if command == 'subimport':
            output.append(r'\import{' + target.parent.as_posix() + '/}{' + target.name + '}')
        else:
            output.append('\\' + command + '{' + target.as_posix() + '}')
        previous = end
    output.append(text[previous:])
    return ''.join(output)


def rewrite_source(text, path, book, main, **options):
    """Typesetting code and diagram definitions do not contain prose to fix."""
    if not path.is_relative_to(book) or 'figures' in path.relative_to(book).parts or path.name == 'preamble.tex':
        return text
    if path == main:
        marker = re.search(r'\\begin\s*\{document\}', imports_skip_comments(text))
        if not marker:
            return text
        return text[:marker.end()] + rewrite(text[marker.end():], **options)
    return rewrite(text, **options)


def prepare(book, cache=None):
    book = book.resolve()
    cache = (cache or cache_directory(book)).resolve()
    sources, index = source_files(book, cache)
    main = main_tex(book)
    names = {}
    for path, source in sources.items():
        target = generated_path(path, book, cache)
        processed = generated_input_paths(source, path, book, cache, index)
        processed = rewrite_source(processed, path, book, main)
        atomic_write(target, processed.encode('utf-8'))
        names[target.relative_to(cache).as_posix()] = path.as_posix()

    # Keep stable IDs in the sources; only the generated map points at copies.
    mapping = imports.render_map({}, book)
    for identifier, paths in sorted(index.items()):
        if len(paths) == 1 and paths[0] in sources:
            target = generated_path(paths[0], book, cache)
            mapping += (
                f'\\expandafter\\def\\csname BookImport@{identifier}\\endcsname'
                f'{{\\import{{{target.parent.as_posix()}/}}{{{target.name}}}}}\n'
            )
    target = generated_path(book / imports.GENERATED_MAP, book, cache)
    atomic_write(target, mapping.encode('utf-8'))
    names[target.relative_to(cache).as_posix()] = (book / imports.GENERATED_MAP).as_posix()
    manifest = cache / 'inputs.json'
    if manifest.exists():
        for old in set(json.loads(manifest.read_text(encoding='utf-8'))) - set(names):
            path = (cache / old).resolve()
            if path.is_relative_to(cache / 'tree'):
                path.unlink(missing_ok=True)
    atomic_write(manifest, (json.dumps(names, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8'))
    return names


def clean_sources(book, *, check=False):
    book = book.resolve()
    sources, _ = source_files(book, cache_directory(book))
    main = main_tex(book)
    count = files = 0
    for path, source in sources.items():
        cleaned = rewrite_source(source, path, book, main, insert=False, clean=True)
        if cleaned != source:
            files += 1
            count += source.count(r'\,') - cleaned.count(r'\,')
            if check:
                print(f'{path}: manual punctuation spacing can be removed', file=sys.stderr)
            else:
                atomic_write(path, cleaned.encode('utf-8'))
    if not check:
        print(f'{book.name}: removed {count} manual gaps from {files} files')
    return bool(files)


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


def restore_source_paths(base, book, cache, names, extra_paths=None):
    paths = {(cache / target).resolve(): source for target, source in names.items()}
    paths.update(extra_paths or {})

    def source_path(name):
        return paths.get(Path(name).resolve(), name)

    log = Path(str(base) + '.log')
    if log.exists():
        text, encoding = decode_tex(log.read_bytes())
        for generated, original in sorted(paths.items(), key=lambda item: len(str(item[0])), reverse=True):
            text = text.replace(generated.as_posix(), original)
        atomic_write(log, text.encode(encoding))

    recorder = Path(str(base) + '.fls')
    if recorder.exists():
        text, encoding = decode_tex(recorder.read_bytes())
        # The compiler runs in the generated tree. Record absolute paths so
        # latexmk and editors can resolve dependencies from their own directory.
        text = re.sub(r'(?m)^INPUT ([^\r\n]+)', lambda m: 'INPUT ' + Path(m[1]).resolve().as_posix(), text)
        inputs = {line[6:] for line in text.splitlines() if line.startswith('INPUT ')}
        dependencies = {source_path(name) for name in inputs} | {
            Path(__file__).resolve().as_posix(), Path(imports.__file__).resolve().as_posix(),
        }
        dependencies = {name for name in dependencies if Path(name).is_file()}
        missing = sorted(dependencies - inputs)
        atomic_write(recorder, (text + ''.join('INPUT ' + name + '\n' for name in missing)).encode(encoding))
    for suffix in ['.synctex.gz', '.synctex']:
        path = Path(str(base) + suffix)
        if not path.exists():
            continue
        compressed = suffix.endswith('.gz')
        data = gzip.decompress(path.read_bytes()) if compressed else path.read_bytes()
        text, encoding = decode_tex(data)
        text = re.sub(r'(?m)^(Input:[0-9]+:)([^\r\n]+)', lambda m: m[1] + source_path(m[2]), text)
        restored = repair_anchors(text.encode(encoding))
        atomic_write(path, gzip.compress(restored, mtime=0) if compressed else restored)


def compile_tex(arguments, book, cache=None, *, engine='uplatex'):
    book = book.resolve()
    cache = (cache or cache_directory(book)).resolve()
    names = prepare(book, cache)
    index = id_index(book, cache)
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
            relative = path.relative_to(book.parent).as_posix() if path.is_relative_to(book.parent) else None
            if relative and 'tree/' + relative in names:
                generated = generated_path(path, book, cache)
            else:
                # The mobile entry point is a generated wrapper outside BOOK.
                # Give its inputs the same explicit paths as the manuscript.
                key = hashlib.sha256(path.as_posix().encode('utf-8')).hexdigest()[:16]
                generated = cache / 'wrappers' / key / path.name
                text = generated_input_paths(path.read_bytes().decode('utf-8'), path, book, cache, index)
                atomic_write(generated, text.encode('utf-8'))
                extra_paths[generated.resolve()] = path.as_posix()
            arguments[i] = generated.as_posix()
    if name is None:
        name = next(Path(arg).stem for arg in reversed(arguments) if arg.endswith('.tex'))
    if not output_option:
        arguments.insert(0, '-output-directory=' + directory.as_posix())
    # Absolute input paths avoid LaTeX's preference for files in the output
    # directory while retaining the original working/output directories.
    run = subprocess.run([engine, *arguments], env={
        **os.environ, 'max_print_line': os.environ.get('max_print_line', '1000'),
    })
    if run.returncode:
        return run.returncode
    restore_source_paths(directory / name, book, cache, names, extra_paths)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', type=Path, default=Path.cwd(), help='original manuscript directory')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--clean', action='store_true', help='remove manual gaps covered by automatic spacing')
    parser.add_argument('--check-clean', action='store_true', help='reject redundant manual punctuation gaps')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if sum((args.compile, args.prepare, args.clean, args.check_clean)) > 1:
        parser.error('Choose only one of --prepare, --compile, --clean, --check-clean')
    if args.clean or args.check_clean:
        found = clean_sources(args.book, check=args.check_clean)
        return int(args.check_clean and found)
    if args.compile:
        return compile_tex(args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments, args.book)
    prepare(args.book)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f'tex-spacing: {error}', file=sys.stderr)
        raise SystemExit(1)
