#!/usr/bin/env bash
# dist/ にある最新正式版のPDFから、Pagesに載せる site/ を作る。
# 必要な環境変数: GH_TOKEN, GH_REPO, LATEST(最新正式版のTag)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
# shellcheck source=lib/common.sh
source "$here/lib/common.sh"

: "${GH_REPO:?}" "${LATEST:?}"

shopt -s nullglob
python3 "$here/verify-release-assets.py" dist
pdfs=()
mobile_pdfs=()
for pdf in dist/*.pdf; do
  if [[ "$pdf" == *-mobile.pdf ]]; then mobile_pdfs+=("$pdf"); else pdfs+=("$pdf"); fi
done

rm -rf site
mkdir -p site
cp "${pdfs[0]}" site/book.pdf
if [ "${#mobile_pdfs[@]}" -eq 1 ]; then cp "${mobile_pdfs[0]}" site/book-mobile.pdf; fi

# book.yml は最新正式版の時点のものを使う
gh api -H 'Accept: application/vnd.github.raw+json' \
  "repos/$GH_REPO/contents/book.yml?ref=$LATEST" > book.at-tag.yml

formal_releases > releases.ndjson
python3 - <<'PY' > releases.json
import json
from pathlib import Path
rows = [json.loads(line) for line in Path("releases.ndjson").read_text().splitlines() if line.strip()]
print(json.dumps(rows, ensure_ascii=False))
PY

python3 "$here/render_index.py" \
  --book book.at-tag.yml \
  --releases releases.json \
  --template "$root/.github/pages/index.template.html" \
  --tag "$LATEST" \
  --repo "$GH_REPO" \
  --out site/index.html

ls -l site
