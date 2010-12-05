# simple execution of each instruction

import sys
sys.path.append('/home/nikhil/workspace/preserve')

from cStringIO import StringIO
from preserve import run

recipe = """
Simple.

Ingredients.
2 beans

Method.
Take apricot jam from refrigerator.
Put apricot jam into the mixing bowl.
Add apricot jam to the mixing bowl.
Add apricot jam to the mixing bowl.
Pour contents of the mixing bowl into the baking dish.
Fold apricot jam into mixing bowl.
Put beans into 2nd mixing bowl.
Add beans to 2nd mixing bowl.
Combine apricot jam into 2nd mixing bowl.
Remove beans from 2nd mixing bowl.

Fold fig into 2nd mixing bowl.

Put apricot jam into the mixing bowl.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Add apricot jam.
Divide fig into mixing bowl.

Serves 1.

"""

stdin = sys.stdin
stdout = sys.stdout

sys.stdin = StringIO()
sys.stdout = StringIO()

sys.stdin.write('1\n')
sys.stdin.seek(0)

result = run(recipe)
sys.stdin.close()

sys.stdout.seek(0)
out = sys.stdout.read()

sys.stdin = stdin
sys.stdout = stdout

print >> sys.stderr, result
assert result
assert len(result.ingredients) == 3
assert result.ingredients['apricot jam'].value == 3
assert result.ingredients['beans'].value == 2
assert result.mixing_bowls[1][-1].value == 3
assert len(result.mixing_bowls[2]) == 0
