#!/usr/bin/env bash
# 共通関数。`source` して使う。呼び出し側で `set -euo pipefail` を有効にすること。

STRICT_SEMVER_RE='^v[0-9]+\.[0-9]+\.[0-9]+$'

die() {
  echo "error: $*" >&2
  exit 1
}

is_strict_semver() {
  [[ "$1" =~ $STRICT_SEMVER_RE ]]
}

# 公開済みRelease(Draftでなく、Pre-releaseでなく、正式版Tag)のSemVer最大を返す。
# 存在しなければ空文字を返す。gh の失敗は呼び出し側に伝わる。
latest_release() {
  gh api --paginate "repos/${GH_REPO:?}/releases?per_page=100" \
    --jq '.[] | select(.draft == false and .prerelease == false) | .tag_name' |
    { grep -E "$STRICT_SEMVER_RE" || true; } |
    sort -V |
    tail -n 1
}

# 引数のTagが「公開済みRelease ∪ {そのTag}」のSemVer最大なら成功(終了コード0)。
is_max_semver() {
  local tag="$1" latest top
  latest="$(latest_release)"
  top="$(printf '%s\n%s\n' "$latest" "$tag" | { grep -E "$STRICT_SEMVER_RE" || true; } | sort -V | tail -n 1)"
  [ "$top" = "$tag" ]
}

# Tagが指すCommit SHAを返す(注釈付きTagも解決する)。
tag_commit() {
  local repo="$1" tag="$2" type sha
  read -r type sha < <(gh api "repos/$repo/git/ref/tags/$tag" --jq '.object | "\(.type) \(.sha)"')
  if [ "$type" = "tag" ]; then
    sha="$(gh api "repos/$repo/git/tags/$sha" --jq '.object.sha')"
  fi
  echo "$sha"
}
