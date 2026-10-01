# 公開版と版番号の整理

更新日: 2026-10-01

## リポジトリの役割

- 原稿・ビルド・正式Releaseの管理先: [zenkashiki-no-chotaikei-publishing](https://github.com/mas256/zenkashiki-no-chotaikei-publishing)
- [math-textbooks](https://github.com/mas256/math-textbooks) は数学書の本棚です。原稿や正式PDFの保管先ではなく、各書籍の現在の正式版へのリンクを一覧表示します。
- 教科書ごとに原稿・Tag・Releaseを1つの教科書Repositoryで管理します。

## 現在の正式版

| 項目 | 値 |
|---|---|
| 書名 | 漸化式の超体系的解説 |
| 版 | 第1版 `v1.3.0` |
| Release | [v1.3.0](https://github.com/mas256/zenkashiki-no-chotaikei-publishing/releases/tag/v1.3.0) |
| TagのCommit | `02c6bee8b662e480d5b85868d97a9284db83257b` |
| 正式PDF | [book.pdf](https://mas256.github.io/zenkashiki-no-chotaikei-publishing/book.pdf)（92ページ） |
| 本棚の表示 | `math-textbooks/books.json` は `v1.3.0` |

`v1.3.0` を現在の正式版として案内します。`v1.2.1` と同じソースCommitから作られたReleaseですが、ReleaseとPDFは別の履歴として保持しています。両ReleaseのPDFは別々にビルドされており、SHA-256は異なります。

## 版履歴

| Tag / Release | 状態 | 整理 |
|---|---|---|
| `v1.0.0` | Tagのみ | 公開ReleaseとPDFがないため、正式版には数えません。 |
| `v1.0.1` | 正式Release | 旧版として保存しています。 |
| `v1.0.2` | テストRelease | PDFとSHA-256がありません。正式版ではなく、版番号も再利用しません。 |
| `v1.1.0` | 未公開 | Tag・Releaseはありません。 |
| `v1.2.0` | 正式Release | 第4章の実践演習を1段組で出力した版です。111ページ。 |
| `v1.2.1` | 正式Release | 第4章の実践演習を2段組の範囲へ戻した修正版です。`v1.3.0` と同じCommitです。 |
| `v1.3.0` | **現行正式Release** | `v1.2.1` の内容を含む現在の案内先です。92ページ。 |

公開済みのTagとReleaseは履歴として残し、書き換えません。正式版の選定では、公開済みReleaseのうち、厳密な `vMAJOR.MINOR.PATCH` 形式で、対応するPDFと `.pdf.sha256` が1組そろったものだけを対象にします。その中のSemVer最大が最新版です。この規則では `v1.0.0`、PDFのない `v1.0.2`、`latest-build-*` のPre-releaseは正式版になりません。

## 111ページから92ページになった理由

`v1.2.0` では、第4章の「実践演習」を読み込む前に `\end{multicols*}` がありました。そのため実践演習全体が1段組になり、ページ数が増えていました。`v1.2.1` では基本版・発展版の両方で `\end{multicols*}` を実践演習の後ろへ移し、2段組の範囲に含めました。これが19ページ減った主な理由です。

`v1.3.0` は `v1.2.1` と同じソースCommit `02c6bee8b662e480d5b85868d97a9284db83257b` を指すため、同じレイアウトの92ページです。

## 次回の正式Release

1. `main` の原稿を確認し、正式版の版番号を1つ決めます。現在の `v1.3.0` より大きく、未使用のSemVer番号を使います。
2. Actionsの **Release** Workflowを `main` から1回だけ実行します。Release画面から手動でTagやReleaseを先に作りません。前の実行が終わる前に別の版番号のReleaseを開始しません。
3. PDF・SHA-256の検査とPages公開が成功した後に、本棚の `books.json` の `version` を更新します。
4. `book.pdf` は正式版、`latest.pdf` と `latest-build-*` は成功した開発ビルドです。本棚の正式版番号には開発ビルドの番号を入れません。