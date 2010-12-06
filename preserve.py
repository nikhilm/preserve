import fileinput
from pprint import pprint
from collections import defaultdict
import logging

import common as c
import instructions
from chefparser import parse

log = logging.getLogger('preserve')
log.addHandler(logging.StreamHandler())

global_loglevel = logging.DEBUG

log.setLevel(global_loglevel)

recipes = {}

class Ingredient(object):
    def __init__(self, name, unit=None, initial=0):
        self.name = name
        self.value = int(initial)

        if type(unit) is str:
            unit = (None, unit)

        self.unit = unit and unit[1].strip()
        if self.unit in [None, 'g', 'kg', 'pinch', 'pinches']:
            self.state = 'dry'
        elif self.unit in ['ml', 'l', 'dash', 'dashes']:
            self.state = 'liquid'
        else:
            if unit[0] in ['heaped', 'level']:
                self.state = 'dry'
            else:
                self.state = 'liquid'

    def __str__(self):
        return "ingredient %s: %s %s %s"%(self.name, self.value, self.unit, self.state)

class IngredientDict(defaultdict):
    def __missing__(self, key):
        self[key] = value = Ingredient(key)
        return value

class Recipe(object):
    def __init__(self, title):
        self.mixing_bowls = defaultdict(list)
        self.baking_dishes = defaultdict(list)
        self.ingredients = IngredientDict()
        self.instructions = []
        self.title = title
        self.log = logging.getLogger(self.title)
        self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(global_loglevel)

    def __str__(self):
        rep = ["""
Recipe %s.

Current state:
 Ingredients: """%self.title]

        for i in self.ingredients.values():
            rep.append('  ' + str(i))

        rep.append('')
        rep.append(' Mixing bowls.')
        for (k, v) in self.mixing_bowls.items():
            rep.append('  Bowl %d'%k)
            for i in v:
                rep.append('    %s'%i)

        rep.append('')
        rep.append(' Baking dishes.')
        for (k, v) in self.baking_dishes.items():
            rep.append('  Dish %d'%k)
            for i in v:
                rep.append('    %s'%v)

        return '\n'.join(rep)


    def add_ingredient(self, ing):
        self.log.debug("Adding %s"%ing)
        self.ingredients[ing.name] = ing

    def cook_instruction(self, instr):
        make = getattr(instructions, 'make_%s'%instr.command)
        return make(instr.rest, self)

    def add_instruction(self, instr):
        try:
            ci = self.cook_instruction(instr)
            self.instructions.append(ci)
        except AttributeError, e:
            self.log.debug("Recipe attribute error %s"%e)
            raise SyntaxError("No such command %s"%instr.command)

    def cook(self):
        log.debug("Starting execution")
        for instr in self.instructions:
            instr()
        return self

def interpret_recipe(title, ast):
    recipes[title] = recipe = Recipe(title)
    log.debug("Interpreting recipe %s"%title)

    for node in ast:
        if type(node) is c.IngredientSection:
            log.debug("Start ingredients")

            for ing in node.list:
                recipe.add_ingredient(Ingredient(ing.name, ing.measure, ing.initial))

        elif type(node) is c.MethodStart:
            log.debug("Starting preparation")
            for instr in node.list:
                recipe.add_instruction(instr)

        # TODO instr scope issue
        elif type(node) is c.Serve:
            # see the note in parser.tokens
            recipe.add_instruction(node)

        else:
            log.warning("Unexpected node %s: %s"%(type(node), node))

    return recipe

def interpret(node, ast):
    if type(node) is c.RecipeTitle:
        return interpret_recipe(node.title, ast[1:])
    else:
        raise SyntaxError("Expected Recipe Title")

def run(program):
    """runs program string"""
    ast = parse(program)
    return interpret(ast[0], ast).cook()

if __name__ == '__main__':
    d = []
    for line in fileinput.input():
        d.append(line.strip())

    run('\n'.join(d))
