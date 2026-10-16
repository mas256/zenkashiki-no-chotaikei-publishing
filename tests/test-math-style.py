#!/usr/bin/env python3
"""Exercise math-style diagnostics without rejecting paths or TikZ arithmetic."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('math_style', ROOT / 'scripts/verify-math-style.py')
math_style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(math_style)


class MathStyleTests(unittest.TestCase):
    def test_invalid_math_is_reported(self):
        for source in (
            r'\[\frac{1}{\frac{2}{3}}\]',
            r'\(\cfrac1{\frac23}\)',
            r'\(a_n/n\)',
            r'\balign x&=1/2\ealigin',
            r'\begin{equation}x=1\end{equation}',
            r'$$x=1$$', r'\(\textstyle x\)', r'\(\tfrac12\)',
            r'\% \(a/b\)',
        ):
            with self.subTest(source=source):
                self.assertTrue(list(math_style.violations(source)))

    def test_valid_math_and_nonmath_slashes_are_preserved(self):
        for source in (
            r'\[\cfrac{1+\cfrac23}{4}\]',
            r'\[\cfrac[l]1{\cfrac[r]23}\]',
            r'\begin{align*}x&=\frac12\end{align*}',
            r'\input{a/b.tex} \url{https://example.com/x}',
            r'\draw plot(\x,\x/2) node {$x$};',
            '% \\(a/b\\)\n' + r'\(x\)',
            '\\[\\cfrac{1}{% comment\n\\cfrac23}\\]',
        ):
            with self.subTest(source=source):
                self.assertFalse(list(math_style.violations(source)))


if __name__ == '__main__':
    unittest.main()
