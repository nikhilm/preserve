import sys
import copy
import re
import operator
import logging

import preserve

log = logging.getLogger('preserve.instructions')
log.addHandler(logging.StreamHandler())

def num(n):
    if n is None or n == 'the':
    	return 1

    n = re.sub(r'st|nd|rd|th', '', n)
    return int(n)

def make_put(args, recipe):
    def put():
        recipe.mixing_bowls[num(args[2])].append(copy.copy(recipe.ingredients[args[0]]))
    return put

def make_take(args, recipe):
    def take():
        inp = int(sys.stdin.readline().strip())
        ing = args[0]
        recipe.ingredients[ing].value = inp
    return take

def make_liquefy(args, recipe):
    # two variants of liquefy
    if len(args) == 3:
        def liquefy():
            n = num(args[1])
            for i in recipe.mixing_bowls[n]:
                i.state = 'liquid'
        return liquefy

def make_pour(args, recipe):
    def pour():
        n = num(args[1])
        p = num(args[5])

        for i in recipe.mixing_bowls[n]:
        	recipe.baking_dishes[n].append(i)

    return pour

def make_fold(args, recipe):
    def fold():
        n = num(args[2])
        ing = recipe.ingredients[args[0]]
        top = recipe.mixing_bowls[n].pop()
        ing.value = top.value

    return fold

def make_serve(args, recipe):
    def serve():
        n = num(args)
        for i in range(1, n+1):
            dish = recipe.baking_dishes[i]
            while len(dish) > 0:
            	ing = dish.pop()
                if ing.state == 'dry':
                    sys.stdout.write(str(ing.value))
                else:
                	sys.stdout.write(chr(ing.value))

    return serve

def make_arith(args, recipe, op):
    def arith():
        ing = recipe.ingredients[args[0]]
        n = 1
        if args[1] is not None:
            n = num(args[1][1])

        try:
            recipe.mixing_bowls[n][-1].value = op(recipe.mixing_bowls[n][-1].value, ing.value)
        except IndexError:
            raise IndexError("Bowl %s is empty!"%n)

    return arith

def make_add(args, recipe):
    return make_arith(args, recipe, operator.add)

def make_remove(args, recipe):
    return make_arith(args, recipe, operator.sub)

def make_combine(args, recipe):
    return make_arith(args, recipe, operator.mul)

def make_divide(args, recipe):
    return make_arith(args, recipe, operator.div)

def make_add_dry_ingredients(args, recipe):
    def add_dry_ingredients():
        actual_args = args[0]

        n = 1
        if actual_args is not None:
            n = num(actual_args[1])

        values = [ing.value for ing in recipe.ingredients.values() if ing.state == 'dry']

        # TODO Place as in add on top or replace?
        try:
            recipe.mixing_bowls[n][-1].value = sum(values)
        except IndexError:
            raise IndexError("Bowl %s is empty!"%n)

    return add_dry_ingredients
