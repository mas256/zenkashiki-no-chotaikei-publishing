# リポジトリ直下のスマホ版も本編と同じupLaTeX設定でビルドする。
do './発展-new/.latexmkrc' or die $@ || $!;
