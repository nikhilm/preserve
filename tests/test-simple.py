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
Remove beans from 2nd mixing bowl.
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

print result
assert result
assert len(result.ingredients) == 2
assert result.ingredients['apricot jam'].value == 3
