# upLaTeX で .dvi を作り、dvipdfmx で PDF にする。
use Cwd qw(abs_path);
use File::Basename qw(dirname);
my $book_dir = abs_path(dirname(__FILE__));
my $spacing_script = abs_path("$book_dir/../scripts/tex-spacing.py");
my $python = $^O eq 'MSWin32' ? 'python' : 'python3';
system($python, $spacing_script, '--prepare') == 0
  or die "Cannot prepare punctuation spacing inputs\n";
my $spacing_inputs = abs_path("$book_dir/../out/tex-spacing/book");
my $path_separator = $^O eq 'MSWin32' ? ';' : ':';
$ENV{'TEXINPUTS'} = $spacing_inputs . $path_separator . $book_dir . $path_separator . ($ENV{'TEXINPUTS'} // '');
$latex      = "$python \"$spacing_script\" --compile -- -halt-on-error -interaction=nonstopmode -file-line-error %O %S";
$bibtex     = 'upbibtex %O %B';
$makeindex  = 'upmendex %O -o %D %S';
$dvipdf     = 'dvipdfmx %O -o %D %S';
$pdf_mode   = 3;   # dvi -> pdf (dvipdfmx)
$max_repeat = 5;
