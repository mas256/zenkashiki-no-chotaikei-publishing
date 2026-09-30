# 初期設定

Tag・Immutable releases・Tag rulesetは、一度作ると取り消せません。**先に、使い捨てのテスト用Repositoryで一通り試してから**、本番のRepositoryに適用してください。

## 0. 前提

- Repositoryは**Public**にします(Privateでは、読者がReleasesに届かず、Pagesに有料プランが必要です)。Publicは、URLを知らない人にも見えます。友人間の共有でも、`main`の原稿は誰でも読めます。
- ローカルに`git`と`gh`(GitHub CLI、`gh auth login`済み)が必要です。`scripts/tag-release.sh`はbashで動きます(Windowsでは WSL または Git Bash を使います)。

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

`.github/workflows/_build.yml`はDocker Hubで確認した`texlive/texlive:TL2025-historic`のmanifest digest `sha256:f25ee2dcd00f58198f918064f4a1c8562410b33e84155bd55b02b419d73d9391`に固定済みです。digestを更新するときは「Show image digest」Workflowを手動実行し、`image:`と`IMAGE_REF:`を同時に更新してください。

## 4. Buildを確認する

`main`へPushして、`Build`が成功することを確認します。既存の入口TeXと本文は日本語パスのまま維持されています。成功しない場合は、ログを確認します。

- 「未解決の参照があります」: `\ref`や`\cite`の参照先を確認します。
- 「PDFに埋め込まれていないフォントがあります」/「原ノ味フォントが埋め込まれていません」: フォント設定を確認します。

## 5. 初回運用確認

Immutable releasesやrulesetは最初のRelease前に有効にしてください。可能なら本番公開前にコピーしたテスト用Repositoryで次を確認します。

1. `main`へのPushで`Build`が成功する
2. `v0.0.1`を作成し、ReleaseにPDFと`.sha256`が付き、Pagesに`/`と`/book.pdf`が公開される
3. 旧系列Tagを後から公開してもPagesが新しい版のままになる

## 6. 最初の正式版

コピー先の本番Repositoryで、Buildが成功したCommitに対して実行します。

```bash
scripts/tag-release.sh v1.0.0
```
