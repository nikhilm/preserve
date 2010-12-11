import sys
sys.path.append('/home/nikhil/workspace/preserve')

from nose.tools import assert_raises

from preserve import run

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

