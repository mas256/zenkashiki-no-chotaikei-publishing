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

日常の執筆はCommitとPushだけです。`main` または `release/**` へのPushでBuildが走ります。Build成功後、正式版を作るCommitに対して次を実行します。

```bash
bash scripts/tag-release.sh v1.0.0
```

Tagの形式は `vMAJOR.MINOR.PATCH` です。Tag Push後、Release WorkflowがPDFとSHA-256を検証して公開し、Pages Workflowが公開済みReleaseのうち最大の版を配信します。

## ブランチ

- `main`: 次に公開する最新版の執筆線
- `release/N.x`: 第N版の保守線。必要になったとき、系列の最新Release Tagから作成

## ライセンス

このRepositoryにはライセンスを追加していません。原稿、図、PDFの利用条件を決めるまで、`LICENSE` は置きません。
