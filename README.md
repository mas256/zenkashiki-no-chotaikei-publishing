# 漸化式の超体系的解説

このRepositoryは「基本-new」と「発展-new」の原稿を管理します。出版基盤が正式版としてビルド・配布するのは、付録を含む最新版の **発展-new** です。基本版のPDFも従来どおり原稿ディレクトリに残しますが、正式ReleaseのPDFには含めません。

公開版の正は、このRepositoryの正式Releaseです。現在の正式版・Tag・本棚の表示・過去の版履歴は[公開版と版番号の整理](docs/release-status.md)にまとめています。

## ローカルでビルド

TeX Live 2025以降を用意し、次を実行します。

```bash
cd 発展-new
latexmk 漸化式の超体系的解説.tex
```

GitHub Actionsでは TeX Live 2025 の固定アーカイブ（`tlnet-final`）から必要なパッケージだけを用意し、同じ入口をビルドします。インストール済み環境をキャッシュするため、2回目以降は大きなコンテナの取得や再インストールが不要です。生成PDFはGitで追跡せず、正式版Releaseのassetとして保存します。

PDFの目次は章・節・項（`chapter` から `subsubsection`）までクリックでき、本文中の見出し参照もリンクになります。例題・演習問題の番号から対応する解答へ、方針・解答・解法の番号から元の問題へ戻れます。番号のない例題を含め、例題の【例題】・【方針】・【解答】・【解法】の見出しにも同じリンクを付けています。リンク設定は両版共通の `tex/book-links.tex` にあります。

## GitHubでの初期設定

コピー先RepositoryをPublicにしたうえで、[出版基盤のセットアップ手順](docs/setup.md)に従って Pages、Immutable releases、Tag rulesetを設定してください。最初のReleaseを作る前に設定を完了してください。

日常の執筆から正式版公開まで、GitHubのWeb画面で操作できます。`main`の原稿・共通TeX・ビルド環境への変更でBuildが走ります。連続した変更では古いビルドを中止し、最新の変更を優先します。正式版にするときはActions → **Release** → **Run workflow** を開き、`main`を選択して版番号を入力します（現行 `v1.3.3` の次の例は `v1.3.4`）。Workflowがその時点の`main`をBuildし、PDFとSHA-256を検証してReleaseを作成します。成功後、Pages Workflowが公開済みのPDFを配信します。

Release Workflowは一度に1つだけ実行します。前の実行・Pages公開が終わってから次の正式版を作成してください。GitHubのReleases画面から先にReleaseを作らないでください。正式版タグはRelease Workflowが作成します。公開済みタグは再利用できないため、毎回まだ使っていない版番号を指定してください。

本棚の版番号とPDFリンクは、Pages公開後に `catalog.json` から自動取得します。

## ブランチ

- `main`: 次に公開する最新版の執筆線
- `release/N.x`: 第N版の保守線。必要になったとき、系列の最新Release Tagから作成

## ライセンス

このRepositoryにはライセンスを追加していません。原稿、図、PDFの利用条件を決めるまで、`LICENSE` は置きません。

## 最新版（開発中）

`main`へのpush時にBuild WorkflowがPDFを作成し、ビルド・参照・フォント検査に成功するとActions成果物 `latex-build` が作られます。Pages Workflowは最新の成功したmainビルドのPDFを `latest.pdf` として配信します。`latest.pdf.sha256` も同じ場所から取得できます。

ビルドが失敗した場合はPagesを更新せず、直前に公開した開発PDFを維持します。開発ビルドごとのTagやPre-releaseは新たに作りません。正式版のReleaseとPagesの `book.pdf` は別に管理し、正式版番号も変わりません。

正式版と開発中のPDFは[数学書の本棚](https://mas256.github.io/math-textbooks/)から閲覧できます。教科書の紹介ページからも両方を開けます。

## PagesのPDFファイル名と本棚への公開情報

Pagesの正式版PDFは `タイトル-vMAJOR.MINOR.PATCH.pdf`、開発中PDFは `latest-タイトル-vMAJOR.MINOR.PATCH.pdf` です。タイトルは公開Release時点の `book.yml`、版番号は配信する正式Releaseから取得します。開発中PDFの名前も現在の正式Release番号を使い、内容の更新はSHA-256クエリで区別します。

Pages WorkflowはPDFと一緒に `catalog.json` を公開します。正式版はReleaseの公開日時、latestは成功ビルドの `built_at` を最終更新日時とし、再配信では変更しません。本棚はこの情報から版番号・更新日時・PDFリンクを自動取得するため、`books.json` の版番号更新は不要です。

既存リンクとの互換性のため `book.pdf` と `latest.pdf` も残しますが、紹介ページと本棚はタイトル・版番号付きのPDFを案内します。公開済みReleaseのassetやTagは変更しません。
