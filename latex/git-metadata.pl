#!/usr/bin/env perl
# Generates main-gitauthor.tmp and main-gitemail.tmp from `git config`.
# These files are read by CTUthesis.cls via \InputIfFileExists to populate
# \@author and \@email without requiring \makeatletter in main.tex.
#
# Usage: perl git-metadata.pl [output-dir]
#   output-dir  directory where .tmp files are written (default: .)
#   This is needed because LaTeX Workshop does not set CWD to the tex dir.

use strict;
use warnings;

my $dir = $ARGV[0] // '.';
mkdir $dir unless -d $dir;

my $author = `git config user.name  2>/dev/null` // '';
my $email  = `git config user.email 2>/dev/null` // '';
chomp $author;  chomp $email;
$author ||= 'Name Surname';
$email  ||= 'address@e-mail.xy';

if (open my $fh, '>', "$dir/main-gitauthor.tmp") {
    print $fh '\gdef\@author{' . $author . "}\n";
    close $fh;
}
if (open my $fh2, '>', "$dir/main-gitemail.tmp") {
    print $fh2 '\gdef\@email{' . $email . "}\n";
    close $fh2;
}
