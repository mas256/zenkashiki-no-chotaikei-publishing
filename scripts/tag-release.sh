#!/usr/bin/env bash
# 正式版Tagを作成してPushする。Tag前の確認を行う著者向けの安全装置(強制ではない)。
# 使い方: scripts/tag-release.sh vX.Y.Z [--yes]
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$here/lib/common.sh"

tag="${1:-}"
assume_yes=false
[ "${2:-}" = "--yes" ] && assume_yes=true

[ -n "$tag" ] || die "使い方: $0 vX.Y.Z [--yes]"
is_strict_semver "$tag" || die "正式版Tagの形式ではありません(vMAJOR.MINOR.PATCH): $tag"

git fetch origin --tags --quiet

if git rev-parse -q --verify "refs/tags/$tag" > /dev/null || [ -n "$(git ls-remote --tags origin "refs/tags/$tag")" ]; then
  die "Tag $tag は既に存在します(Tagは削除・再利用しません)"
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
case "$branch" in
  main) ;;
  release/*)
    series="${branch#release/}"
    series_major="${series%%.*}"
    tag_major="${tag#v}"; tag_major="${tag_major%%.*}"
    [ "$series_major" = "$tag_major" ] || die "ブランチ $branch に対してMAJORが合いません: $tag"
    ;;
  *) die "main または release/* で実行してください(現在: $branch)" ;;
esac

if ! git diff --quiet || ! git diff --cached --quiet; then
  die "未コミットの変更があります"
fi

sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"
[ "$sha" = "$remote_sha" ] || die "HEAD が origin/$branch と一致しません。Pushしてください"

ok_runs="$(gh run list --workflow build.yml --commit "$sha" --status success --json databaseId --jq 'length')"
if [ "$ok_runs" -lt 1 ]; then
  echo "このCommitに成功した build.yml のRunがありません。状況:" >&2
  gh run list --workflow build.yml --commit "$sha" --json status,conclusion,url \
    --jq '.[] | "  \(.status) \(.conclusion) \(.url)"' >&2 || true
  die "Buildが完了して成功してから、もう一度実行してください"
fi

latest="$(latest_release)"
if [ -n "$latest" ]; then
  top="$(printf '%s\n%s\n' "$latest" "$tag" | { grep -E "$STRICT_SEMVER_RE" || true; } | sort -V | tail -n 1)"
  if [ "$top" != "$tag" ]; then
    echo "注意: $tag は最新正式版 $latest より小さい版です。公開されますが、Pagesは更新されません。"
  fi
fi

echo "Tag:    $tag"
echo "Branch: $branch"
echo "Commit: $sha"
if ! $assume_yes; then
  read -r -p "このCommitに Tag を作成して Push します。よろしいですか? [y/N] " answer
  [ "$answer" = "y" ] || die "中止しました"
fi

git tag -a "$tag" -m "$tag" "$sha"
git push origin "refs/tags/$tag"
echo "Push しました。Actions の Release ワークフローを確認してください。"
