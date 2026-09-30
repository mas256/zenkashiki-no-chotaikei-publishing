# 仮の設定。正式版は後日差し替える。
# upLaTeX で .dvi を作り、dvipdfmx で PDF にする。
$latex      = 'uplatex -halt-on-error -interaction=nonstopmode -file-line-error %O %S';
$bibtex     = 'upbibtex %O %B';
$makeindex  = 'upmendex %O -o %D %S';
$dvipdf     = 'dvipdfmx %O -o %D %S';
$pdf_mode   = 3;   # dvi -> pdf (dvipdfmx)
$max_repeat = 5;
