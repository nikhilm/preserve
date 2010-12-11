import sys
import copy
import re
import operator
import logging
import random

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
    def liquefy():
        if len(args) == 3:
            n = num(args[1])
            for i in recipe.mixing_bowls[n]:
                i.state = 'liquid'
        else:
            recipe.ingredients[args[0]].state = 'liquid'

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

def make_stir(args, recipe):
    def stir():
        howmany = 0
        bowl = None
        if type(args[0]) is str:
            howmany = recipe.ingredients[args[0]].value
            bowl = recipe.mixing_bowls[num(args[3])]

        else:
            howmany = int(args[2])
            n = 1
            if args[0] is not None:
                n = num(args[0][1])

            bowl = recipe.mixing_bowls[n]

        try:
            if len(bowl) <= howmany:
                bowl.insert(0, bowl.pop())
            else:
                pos = len(bowl) - howmany - 1
                bowl.insert(pos, bowl.pop())
        except IndexError:
            raise IndexError("Stir attempted on empty bowl! %s"%str(args))

    return stir

def make_mix(args, recipe):
    def mix():
        n = 1
        if args[0] is not None:
            n = num(args[0][1])

        random.shuffle(recipe.mixing_bowls[n])

    return mix

def make_clean(args, recipe):
    def clean():
        n = num(args[0])
        recipe.mixing_bowls[n] = []

    return clean

class loop_start(object):
    def __init__(self, instr, depth, recipe):
        self.recipe = recipe
        self.verb = instr.command.lower()
        self.ingredient_name = instr.rest[1]
        self.depth = depth
        self.jump = None

    def __call__(self):
        if self.jump == None:
            raise SyntaxError("%s:%s: No matching loop end for %s %s"%(self.recipe.title, self.recipe.instructions.index(self), self.verb, self.ingredient_name))
        val = self.recipe.ingredients[self.ingredient_name].value
        if val == 0:
            self.recipe.ip = self.jump

class loop_stop(object):
    def __init__(self, instr, depth, recipe):
        self.recipe = recipe
        self.verb = instr.rest[2].lower()[:-2]
        self.depth = depth
        self.jump = None

        self.ingredient_name = None
        if instr.rest[0] is not None:
            self.ingredient_name = instr.rest[0][1]

        self.search_depth = 0
        # search for start expression
        for i in reversed(recipe.instructions):
            if type(i) == loop_start:
                # depth > ours is ok
                if i.depth == self.depth:
                    if i.verb != self.verb:
                        raise NameError("Unexpected loop verb %s. Expected %s"%(i.verb, self.verb))
                    else:
                        self.jump = recipe.instructions.index(i)
                        i.jump = len(recipe.instructions) + 1
                        break
                else:
                    self.search_depth -= 1
            elif type(i) == loop_stop:
                self.search_depth += 1
        assert self.search_depth == 0

    def __call__(self):
        if self.ingredient_name is not None:
            self.recipe.ingredients[self.ingredient_name].value -= 1
        self.recipe.ip = self.jump

def make_set_aside(args, recipe):
    def set_aside():
        for i in range(recipe.ip, len(recipe.instructions)):
            instr = recipe.instructions[i]
            if type(instr) is loop_stop:
                recipe.ip = i+1
                return
        # if we reach here, we weren't
        # in a loop
        raise SyntaxError("'Set aside.' not in loop body!")

    return set_aside

