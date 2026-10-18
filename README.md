# 漸化式の体系と解法

このRepositoryは「基本-new」と「発展-new」の原稿を管理します。出版基盤が正式版としてビルド・配布するのは、付録を含む最新版の **発展-new** です。基本版のPDFも従来どおり原稿ディレクトリに残しますが、正式ReleaseのPDFには含めません。

公開版の正は、このRepositoryの正式Releaseです。現在の正式版・Tag・本棚の表示・過去の版履歴は[公開版と版番号の整理](docs/release-status.md)にまとめています。

## ローカルでビルド

TeX Live 2025以降を用意し、次を実行します。

```bash
cd 発展-new
latexmk 漸化式の超体系的解説.tex
```

GitHub Actionsでは TeX Live 2025 の固定アーカイブ（`tlnet-final`）から必要なパッケージだけを用意し、同じ原稿からA4版とスマホ版をビルドします。インストール済み環境をキャッシュするため、2回目以降は再インストールが不要です。生成PDFはGitで追跡せず、正式版Releaseのassetとして保存します。

PDFの目次は章・節・項（`chapter` から `subsubsection`）までクリックでき、本文中の見出し参照もリンクになります。例題・演習問題の番号から対応する解答へ、方針・解答・解法の番号から元の問題へ戻れます。番号のない例題を含め、例題の【例題】・【方針】・【解答】・【解法】の見出しにも同じリンクを付けています。リンク設定は両版共通の `tex/book-links.tex` にあります。

現在の原稿は、第2章「漸化式の解法」で数列・漸化式の導入から始め、計算や用語を第5章「用語と公式」で確認する構成です。旧第2章の配置変更と章番号の対応は[参照資料の統合](docs/chapter-reference-reorganization-2026-10-11.md)にまとめています。

原稿は、親のTeXファイルと子ファイル用の `sections/`・`subsections/`・`subsubsections/` を分けて配置しています。子ファイルを持たない項目のTeXファイルは、対応する階層のフォルダへ直接置きます。[原稿ファイル名と章構成の対応](docs/manuscript-paths-2026-10-14.md)に構成例と入口ファイルをまとめています。

本文のカンマ・ピリオドに続くインライン数式・数字・参照（`\ref`、`\sectionref`、`\chapterref`、`\headingref` とそのスター付き形式）の前には、`latexmk` でのビルド時に薄い空白を自動挿入します。原稿に `\,` を手書きする必要はありません。数式内部の空白、小数点、桁区切り、URL、図の座標は保持します。処理済みの入力は `out/tex-spacing/` に生成し、編集対象は元の原稿のままです。SyncTeXの参照先も元の原稿へ戻します。

具体例から別解・解釈へ進む順序と、共通原理を各解法で使う方針は[理解の順序と解法のつながりの改訂](docs/connected-narrative-revision-2026-10-12.md)にまとめています。

現行PDFの再レビューを受けた説明順序・数学的条件・図とリンクの改訂は[具体例から構造へ進む改訂](docs/reader-centered-revision-2026-10-12.md)にまとめています。

## スマホ版

付録を含む発展-newの全文を、縦160mm × 横90mm・四辺8mmの余白・1段組みで読む版です。本文の文字サイズと数式のスタイルは本編と同じで、ディスプレイ数式のインデントは全角1文字（`1zw`）です。長い数式は等号や項のまとまりで改行し、目次・柱・図も紙幅に収めます。

```bash
python3 scripts/build-mobile.py
```

リポジトリ直下で実行します。スクリプトが `out/mobile/mobile.tex` を生成し、A4版の入口原稿をスマホ幅でビルドします。出力は `out/mobile/mobile.pdf` です。本文・付録・参照リンク・組版設定はA4原稿に集約し、スマホ用の本文コピーは管理しません。旧入口ソース、完成PDF、専用設定ファイル、確認用画像は削除しました。

改行の切り替えは共通原稿中の `\BookMathLayout{本編}{スマホ版}` で管理します。等号、項のまとまり、行列の並びなど、意味の区切りで折り返します。文字や数式を縮めて収める方法は使いません。図は必要なときだけ紙幅に合わせます。

スマホ版は、文字サイズを保ったまま行間の余白を従来の約6割にしています。本文10ptの行送りは16.8ptから14.08ptにし、段落・数式・箇条書き・見出し・要点ボックスの縦の余白も詰めます。これらの設定は入口原稿の `\BookMobile` 分岐にまとめ、A4版には適用しません。

CIは両版を生成した後、ログのはみ出し・未解決参照、全ページの寸法、フォント、式番号・演習・用語のリンクを検査します。はみ出しがあればファイル名・行番号・幅を表示し、公開を止めます。ローカルでも生成後に同じ検査ができます。

```bash
python3 scripts/verify-tex-layout.py '発展-new/漸化式の超体系的解説.log' out/mobile/mobile.log
```

## GitHubでの初期設定

コピー先RepositoryをPublicにしたうえで、[出版基盤のセットアップ手順](docs/setup.md)に従って Pages、Immutable releases、Tag rulesetを設定してください。最初のReleaseを作る前に設定を完了してください。

日常の執筆から正式版公開まで、GitHubのWeb画面で操作できます。`main`の原稿・共通TeX・ビルド環境への変更でBuildが走ります。連続した変更では古いビルドを中止し、最新の変更を優先します。正式版にするときはActions → **Release** → **Run workflow** を開き、`main`を選択して未使用の版番号を入力します。Workflowがその時点の`main`から両版をBuildし、各PDFとSHA-256を検証してReleaseを作成します。成功後、Pages Workflowが公開済みのPDFを配信します。

Release Workflowは一度に1つだけ実行します。前の実行・Pages公開が終わってから次の正式版を作成してください。GitHubのReleases画面から先にReleaseを作らないでください。正式版タグはRelease Workflowが作成します。公開済みタグは再利用できないため、毎回まだ使っていない版番号を指定してください。

本棚の版番号とPDFリンクは、Pages公開後に `catalog.json` から自動取得します。

## ブランチ

- `main`: 次に公開する最新版の執筆線
- `release/N.x`: 第N版の保守線。必要になったとき、系列の最新Release Tagから作成

## ライセンス

このRepositoryにはライセンスを追加していません。原稿、図、PDFの利用条件を決めるまで、`LICENSE` は置きません。

## 最新版（開発中）

`main`へのpush時にBuild Workflowが両版のPDFを作成し、検査に成功するとActions成果物 `latex-build` に `main.pdf`、`mobile.pdf`、両版のSHA-256を含む `build-info.json` が保存されます。Pages Workflowは最新の成功したmainビルドを `latest.pdf`、`latest-mobile.pdf` として配信します。それぞれの `.sha256` も同じ場所から取得できます。

ビルドが失敗した場合はPagesを更新せず、直前に公開した開発PDFを維持します。開発ビルドごとのTagやPre-releaseは新たに作りません。正式版のReleaseとPagesの `book.pdf` は別に管理し、正式版番号も変わりません。

正式版と開発中のPDFは[数学書の本棚](https://mas256.github.io/math-textbooks/)から閲覧できます。教科書の紹介ページからも両方を開けます。

## PagesのPDFファイル名と本棚への公開情報

Pagesの正式版PDFは `タイトル-vMAJOR.MINOR.PATCH.pdf`、スマホ版は `タイトル-スマホ版-vMAJOR.MINOR.PATCH.pdf` です。開発中PDFには `latest-` が付きます。タイトルは公開Release時点の `book.yml`、版番号は配信する正式Releaseから取得します。開発中PDFの名前も現在の正式Release番号を使い、内容の更新はSHA-256クエリで区別します。

Pages WorkflowはPDFと一緒に `catalog.json` を公開します。正式版はReleaseの公開日時、latestは成功ビルドの `built_at` を最終更新日時とし、再配信では変更しません。本棚はこの情報から版番号・更新日時・PDFリンクを自動取得するため、`books.json` の版番号更新は不要です。

既存リンクとの互換性のため `book.pdf` と `latest.pdf` も残しますが、紹介ページと本棚はタイトル・版番号付きのPDFを案内します。公開済みReleaseのassetやTagは変更しません。

スマホ版の情報は同じ `catalog.json` の `release.mobile` / `latest.mobile` にPDF名とSHA-256を追加します。本棚と紹介ページはこの情報がある場合に「スマホ版で読む」を表示します。スマホ版がなかった旧Releaseも引き続き配信できます。
