# このPCのLaTeX共通ビルド設定

2026年10月4日、現在のWindowsユーザーの共通設定を、この原稿の発展版と同じビルド方式に統一しました。

## ビルド方式

```text
latexmk → upLaTeX → DVI → dvipdfmx → PDF
```

文献は `upbibtex`、索引は `upmendex` を使用します。参照や目次を確定するための再コンパイルは `latexmk` が管理し、最大5回まで実行します。確認時のTeX環境は `C:\texlive\2026`、latexmkは4.88です。

## 共通設定の場所

- `%USERPROFILE%\.latexmkrc`：通常のユーザー共通設定。
- `%USERPROFILE%\latexmkrc`：既存の別名ファイルにも同じ設定を保存。
- `%APPDATA%\Code\User\settings.json`：VS CodeのLaTeX Workshop設定。
- `%APPDATA%\Cursor\User\settings.json`：CursorのLaTeX Workshop設定。

新しい原稿フォルダに設定ファイルをコピーする必要はありません。VS CodeとCursorでは `latexmk (latexmkrc)` を標準レシピにし、このレシピ・ツール設定を全プロファイルで共用します。SyncTeXによる原稿とPDFの位置対応も有効です。

ユーザー共通設定より後に、その実行フォルダの `.latexmkrc` または `latexmkrc` が読み込まれます。個別原稿で別のエンジンを指定している場合は、その個別設定が優先されます。LaTeX Workshopも個別のワークスペース設定やTeXのマジックコメントに対応しています。[latexmkの説明書](https://mirrors.ibiblio.org/CTAN/support/latexmk/latexmk.pdf)、[LaTeX Workshopのビルド設定](https://github.com/James-Yu/LaTeX-Workshop/wiki/Compile)

## 今後の執筆

VS CodeまたはCursorで原稿を開き、通常のLaTeX Workshopのビルド操作を行います。起動中のエディタに設定が反映されない場合は、一度ウィンドウを再読み込みしてください。

ターミナルでは、メインのTeXファイルを指定します。

```powershell
latexmk '原稿.tex'
```

別フォルダにある原稿も指定できます。共通設定の `$do_cd = 1` により、原稿のあるフォルダに移動して処理し、PDFをそこに生成します。

```powershell
latexmk 'C:\原稿フォルダ\新しい原稿.tex'
```

個別の `.latexmkrc` を使う原稿は、メインTeXと設定ファイルのあるフォルダから実行してください。`-pdf` はpdfLaTeXを選択するオプションなので、上記の標準ビルドでは追加しません。

## 確認済みの内容

このプロジェクトの外にある一時フォルダで、個別の `.latexmkrc` を置かずに日本語のテスト原稿をビルドしました。日本語・空白を含むファイル名と `\input`、数式、TikZ、tcolorbox、相互参照、文献、索引を確認しています。

## 元の設定のバックアップ

変更前の4ファイルと変更内容の記録は、次に保存しました。

```text
%USERPROFILE%\.latex-build-backups\20261004-161147
```

バックアップ内の `home-dot-latexmkrc` は元の `.latexmkrc`、`home-latexmkrc` は元の `latexmkrc`、`vscode-settings.json` と `cursor-settings.json` は各エディタの元の設定です。
