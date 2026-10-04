"""Verify real global defaults in a fresh folder outside the manuscript project."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

STAGE = Path(__file__).resolve().parent
source = STAGE / 'verify'
check = Path(tempfile.mkdtemp(prefix='latex-global-verified-'))
for name in ['日本語 原稿.tex', 'references.bib', '章 本文']:
    item = source / name
    if item.is_dir():
        shutil.copytree(item, check / name)
    else:
        shutil.copy2(item, check / name)

env = os.environ.copy()
env['LC_ALL'] = 'C'
env['LANG'] = 'C'
binary = shutil.which('latexmk')
assert binary and 'texlive\\2026\\' in binary.lower(), binary
command = [binary, str(check / '日本語 原稿.tex')]
run = subprocess.run(command, cwd=STAGE, env=env, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, timeout=120)
output = run.stdout.decode('cp932', errors='replace')
(STAGE / 'verified-global-build.log').write_bytes(run.stdout)
assert run.returncode == 0, output[-5000:]
assert '.latexmkrc' in output and str(check / '.latexmkrc') not in output
assert not (check / '.latexmkrc').exists() and not (check / 'latexmkrc').exists()
for tool in ['uplatex', 'upbibtex', 'upmendex', 'dvipdfmx']:
    assert f"Running '{tool}" in output, f'{tool} did not run'
base = check / '日本語 原稿'
for extension in ['pdf', 'dvi', 'fls', 'bbl', 'ind']:
    artifact = base.with_suffix('.' + extension)
    assert artifact.is_file() and artifact.stat().st_size > 0, artifact
assert base.with_suffix('.pdf').read_bytes().startswith(b'%PDF-')
log = base.with_suffix('.log').read_text(encoding='utf-8', errors='replace')
assert 'upTeX' in log
assert not re.search(r'undefined references|undefined citations|Citation .* undefined|Reference .* undefined|LaTeX Error|Emergency stop', log)

# Exercise the editor recipe with SyncTeX, using the same installed arguments.
# A source edit triggers a rebuild; changing flags alone can leave an already
# up-to-date latexmk target untouched.
tex = base.with_suffix('.tex')
tex.write_bytes(tex.read_bytes() + b'\n% Source edit for the editor build check.\n')
editor = json.loads((STAGE / 'vscode-settings.json').read_text(encoding='utf-8'))
args = editor['latex-workshop.latex.tools'][0]['args']
args = [arg.replace('%DOC%', str(base)) for arg in args]
editor_run = subprocess.run([binary, *args], cwd=check, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=120)
(STAGE / 'verified-editor-build.log').write_bytes(editor_run.stdout)
assert editor_run.returncode == 0, editor_run.stdout.decode('cp932', errors='replace')[-5000:]
synctex = base.with_suffix('.synctex.gz')
assert synctex.is_file() and synctex.stat().st_size > 0, 'SyncTeX was not created'
result = {
    'check_directory': str(check),
    'latexmk': binary,
    'global_rc': str(Path(os.environ['USERPROFILE']) / '.latexmkrc'),
    'local_rc_present': False,
    'global_build_exit_code': run.returncode,
    'editor_build_exit_code': editor_run.returncode,
    'verified_tools': ['uplatex', 'upbibtex', 'upmendex', 'dvipdfmx'],
    'undefined_references_or_citations': False,
    'synctex': True,
    'pdf_bytes': base.with_suffix('.pdf').stat().st_size,
}
(STAGE / 'verification.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
