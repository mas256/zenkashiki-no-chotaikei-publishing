import importlib.util
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('tex_spacing', ROOT / 'scripts/tex-spacing.py')
spacing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spacing)


class PunctuationSpacingTests(unittest.TestCase):
    def test_references_after_punctuation(self):
        for command in ('ref', 'sectionref', 'chapterref', 'headingref'):
            for star in ('', '*'):
                for punctuation in (',', '.'):
                    with self.subTest(command=command, star=star, punctuation=punctuation):
                        reference = '\\' + command + star + '{target}'
                        source = 'Text' + punctuation + reference
                        expected = 'Text' + punctuation + r'\,' + reference
                        self.assertEqual(spacing.rewrite(source), expected)
                        self.assertEqual(spacing.rewrite(expected), expected)
        self.assertEqual(spacing.rewrite(r'Text,\ref {target}'), r'Text,\,\ref {target}')

    def test_reference_spacing_preserves_existing_gaps_and_protected_contexts(self):
        source = (r'Text, \ref{target}.\,\sectionref*{target},~\chapterref{target}'
                  r' $x,\ref{target}$ \[x.\chapterref{target}\]'
                  r' \label{key,\ref{target}} [key,\sectionref{target}]'
                  r' \url{https://example.com/,\chapterref{target}}'
                  r' \verb|,\ref{target}|'
                  r' Text,\reference{target}.\refstepcounter{section}'
                  r' Text,\refname.\ref@internal{target}')
        self.assertEqual(spacing.rewrite(source), source)

    def test_manual_reference_spacing_can_be_removed_and_restored(self):
        for command in ('ref', 'sectionref', 'chapterref', 'headingref'):
            for star in ('', '*'):
                with self.subTest(command=command, star=star):
                    reference = '\\' + command + star + '{target}'
                    source = 'Text,' + r'\,\,' + reference
                    cleaned = spacing.rewrite(source, insert=False, clean=True)
                    self.assertEqual(cleaned, 'Text,' + reference)
                    self.assertEqual(spacing.rewrite(cleaned), 'Text,' + r'\,' + reference)
        source = r'$x,\,\ref{target}$ \label{key,\,\ref{target}}'
        self.assertEqual(spacing.rewrite(source, insert=False, clean=True), source)

    def test_text_math_and_numbers(self):
        self.assertEqual(spacing.rewrite(r'従って,$a_n=2$.3つ.\(x\)を使う.'),
                         r'従って,\,$a_n=2$.\,3つ.\,\(x\)を使う.')

    def test_decimal_numbers_thousands_and_explicit_spaces(self):
        source = r'0.5と1,000. 例えば, $x$と, 2つ.'
        self.assertEqual(spacing.rewrite(source), source)

    def test_math_spacing_is_preserved(self):
        source = r'$x,y,\,z=0.5$ $$a,b$$ \[a,b.2\] \(p,q\) \begin{align*}a,b.2\end{align*}'
        self.assertEqual(spacing.rewrite(source), source)

    def test_urls_options_and_tikz_are_preserved(self):
        source = r'\href{https://example.com/section.2}{説明,$x$}\url{https://example.com/a.2} [x=0,y=2,3] \begin{tikzpicture}\draw (0,2)--(1,3);\end{tikzpicture}'
        self.assertEqual(spacing.rewrite(source), source.replace(r'説明,$', r'説明,\,$'))

    def test_percent_encoded_url_does_not_hide_following_prose(self):
        source = r'\url{https://example.com/a%20b.2}続いて,$x$'
        self.assertEqual(spacing.rewrite(source), source.replace(r'続いて,$', r'続いて,\,$'))

    def test_manual_text_spacing_only(self):
        source = r'文,\,$x$と,\,\,$y$.\,2つ $a,\,b$ 著者,\,『書名』'
        cleaned = spacing.rewrite(source, insert=False, clean=True)
        self.assertEqual(cleaned, r'文,$x$と,$y$.2つ $a,\,b$ 著者,\,『書名』')
        self.assertEqual(spacing.rewrite(cleaned), r'文,\,$x$と,\,$y$.\,2つ $a,\,b$ 著者,\,『書名』')

    def test_comments_verbatim_escaped_dollars_and_display_math(self):
        source = '本文,\\$2.\n% 注釈,$x$\n' + r'\verb|a.2,$x$|文.$$x$$'
        self.assertEqual(spacing.rewrite(source), source)

    def test_synctex_anchor_offsets_survive_path_changes(self):
        data = b'SyncTeX Version:1\nInput:1:/a/longer/path.tex\n!1\n{1\n!3\n}1\n!4\n'
        result = spacing.repair_anchors(data)
        previous = 0
        for match in re.finditer(rb'(?m)^!([0-9]+)\n', result):
            self.assertEqual(int(match[1]), match.start() - previous)
            previous = match.start()

    def test_generated_inputs_leave_sources_untouched_and_track_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory) / 'book'
            cache = Path(directory) / 'generated'
            book.mkdir()
            (book / spacing.MAIN).write_text(r'\input{body.tex}', encoding='utf-8')
            source = book / 'body.tex'
            source.write_text(r'例えば,$x$.2つ', encoding='utf-8')
            spacing.prepare(book, cache)
            generated = cache / 'body.tex'
            self.assertEqual(source.read_text(encoding='utf-8'), r'例えば,$x$.2つ')
            self.assertEqual(generated.read_text(encoding='utf-8'), r'例えば,\,$x$.\,2つ')
            timestamp = generated.stat().st_mtime_ns
            spacing.prepare(book, cache)
            self.assertEqual(generated.stat().st_mtime_ns, timestamp)
            source.write_text(r'次に,$y$', encoding='utf-8')
            spacing.prepare(book, cache)
            self.assertEqual(generated.read_text(encoding='utf-8'), r'次に,\,$y$')

    @unittest.skipUnless(shutil.which('uplatex'), 'upLaTeX is needed for the input-resolution check')
    def test_compiler_selects_generated_inputs_and_keeps_output_location(self):
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory) / 'book'
            cache = Path(directory) / 'generated'
            book.mkdir()
            main = book / spacing.MAIN
            main.write_text(r'\documentclass{article}\begin{document}\input{body.tex}\end{document}', encoding='utf-8')
            (book / 'body.tex').write_text(r'\errmessage{ORIGINAL INPUT SELECTED}', encoding='utf-8')
            spacing.prepare(book, cache)
            (cache / 'body.tex').write_text(r'\typeout{GENERATED INPUT SELECTED}Example.', encoding='utf-8')
            previous = Path.cwd()
            try:
                os.chdir(book)
                with patch.object(spacing, 'BOOK', book), patch.object(spacing, 'CACHE', cache):
                    result = spacing.compile_tex(['-halt-on-error', '-interaction=batchmode', '-jobname=probe', str(main)])
                log = (book / 'probe.log').read_text(encoding='utf-8', errors='replace')
                self.assertEqual(result, 0, log[-3000:])
                self.assertIn('GENERATED INPUT SELECTED', (book / 'probe.log').read_text(encoding='utf-8'))
                self.assertTrue((book / 'probe.dvi').exists())
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
