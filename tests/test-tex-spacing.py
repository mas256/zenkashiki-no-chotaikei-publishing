#!/usr/bin/env python3
"""Regression checks for punctuation spacing, stable imports, and source navigation."""
import gzip
import importlib.util
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('tex_spacing', ROOT / 'scripts/tex-spacing.py')
spacing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spacing)
ENGINE = shutil.which('uplatex')


class PunctuationSpacingTests(unittest.TestCase):
    def test_inline_math_digits_and_references(self):
        for target in (r'$x$', r'\(x\)', '2つ', r'\ref{key}', r'\sectionref*{key}',
                       r'\chapterref{key}', r'\headingref* {key}'):
            for punctuation in ',.':
                with self.subTest(target=target, punctuation=punctuation):
                    source = 'Text' + punctuation + target
                    expected = 'Text' + punctuation + r'\,' + target
                    self.assertEqual(spacing.rewrite(source), expected)
                    self.assertEqual(spacing.rewrite(expected), expected)

    def test_clean_only_removes_gaps_covered_by_automatic_spacing(self):
        source = r'Text,\,$x$.\,\,2つ,\,\ref{key} $a,\,b$ 著者,\,『書名』 別の\,$y$'
        cleaned = r'Text,$x$.2つ,\ref{key} $a,\,b$ 著者,\,『書名』 別の\,$y$'
        self.assertEqual(spacing.rewrite(source, insert=False, clean=True), cleaned)
        self.assertEqual(spacing.rewrite(cleaned), source.replace(r'\,\,', r'\,'))
        self.assertEqual(spacing.rewrite(source, clean=True), source.replace(r'\,\,', r'\,'))

    def test_explicit_spaces_and_numeric_punctuation_are_preserved(self):
        source = r'0.5と1,000. 例えば, $x$と, 2つ,~\ref{key}と,\quad$x$'
        self.assertEqual(spacing.rewrite(source), source)
        self.assertEqual(spacing.rewrite(r'Text, \, $x$', insert=False, clean=True), r'Text,  $x$')

    def test_math_and_aliases_are_protected(self):
        source = (r'$a,b.2,\,c$ $$a,b.2$$ \[a,b.2\] \(a,b.2\) '
                  r'\begin{align*}a,b.2,\,c\end{align*} '
                  r'\begin {align*}a,b.2,\,c\end{align*} '
                  r'\balign a,b.2,\,c\ealigin \ensuremath{a,b.2,\,c}')
        self.assertEqual(spacing.rewrite(source), source)
        self.assertEqual(spacing.rewrite(source, insert=False, clean=True), source)

    def test_urls_labels_options_comments_and_diagrams_are_protected(self):
        source = (r'\url{https://example.com/a%20b.2} '
                  r'\href{https://example.com/a.2}{Text,$x$} '
                  r'\label{key.2}\BookImport{f-1.2} [x=0,y=2,3] '
                  r'\begin{tikzpicture}\draw (0,2)--(1,3);\end{tikzpicture}'
                  '\n% Comment,$x$\n' + r'\verb|Text,$x$| Text,\$2 Text,\reference{key}')
        self.assertEqual(spacing.rewrite(source), source.replace(r'{Text,$', r'{Text,\,$'))

    def test_display_math_does_not_get_inline_spacing(self):
        source = r'Text.$$x$$ Text.\[x\] Text.\,$$x$$'
        self.assertEqual(spacing.rewrite(source), source)
        self.assertEqual(spacing.rewrite(source, insert=False, clean=True), source)

    def test_synctex_byte_anchors_and_mixed_windows_encodings(self):
        data = b'SyncTeX Version:1\nInput:1:/long/path.tex\n!1\n{1\n!3\n}1\n!4\n'
        restored = spacing.repair_anchors(data)
        previous = 0
        for match in re.finditer(rb'(?m)^!([0-9]+)\n', restored):
            self.assertEqual(int(match[1]), match.start() - previous)
            previous = match.start()
        data = 'INPUT 日本語.tex\n'.encode('utf-8') + 'INPUT 原稿.tex\n'.encode('cp932')
        self.assertEqual(spacing.decode_tex(data)[0], 'INPUT 日本語.tex\nINPUT 原稿.tex\n')


class ImportPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name)
        self.book = self.repository / '日本語の原稿'
        self.book.mkdir()
        self.cache = self.repository / 'out/tex-spacing/test'
        self.main = self.book / 'main.tex'
        self.main.write_text(
            r'\documentclass{article}\usepackage{import}\input{.book-import-map.tex}' '\n'
            r'\begin{document}\BookImport{body}\end{document}' '\n', encoding='utf-8')
        self.body = self.book / '章 本文/body.tex'
        self.body.parent.mkdir()
        self.body.write_text('% BOOK-FILE-ID: body\nText,$x$.2つ\n', encoding='utf-8')

    def generated(self, path):
        return spacing.generated_path(path, self.book, self.cache)

    def test_stable_ids_point_to_generated_inputs_and_keep_sources_unchanged(self):
        original = self.body.read_bytes()
        names = spacing.prepare(self.book, self.cache)
        self.assertEqual(self.body.read_bytes(), original)
        self.assertEqual(self.generated(self.body).read_text(), '% BOOK-FILE-ID: body\nText,\\,$x$.\\,2つ\n')
        mapping = self.generated(self.book / '.book-import-map.tex').read_text()
        self.assertIn(self.generated(self.body).parent.as_posix() + '/', mapping)
        self.assertIn(r'\BookImport{body}', self.generated(self.main).read_text())
        self.assertIn(self.generated(self.book / '.book-import-map.tex').as_posix(), self.generated(self.main).read_text())
        self.assertEqual(names[self.generated(self.body).relative_to(self.cache).as_posix()], self.body.as_posix())
        self.assertEqual(original.count(b'\n'), self.generated(self.body).read_bytes().count(b'\n'))
        timestamp = self.generated(self.body).stat().st_mtime_ns
        spacing.prepare(self.book, self.cache)
        self.assertEqual(timestamp, self.generated(self.body).stat().st_mtime_ns)

    def test_id_survives_rename_and_stale_generated_file_is_removed(self):
        spacing.prepare(self.book, self.cache)
        previous = self.generated(self.body)
        moved = self.book / '移動した章/改名.tex'
        moved.parent.mkdir()
        self.body.rename(moved)
        spacing.prepare(self.book, self.cache)
        self.assertFalse(previous.exists())
        self.assertTrue(self.generated(moved).is_file())
        self.assertIn(self.generated(moved).parent.as_posix(), self.generated(self.book / '.book-import-map.tex').read_text())

    def test_missing_and_duplicate_ids_stop_the_build(self):
        self.main.write_text(self.main.read_text().replace('{body}', '{missing}'))
        with self.assertRaisesRegex(ValueError, 'unknown or ambiguous'):
            spacing.prepare(self.book, self.cache)
        self.main.write_text(self.main.read_text().replace('{missing}', '{body}'))
        (self.book / 'duplicate.tex').write_bytes(self.body.read_bytes())
        with self.assertRaisesRegex(ValueError, 'unknown or ambiguous'):
            spacing.prepare(self.book, self.cache)

    def test_legacy_inputs_and_preamble_entry_point_are_supported(self):
        self.main.write_text(r'\input{preamble.tex}\begin{document}\input{章 本文/body.tex}\end{document}')
        preamble = self.book / 'preamble.tex'
        preamble.write_text(r'\documentclass{article}\def\Example{Text,$x$}')
        spacing.prepare(self.book, self.cache)
        self.assertEqual(spacing.main_tex(self.book), self.main)
        self.assertEqual(self.generated(preamble).read_text(), preamble.read_text())
        self.assertIn(self.generated(self.body).as_posix(), self.generated(self.main).read_text())

    def test_cleanup_follows_current_imports_and_leaves_math_and_archives(self):
        self.body.write_text('% BOOK-FILE-ID: body\nText,\\,$x$ and $a,\\,b$\n')
        archive = self.book / 'unused.tex'
        archive.write_text(r'Text,\,$x$')
        self.assertTrue(spacing.clean_sources(self.book))
        self.assertEqual(self.body.read_text(), '% BOOK-FILE-ID: body\nText,$x$ and $a,\\,b$\n')
        self.assertEqual(archive.read_text(), r'Text,\,$x$')
        self.assertFalse(spacing.clean_sources(self.book, check=True))

    @unittest.skipUnless(ENGINE, 'A LaTeX engine is needed for the compilation check')
    def test_actual_compiler_uses_spacing_and_synctex_points_at_original_sources(self):
        self.main.write_text(self.main.read_text().replace(
            r'\begin{document}',
            r'\AddToHook{file/before}{\typeout{BOOK-BEGIN:\CurrentFilePath\CurrentFile}}'
            r'\begin{document}'))
        self.body.write_text(
            '% BOOK-FILE-ID: body\n'
            r'\setbox0=\hbox{Text,\,$x$}\setbox1=\hbox{Text,$x$}' '\n'
            r'\ifdim\wd0=\wd1\typeout{SPACE-PASS}\else\errmessage{Spacing missing}\fi' '\n'
            r'\box0\box1' '\n')
        previous = Path.cwd()
        os.chdir(self.book)
        self.addCleanup(os.chdir, previous)
        result = spacing.compile_tex(['-halt-on-error', '-interaction=batchmode', '-recorder',
                                      '-synctex=1', str(self.main)], self.book, self.cache, engine=ENGINE)
        log = (self.book / 'main.log').read_text(errors='replace')
        self.assertEqual(result, 0, log[-3000:])
        self.assertIn('SPACE-PASS', log)
        self.assertIn(self.body.as_posix(), log)
        self.assertIn('BOOK-BEGIN:' + self.body.as_posix(), log)
        self.assertNotIn((self.cache / 'tree').as_posix(), log)
        recorder = (self.book / 'main.fls').read_text()
        self.assertIn('INPUT ' + self.body.as_posix(), recorder)
        navigation = gzip.decompress((self.book / 'main.synctex.gz').read_bytes()).decode('utf-8')
        self.assertIn(self.body.as_posix(), navigation)
        self.assertNotIn((self.cache / 'tree').as_posix(), navigation)

    @unittest.skipUnless(ENGINE, 'A LaTeX engine is needed for the error-location check')
    def test_failed_compilation_reports_the_original_source(self):
        self.body.write_text('% BOOK-FILE-ID: body\n' + r'\errmessage{INTENTIONAL TEST ERROR}')
        previous = Path.cwd()
        os.chdir(self.book)
        self.addCleanup(os.chdir, previous)
        result = spacing.compile_tex(['-halt-on-error', '-interaction=batchmode', '-file-line-error',
                                      '-recorder', str(self.main)], self.book, self.cache, engine=ENGINE)
        self.assertNotEqual(result, 0)
        log = (self.book / 'main.log').read_text(errors='replace')
        self.assertIn(self.body.as_posix() + ':2:', log)
        self.assertNotIn((self.cache / 'tree').as_posix(), log)

    @unittest.skipUnless(ENGINE, 'A LaTeX engine is needed for the mobile wrapper check')
    def test_mobile_wrapper_outside_book_and_source_edits_are_picked_up(self):
        self.body.write_text('% BOOK-FILE-ID: body\n\\typeout{OLD-CONTENT}Text,$x$\n')
        spacing.prepare(self.book, self.cache)
        self.body.write_text('% BOOK-FILE-ID: body\n\\typeout{NEW-CONTENT}Text,$x$\n')
        output = self.repository / 'mobile output'
        output.mkdir()
        wrapper = output / 'mobile.tex'
        wrapper.write_text(r'\def\BookMobile{1}\input{main.tex}')
        previous = Path.cwd()
        os.chdir(self.book)
        self.addCleanup(os.chdir, previous)
        result = spacing.compile_tex(['-halt-on-error', '-interaction=batchmode', '-recorder',
                                      '-synctex=1', '-output-directory=' + str(output), str(wrapper)],
                                     self.book, self.cache, engine=ENGINE)
        log = (output / 'mobile.log').read_text(errors='replace')
        self.assertEqual(result, 0, log[-3000:])
        self.assertIn('NEW-CONTENT', log)
        self.assertNotIn('OLD-CONTENT', log)
        self.assertFalse((self.book / 'mobile.dvi').exists())
        self.assertTrue((output / 'mobile.dvi').exists())
        navigation = gzip.decompress((output / 'mobile.synctex.gz').read_bytes()).decode('utf-8')
        self.assertIn(wrapper.as_posix(), navigation)
        self.assertNotIn((self.cache / 'wrappers').as_posix(), navigation)


if __name__ == '__main__':
    unittest.main()
