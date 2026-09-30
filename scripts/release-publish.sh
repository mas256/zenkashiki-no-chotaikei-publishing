#!/usr/bin/env bash
# Draft Releaseを作成し、asset・SHA-256を検証してから公開する。
# 必要な環境変数:
#   GH_TOKEN, GH_REPO  gh の認証とRepository (owner/name)
#   TAG                公開するTag (vX.Y.Z)
#   COMMIT             Buildの対象にしたCommit SHA
#   BUILD_DIR          main.pdf と build-info.json があるディレクトリ
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$here/lib/common.sh"

: "${GH_REPO:?}" "${TAG:?}" "${COMMIT:?}" "${BUILD_DIR:?}"
is_strict_semver "$TAG" || die "正式版Tagの形式ではありません: $TAG"
[ -f "$BUILD_DIR/main.pdf" ] || die "$BUILD_DIR/main.pdf がありません"
[ -f "$BUILD_DIR/build-info.json" ] || die "$BUILD_DIR/build-info.json がありません"

repo_name="${GH_REPO#*/}"
asset="${repo_name}-${TAG}.pdf"
major="${TAG#v}"
major="${major%%.*}"
work="$(mktemp -d)"

list_draft_ids() {
  gh api --paginate "repos/$GH_REPO/releases?per_page=100" \
    --jq ".[] | select(.draft == true and .tag_name == \"$TAG\") | .id"
}

# 1. asset と .sha256 を作る
cp "$BUILD_DIR/main.pdf" "$work/$asset"
(cd "$work" && sha256sum "$asset" > "$asset.sha256")
sha="$(cut -d' ' -f1 "$work/$asset.sha256")"

# 2. Release Notes(人が読む記録。SHA-256の正は .sha256 asset)
built_at="$(jq -r '.built_at' "$BUILD_DIR/build-info.json")"
tex="$(jq -r '.tex' "$BUILD_DIR/build-info.json")"
dvipdfmx="$(jq -r '.dvipdfmx' "$BUILD_DIR/build-info.json")"
image="$(jq -r '.image' "$BUILD_DIR/build-info.json")"
fonts="$(jq -r '.fonts | join(", ")' "$BUILD_DIR/build-info.json")"
cat > "$work/notes.md" <<NOTES
第${major}版 \`${TAG}\`

| 項目 | 値 |
|---|---|
| Tag | \`${TAG}\` |
| Commit | \`${COMMIT}\` |
| Build日時(UTC) | ${built_at} |
| TeX | ${tex} |
| dvipdfmx | ${dvipdfmx} |
| Build image | \`${image}\` |
| 埋め込みフォント | ${fonts} |
| PDF | \`${asset}\` |
| PDF SHA-256 | \`${sha}\` |

SHA-256の正は、同梱の \`${asset}.sha256\` です(このNotesは公開後も編集できます)。
NOTES

# 3. 同じTagのDraftが残っていれば破棄する(Tagは削除しない)
while read -r old_id; do
  [ -n "$old_id" ] || continue
  echo "残存Draftを破棄: id=$old_id"
  gh api -X DELETE "repos/$GH_REPO/releases/$old_id" > /dev/null
done < <(list_draft_ids)

# 4. Draftとして作成し、assetを添付する
gh release create "$TAG" "$work/$asset" "$work/$asset.sha256" \
  --draft --verify-tag \
  --title "第${major}版 ${TAG}" --notes-file "$work/notes.md"

mapfile -t draft_ids < <(list_draft_ids)
[ "${#draft_ids[@]}" -eq 1 ] || die "Draftがちょうど1件ではありません: ${#draft_ids[@]}件"
id="${draft_ids[0]}"

# 5. Draftのassetを再取得して検証する
verify_dir="$work/verify"
mkdir -p "$verify_dir"
mapfile -t rows < <(gh api "repos/$GH_REPO/releases/$id" \
  --jq '.assets[] | [.id, .name, (.digest // "")] | @tsv')
[ "${#rows[@]}" -eq 2 ] || die "assetが2件ではありません: ${#rows[@]}件"
for row in "${rows[@]}"; do
  IFS=$'\t' read -r aid aname adigest <<< "$row"
  gh api -H 'Accept: application/octet-stream' \
    "repos/$GH_REPO/releases/assets/$aid" > "$verify_dir/$aname"
  if [ "$aname" = "$asset" ]; then
    if [ -n "$adigest" ]; then
      [ "$adigest" = "sha256:$sha" ] || die "APIのdigestが一致しません: $adigest != sha256:$sha"
    else
      echo "::warning::Draftのassetにdigestがありません。公開後に確認してください"
    fi
  fi
done
[ -f "$verify_dir/$asset" ] && [ -f "$verify_dir/$asset.sha256" ] || die "期待するassetがありません"
cmp "$work/$asset.sha256" "$verify_dir/$asset.sha256" || die ".sha256 が一致しません"
(cd "$verify_dir" && sha256sum -c "$asset.sha256")

# 6. TagがBuild対象のCommitを指したままか確認する
current="$(tag_commit "$GH_REPO" "$TAG")"
[ "$current" = "$COMMIT" ] || die "Tagが移動しています: $current != $COMMIT"

# 7. 公開する。最大バージョンのときだけ Latest にする
if is_max_semver "$TAG"; then make_latest=true; else make_latest=false; fi
gh api -X PATCH "repos/$GH_REPO/releases/$id" -F draft=false -f make_latest="$make_latest" > /dev/null
echo "公開しました: $TAG (make_latest=$make_latest)"

# 8. 公開後の確認
gh api --paginate "repos/$GH_REPO/releases?per_page=100" \
  --jq '.[] | select(.draft == false and .prerelease == false) | .tag_name' | grep -qx "$TAG" \
  || die "公開後の一覧に $TAG がありません"
