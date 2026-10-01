#!/usr/bin/env bash
# 正式版とは別の、main の最新成功ビルドを永続的に公開する。
set -euo pipefail
: "${GH_REPO:?}" "${GITHUB_SHA:?}" "${GITHUB_RUN_NUMBER:?}" "${GITHUB_RUN_ID:?}"
latest_dir="${BUILD_DIR:-latest-out}"
latest_tag="latest-build"

# 公開操作の前に、ビルド成果物と対象コミットを確認する。
python3 - "$latest_dir" <<'PYVERIFY'
import json, os, sys
from pathlib import Path
path = Path(sys.argv[1])
assert (path / "main.pdf").read_bytes().startswith(b"%PDF-"), "Invalid PDF"
info = json.loads((path / "build-info.json").read_text())
assert info["commit"] == os.environ["GITHUB_SHA"], "Build commit mismatch"
info.update(run_number=int(os.environ["GITHUB_RUN_NUMBER"]),
            run_id=int(os.environ["GITHUB_RUN_ID"]))
(path / "latest-build.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
PYVERIFY
(cd "$latest_dir" && sha256sum main.pdf > main.pdf.sha256 && sha256sum -c main.pdf.sha256)

# 手動で古いrunを再実行しても、最新版を古いコミットへ戻さない。
if gh release view "$latest_tag" --json isPrerelease,isDraft > latest-release.json; then
  python3 - <<'PYRELEASE'
import json
release = json.load(open("latest-release.json"))
assert release["isPrerelease"], "latest-build must be a prerelease"
PYRELEASE
  if [ "$(python3 -c 'import json; print(json.load(open("latest-release.json"))["isDraft"])')" = False ]; then
    mkdir -p previous-latest
    gh release download "$latest_tag" --pattern latest-build.json --dir previous-latest
    previous_run="$(python3 -c 'import json; print(json.load(open("previous-latest/latest-build.json"))["run_number"])')"
    if [ "$previous_run" -gt "$GITHUB_RUN_NUMBER" ]; then
      echo "Skip older build: $GITHUB_RUN_NUMBER < $previous_run"
      exit 0
    fi
  fi
else
  gh release create "$latest_tag" --target "$GITHUB_SHA" --draft --prerelease --latest=false \
    --title '最新版（開発中）' --notes '初回ビルドの公開準備中です。'
fi

gh release upload "$latest_tag" \
  "$latest_dir/main.pdf" "$latest_dir/main.pdf.sha256" \
  "$latest_dir/build-info.json" "$latest_dir/latest-build.json" --clobber

# 公開前にアップロードされたPDFのチェックサムを検証する。
mkdir -p verify-latest
gh release download "$latest_tag" --pattern main.pdf --pattern main.pdf.sha256 --dir verify-latest
(cd verify-latest && sha256sum -c main.pdf.sha256)

cat > latest-notes.md <<EOF
mainへのpush後、ビルドと参照・フォントの検査に成功した最新版です。正式版ではありません。

対象コミット: $GITHUB_SHA
ビルド: https://github.com/$GH_REPO/actions/runs/$GITHUB_RUN_ID

ビルドが失敗した場合は、直前に成功したPDFを維持します。
EOF
gh release edit "$latest_tag" --draft=false --prerelease --latest=false \
  --title '最新版（開発中）' --notes-file latest-notes.md

gh api --method PATCH "repos/$GH_REPO/git/refs/tags/$latest_tag" \
  -f sha="$GITHUB_SHA" -F force=true > /dev/null
