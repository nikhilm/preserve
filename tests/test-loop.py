import sys
sys.path.append('/home/nikhil/workspace/preserve')

from nose.tools import assert_raises

from preserve import run, interpret, parse

recipe_simple_loop = """
Fruity Loops 1.

Ingredients.
10 g flour
1 teaspoon honey

Method.
Sift the flour.
  Put honey into mixing bowl.
Shake the flour until sifted.
"""

simple_loop = run(recipe_simple_loop)

assert simple_loop.ingredients['flour'].value == 0
assert len(simple_loop.mixing_bowls[1]) == 10

recipe_nesting = """
Fruity Loops Nesting.

Ingredients.
10 g flour
5 g cheese
1 teaspoon honey

Method.
Sift the flour.
  Put honey into mixing bowl.
  Grate the cheese.
    Put honey into the mixing bowl.
  Dance the cheese until grateed.
Shake the flour until sifted.
"""

nesting = run(recipe_nesting)

assert nesting.ingredients['flour'].value == 0
assert nesting.ingredients['cheese'].value == 0
assert len(nesting.mixing_bowls[1]) == 15

recipe_err_nesting = """
Fruity Loops Broken Nesting.

Ingredients.

Method.
Sift the flour.
  Sift the flour.
    Put honey into mixing bowl.
Shake the flour until sifted.
"""

assert_raises(SyntaxError, run, recipe_err_nesting)

recipe_verb_match = """
Fruity Loops Verb Match.

Ingredients.
1 g flour
1 g cheese

Method.
Sift the flour.
  Grate the cheese.
    Gyrate the hips.
    Dance until gyrateed.
  Grate the cheese until grateed.
Shake the flour until sifted.
"""

verb_match_ast = parse(recipe_verb_match)
verb_match_i = interpret(verb_match_ast[0], verb_match_ast)

verb_match = verb_match_i.cook()
assert len(verb_match.ingredients) == 3

recipe_verb_match_fail = """
Fruity Loops Verb Match Fail.

Ingredients.
1 g flour
1 g cheese

Method.
Sift the flour.
  Grate the cheese.
    Gyrate the hips.
    Dance until gyrate.
  Grate the cheese until grateed.
Shake the flour until sifted.
"""

assert_raises(NameError, run, recipe_verb_match_fail)

recipe_err_nesting = """
Fruity Loops Broken Nesting.

Ingredients.

Method.
Sift the flour.
  Sift the flour.
    Put honey into mixing bowl.
Shake the flour until sifted.
"""

assert_raises(SyntaxError, run, recipe_err_nesting)

