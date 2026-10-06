# 初期設定

Tag・Immutable releases・Tag rulesetは、一度作ると取り消せません。**先に、使い捨てのテスト用Repositoryで一通り試してから**、本番のRepositoryに適用してください。

## 0. 前提

- Repositoryは**Public**にします(Privateでは、読者がReleasesに届かず、Pagesに有料プランが必要です)。Publicは、URLを知らない人にも見えます。友人間の共有でも、`main`の原稿は誰でも読めます。
- 執筆と公開はGitHubのWeb画面から行えます。ローカルのGit BashやGitHub CLIは不要です。

## 1. ファイルを置く

このRepositoryでは「基本-new」と「発展-new」の2系統を管理し、正式版としてReleaseするのは`発展-new/漸化式の超体系的解説.tex`です。Build Workflowと`.github/workflows/_build.yml`はこの入口に合わせて設定済みです。発展版はTeX Live 2026で日本語・空白を含む`\input`を含めてコンパイル確認済みです。

## 2. Repositoryの設定

画面の名称は変わることがあります。

1. **Pages:** Settings → Pages → Source を「GitHub Actions」にします。
2. **Immutable releases:** Settings で有効にします。**最初のReleaseを作る前**に行います。
3. **Tag ruleset:** Settings → Rules → Rulesets → New tag ruleset。
   - Target: `v[0-9]*.[0-9]*.[0-9]*`(一致しなければ`v*`)
   - Restrict updates と Restrict deletions を有効にします。Enforcementは Active です。
4. **Actions権限:** Settings → Actions → General → Workflow permissions を、読み取りのみにします(書き込みが必要なjobは、Workflowで個別に宣言しています)。
5. **Environment `github-pages`:** Pagesを有効にすると自動で作られます。デプロイ対象がデフォルトブランチのみであることを確認します(`v*`は追加しません)。

## 3. Build環境

`.github/workflows/_build.yml`は Ubuntu 24.04 上で TeX Live 2025 の固定アーカイブ `https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2025/tlnet-final` を使用します。`scripts/setup-texlive.sh` が SHA-512 を固定したインストーラーで最小構成を用意し、`.github/texlive/packages.txt` のパッケージと依存関係を追加します。マニュアル・ソースはインストールしません。

環境全体を Actions cache に保存します。セットアップスクリプトまたはパッケージ一覧を変更するとキャッシュキーも変わり、自動で再構築します。新しい LaTeX パッケージを使う場合は一覧にも追加してください。キャッシュがない初回はインストールに時間がかかります。参照検査と原ノ味フォントの埋め込み検査は毎回実行します。

Build は原稿・共通TeX・ビルド設定が変わった場合に実行します。README や出版サイトだけの変更では PDF を再ビルドしません。Actions の手動実行は引き続き利用できます。通常の Build は新しい変更で古い実行を中止します。正式版の Release は中止せず、最後まで実行します。

## 4. Buildを確認する

`main`へPushして、`Build`が成功することを確認します。成功後に`Deploy Pages`が実行され、開発中PDFを`latest.pdf`として公開します。既存の入口TeXと本文は日本語パスのまま維持されています。成功しない場合は、ログを確認します。

- 「未解決の参照があります」: `\ref`や`\cite`の参照先を確認します。
- 「PDFに埋め込まれていないフォントがあります」/「原ノ味フォントが埋め込まれていません」: フォント設定を確認します。

## 5. 正式版をブラウザーから公開する

1. 原稿の変更を`main`へCommitします。ファイルの画面で鉛筆アイコンから編集し、`Commit changes`を押せます。
2. Actionsで`Build`と後続の`Deploy Pages`が成功し、開発中PDFが`latest.pdf`に公開されたことを確認します。
3. Actions → `Release` → `Run workflow`を開きます。
4. Branchを`main`にし、`version`へ未使用の版番号（例: `v1.0.3`）を入力して実行します。
5. `Release`が成功したら、ReleasesにPDFと`.sha256`の2ファイルが添付されたことを確認します。
6. `Deploy Pages`が成功し、正式版の`book.pdf`と開発中の`latest.pdf`が配信されたことを確認します。
7. `math-textbooks`リポジトリの`books.json`を編集し、`version`を公開した番号にしてCommitします。
8. カタログのActionsも成功したら、本棚の表示を確認します。

GitHubのReleases画面から先にReleaseを作らないでください。この方法では、Release WorkflowがタグとRelease、添付ファイルをまとめて作成します。公開済みの版番号は再利用できません。

## 6. 初回運用確認

Immutable releasesやrulesetは最初のRelease前に有効にしてください。可能なら本番公開前にコピーしたテスト用Repositoryで次を確認します。

1. `main`へのPushで`Build`が成功し、`Deploy Pages`が`/latest.pdf`を公開する
2. `v0.0.1`を作成し、ReleaseにPDFと`.sha256`が付き、Pagesに`/`と`/book.pdf`が公開される
3. 旧系列Tagを後から公開してもPagesが新しい版のままになる

## 7. 最初の正式版

Actions画面から`Release`を実行します。初版の番号は`v1.0.0`です。
