# 句読点後の空白をビルド時に補い、SyncTeXは元原稿へ戻す。
use Cwd qw(abs_path);
use File::Basename qw(dirname);
my $book_dir = abs_path(dirname(__FILE__));
my $repo_dir = abs_path("$book_dir/..");
my $python = $^O eq 'MSWin32' ? 'python' : 'python3';
my $spacing_script = abs_path("$book_dir/../scripts/tex-spacing.py");
system($python, $spacing_script, '--book', $book_dir, '--prepare') == 0
  or die "Cannot prepare punctuation spacing inputs\n";
$latex      = "$python \"$spacing_script\" --book \"$book_dir\" --compile -- -halt-on-error -interaction=nonstopmode -file-line-error %O %S";
$bibtex     = 'upbibtex %O %B';
$makeindex  = 'upmendex %O -o %D %S';
$dvipdf     = 'dvipdfmx %O -o %D %S';
$pdf_mode   = 3;
$max_repeat = 5;
$aux_dir    = "$repo_dir/out/latex-aux/basic";
