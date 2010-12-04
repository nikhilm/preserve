from collections import namedtuple

RecipeTitle = namedtuple('RecipeTitle', 'title')
IngredientStart = namedtuple('IngredientStart', 'ignored')
Ingredient = namedtuple('Ingredient', 'initial measure name')
IngredientSection = namedtuple('IngredientSection', 'start list')
CookingTime = namedtuple('CookingTime', 'time unit')
Oven = namedtuple('Oven', 'temperature')
MethodStart = namedtuple('MethodStart', 'start list')
Serve = namedtuple('Serve', 'command rest')
Instruction = namedtuple('Instruction', 'command rest')

