# upLaTeX で原稿を直接コンパイルし、dvipdfmx で PDF にする。
use Cwd qw(abs_path);
use File::Basename qw(dirname);
my $book_dir = abs_path(dirname(__FILE__));
my $python = $^O eq 'MSWin32' ? 'python' : 'python3';
my $input_checker = abs_path("$book_dir/../scripts/check-tex-inputs.py");
system($python, $input_checker, $book_dir) == 0
  or die "TeX import ID resolution or map generation failed\n";
$latex      = 'uplatex -halt-on-error -interaction=nonstopmode -file-line-error %O %S';
$bibtex     = 'upbibtex %O %B';
$makeindex  = 'upmendex %O -o %D %S';
$dvipdf     = 'dvipdfmx %O -o %D %S';
$pdf_mode   = 3;   # dvi -> pdf (dvipdfmx)
$max_repeat = 5;
