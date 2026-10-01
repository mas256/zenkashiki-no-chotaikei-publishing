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

# PagesとRelease Workflowで共通に使う、PDFとチェックサムがそろった正式版一覧。
# --jqはページごとに実行されるため、ここでは各Releaseを一行ずつ出力する。
formal_releases() {
  gh api --paginate "repos/${GH_REPO:?}/releases?per_page=100" --jq '
    def complete_pdf:
      [.assets[]? | .name] as $assets
      | [$assets[] | select(endswith(".pdf"))] as $pdfs
      | [$assets[] | select(endswith(".pdf.sha256"))] as $checksums
      | (($pdfs | length) == 1 and ($checksums | length) == 1
         and $checksums[0] == ($pdfs[0] + ".sha256"));
    .[]
    | select(.draft == false and .prerelease == false)
    | select(.tag_name | test("^v[0-9]+\\.[0-9]+\\.[0-9]+$"))
    | select(complete_pdf)
    | {tagName: .tag_name, publishedAt: .published_at}
  '
}

# 全ページの正式版をまとめて比較し、最大のSemVerを返す。
# 存在しなければ空文字を返す。ghの失敗は呼び出し側に伝わる。
latest_release() {
  formal_releases | jq -r '.tagName' | sort -V | tail -n 1
}

# 全ページの成功ビルドから、run番号が最大のPre-releaseを返す。
latest_build_release() {
  gh api --paginate "repos/${GH_REPO:?}/releases?per_page=100" --jq '
    .[]
    | select(.draft == false and .prerelease == true)
    | select(.tag_name | test("^latest-build-[0-9]+$"))
    | [.assets[]? | .name] as $assets
    | select(($assets | index("main.pdf")) != null
             and ($assets | index("main.pdf.sha256")) != null
             and ($assets | index("latest-build.json")) != null)
    | .tag_name
  ' | sort -V | tail -n 1
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
