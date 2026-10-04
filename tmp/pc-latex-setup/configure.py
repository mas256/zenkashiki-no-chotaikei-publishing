"""Stage and apply the user's existing Japanese LaTeX build defaults."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from datetime import datetime, timedelta, timezone

STAGE = Path(__file__).resolve().parent
USER = Path(os.environ['USERPROFILE'])
APPDATA = Path(os.environ['APPDATA'])
RECIPE = 'latexmk (latexmkrc)'
LATEX_KEYS = [
    'latex-workshop.latex.recipe.default',
    'latex-workshop.latex.recipes',
    'latex-workshop.latex.tools',
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def editor_settings(original):
    settings = json.loads(original.decode('utf-8-sig'))
    old_settings = json.loads(original.decode('utf-8-sig'))
    settings[LATEX_KEYS[0]] = RECIPE
    settings[LATEX_KEYS[1]] = [{'name': RECIPE, 'tools': [RECIPE]}]
    settings[LATEX_KEYS[2]] = [{
        'name': RECIPE,
        'command': 'latexmk',
        'args': ['-cd', '-synctex=1', '-interaction=nonstopmode',
                 '-file-line-error', '%DOC%'],
    }]
    profile_keys = list(settings.get('workbench.settings.applyToAllProfiles', []))
    for key in LATEX_KEYS:
        if key not in profile_keys:
            profile_keys.append(key)
    settings['workbench.settings.applyToAllProfiles'] = profile_keys
    allowed = {*LATEX_KEYS, 'workbench.settings.applyToAllProfiles'}
    assert {k: v for k, v in settings.items() if k not in allowed} == {
        k: v for k, v in old_settings.items() if k not in allowed
    }, 'Unrelated editor settings changed'
    return (json.dumps(settings, ensure_ascii=False, indent=4) + '\n').encode('utf-8')


def prepare():
    entries = []
    rc = (STAGE / 'latexmkrc').read_bytes()
    targets = [(USER / '.latexmkrc', 'home-dot-latexmkrc', rc),
               (USER / 'latexmkrc', 'home-latexmkrc', rc)]
    for name, editor in [('vscode-settings.json', 'Code'),
                         ('cursor-settings.json', 'Cursor')]:
        target = APPDATA / editor / 'User' / 'settings.json'
        if target.is_file():
            targets.append((target, name, editor_settings(target.read_bytes())))
    for target, name, replacement in targets:
        original = target.read_bytes() if target.exists() else None
        (STAGE / name).write_bytes(replacement)
        entries.append({'target': str(target), 'staged': name,
                        'original_sha256': digest(original) if original is not None else None,
                        'replacement_sha256': digest(replacement)})
        print(f'Prepared: {target}')
    (STAGE / 'manifest.json').write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def apply():
    entries = json.loads((STAGE / 'manifest.json').read_text(encoding='utf-8'))
    # Validate every original and staged file before making any external change.
    for entry in entries:
        target = Path(entry['target'])
        original = target.read_bytes() if target.exists() else None
        actual = digest(original) if original is not None else None
        if actual != entry['original_sha256']:
            raise RuntimeError(f'Settings changed since preparation: {target}')
        if digest((STAGE / entry['staged']).read_bytes()) != entry['replacement_sha256']:
            raise RuntimeError(f'Staged file changed: {entry["staged"]}')
    timestamp = datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d-%H%M%S')
    backup = USER / '.latex-build-backups' / timestamp
    backup.mkdir(parents=True, exist_ok=False)
    for entry in entries:
        target = Path(entry['target'])
        if target.exists():
            shutil.copy2(target, backup / entry['staged'])
    shutil.copy2(STAGE / 'manifest.json', backup / 'manifest.json')
    applied = []
    try:
        for entry in entries:
            target = Path(entry['target'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((STAGE / entry['staged']).read_bytes())
            applied.append(entry)
            if digest(target.read_bytes()) != entry['replacement_sha256']:
                raise RuntimeError(f'Could not verify installed file: {target}')
            print(f'Applied: {target}')
    except Exception:
        for entry in reversed(applied):
            target = Path(entry['target'])
            if entry['original_sha256'] is not None:
                shutil.copy2(backup / entry['staged'], target)
            else:
                target.unlink(missing_ok=True)
        raise
    (STAGE / 'applied.json').write_text(
        json.dumps({'backup': str(backup), 'files': entries}, ensure_ascii=False, indent=2)
        + '\n', encoding='utf-8')
    print(f'Backup: {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'apply'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else apply()
