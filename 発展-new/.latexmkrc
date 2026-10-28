# ID参照を検査し、句読点後の空白を補った入力からPDFを作る。
use Cwd qw(abs_path);
use File::Basename qw(dirname);
my $book_dir = abs_path(dirname(__FILE__));
my $repo_dir = abs_path("$book_dir/..");
my $python = $^O eq 'MSWin32' ? 'python' : 'python3';
my $input_checker = abs_path("$book_dir/../scripts/check-tex-inputs.py");
system($python, $input_checker, $book_dir) == 0
  or die "TeX import ID resolution or map generation failed\n";
my $spacing_script = abs_path("$book_dir/../scripts/tex-spacing.py");
system($python, $spacing_script, '--book', $book_dir, '--prepare') == 0
  or die "Cannot prepare punctuation spacing inputs\n";
$latex      = "$python \"$spacing_script\" --book \"$book_dir\" --compile -- -halt-on-error -interaction=nonstopmode -file-line-error %O %S";
$bibtex     = 'upbibtex %O %B';
$makeindex  = 'upmendex %O -o %D %S';
$dvipdf     = 'dvipdfmx %O -o %D %S';
$pdf_mode   = 3;   # dvi -> pdf (dvipdfmx)
$max_repeat = 5;
$aux_dir    = "$repo_dir/out/latex-aux";
