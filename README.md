# 漸化式の超体系的解説

このRepositoryは「基本-new」と「発展-new」の原稿を管理します。出版基盤が正式版としてビルド・配布するのは、付録を含む最新版の **発展-new** です。基本版のPDFも従来どおり原稿ディレクトリに残しますが、正式ReleaseのPDFには含めません。

## ローカルでビルド

TeX Live 2025以降を用意し、次を実行します。

```bash
cd 発展-new
latexmk 漸化式の超体系的解説.tex
```

GitHub Actionsでは `texlive/texlive:TL2025-historic` のmanifest digestを固定して同じ入口をビルドします。生成PDFはGitで追跡せず、正式版Releaseのassetとして保存します。

## GitHubでの初期設定

コピー先RepositoryをPublicにしたうえで、[出版基盤のセットアップ手順](docs/setup.md)に従って Pages、Immutable releases、Tag rulesetを設定してください。最初のReleaseを作る前に設定を完了してください。

日常の執筆から正式版公開まで、GitHubのWeb画面で操作できます。`main`への変更でBuildが走ります。正式版にするときはActions → **Release** → **Run workflow** を開き、`main`を選択して版番号（例: `v1.0.3`）を入力します。Workflowがその時点の`main`をBuildし、PDFとSHA-256を検証してReleaseを作成します。成功後、Pages Workflowが公開済みのPDFを配信します。

GitHubのReleases画面から先にReleaseを作らないでください。正式版タグはRelease Workflowが作成します。公開済みタグは再利用できないため、毎回まだ使っていない版番号を指定してください。

本棚に表示する版番号は、ReleaseとPagesの公開が成功した後、[数学書の本棚](https://github.com/mas256/math-textbooks)の`books.json`で更新します。

## ブランチ

- `main`: 次に公開する最新版の執筆線
- `release/N.x`: 第N版の保守線。必要になったとき、系列の最新Release Tagから作成

## ライセンス

このRepositoryにはライセンスを追加していません。原稿、図、PDFの利用条件を決めるまで、`LICENSE` は置きません。

## 最新版（開発中）

`main`へのpush時にBuild WorkflowがPDFを作成し、ビルド・参照・フォント検査に成功した場合だけ、
run番号ごとに固有の`latest-build-<run number>` Pre-releaseへ保存します。公開済みassetは変更せず、Pagesの`latest.pdf`だけを成功ビルドに合わせて更新します。
正式版のReleaseとPagesの`book.pdf`は従来どおりです。
ビルド失敗時は直前の最新版PDFを維持し、古いrunの再実行による巻き戻しも防ぎます。
最新版は[数学書の本棚](https://mas256.github.io/math-textbooks/)から閲覧できます。
