Preserve
========

Preserve is an interpreter for the esoteric programming language
[Chef](http://www.dangermouse.net/esoteric/chef.html) by Davig Morgan-Mar.

It is written in Python (2.6-2.7) and uses
[funcparserlib](http://code.google.com/p/funcparserlib/).

**NOTE: The latest stable release of funcparserlib - 0.3.4 does not have the
_contrib_ package. So make sure you checkout from
[hg](http://code.google.com/p/funcparserlib/source/checkout)**

The two example programs from the website are included in examples.

Run:

    python preserve.py [program name]

If program name is absent, Preserve will wait for you to type in the program on
standard input.
