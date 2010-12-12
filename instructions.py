import sys
import copy
import re
import operator
import logging
import random

import preserve

log = logging.getLogger('preserve.instructions')
#log.addHandler(logging.StreamHandler())
#log.setLevel(preserve.global_loglevel)

def num(n):
    if n is None or n == 'the':
    	return 1

    n = re.sub(r'st|nd|rd|th', '', n)
    return int(n)

def make_put(args, recipe):
    def put(env):
        recipe.mixing_bowls[num(args[2])].append(copy.copy(recipe.ingredients[args[0]]))
    return put

def make_take(args, recipe):
    def take(env):
        inp = int(sys.stdin.readline().strip())
        ing = args[0]
        recipe.ingredients[ing].value = inp
    return take

def make_liquefy(args, recipe):
    # two variants of liquefy
    def liquefy(env):
        if len(args) == 3:
            n = num(args[1])
            for i in recipe.mixing_bowls[n]:
                i.state = 'liquid'
        else:
            recipe.ingredients[args[0]].state = 'liquid'

    return liquefy

def make_pour(args, recipe):
    def pour(env):
        n = num(args[1])
        p = num(args[5])

        for i in recipe.mixing_bowls[n]:
        	recipe.baking_dishes[n].append(i)

    return pour

def make_fold(args, recipe):
    def fold(env):
        n = num(args[2])
        ing = recipe.ingredients[args[0]]
        top = recipe.mixing_bowls[n].pop()
        ing.value = top.value

    return fold

def make_serve(args, recipe):
    def serve(env):
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
    def arith(env):
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
    def add_dry_ingredients(env):
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
    def stir(env):
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
    def mix(env):
        n = 1
        if args[0] is not None:
            n = num(args[0][1])

        random.shuffle(recipe.mixing_bowls[n])

    return mix

def make_clean(args, recipe):
    def clean(env):
        n = num(args[0])
        recipe.mixing_bowls[n] = []

    return clean

class make_loop_start(object):
    def __init__(self, args, recipe):
        args = args[0] #unpack
        recipe.loop_depth += 1
        self.recipe = recipe
        self.verb = args[0].lower()
        # if it ends in e, the end loop equivalent
		# will have just a d
        if self.verb[-1] == 'e':
            self.verb = self.verb[:-1]

        self.ingredient_name = args[2]
        self.depth = recipe.loop_depth
        self.jump = None

    def __call__(self, env):
        if self.jump == None:
            raise SyntaxError("%s:%s: No matching loop end for %s %s"%(self.recipe.title, self.recipe.instructions.index(self), self.verb, self.ingredient_name))
        val = self.recipe.ingredients[self.ingredient_name].value
        if val == 0:
            self.recipe.ip = self.jump

class make_loop_end(object):
    def __init__(self, args, recipe):
        args = args[0] #unpack
        self.recipe = recipe
        self.verb = args[3].lower()[:-2]
        self.depth = recipe.loop_depth
        recipe.loop_depth -= 1
        self.jump = None

        self.ingredient_name = None
        if args[1] is not None:
            self.ingredient_name = args[1][1]

        self.search_depth = 0
        # search for start expression
        for i in reversed(recipe.instructions):
            if type(i) == make_loop_start:
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
            elif type(i) == make_loop_end:
                self.search_depth += 1
        assert self.search_depth == 0

    def __call__(self, env):
        if self.ingredient_name is not None:
            self.recipe.ingredients[self.ingredient_name].value -= 1
        self.recipe.ip = self.jump

def make_set_aside(args, recipe):
    def set_aside(env):
        for i in range(recipe.ip, len(recipe.instructions)):
            instr = recipe.instructions[i]
            if type(instr) is make_loop_end:
                recipe.ip = i+1
                return
        # if we reach here, we weren't
        # in a loop
        raise SyntaxError("'Set aside.' not in loop body!")

    return set_aside

def make_serve_with(args, recipe):
    def serve_with(env):
        log.debug("Recipes are %s", env.recipes)
        subrecipe = env.recipes[args[0]]
        log.debug("Invoking %s", subrecipe)

        subrecipe.mixing_bowls = copy.deepcopy(recipe.mixing_bowls)
        subrecipe.baking_dishes = copy.deepcopy(recipe.baking_dishes)
        subrecipe.cook(env)

        recipe.mixing_bowls[1].extend(subrecipe.mixing_bowls[1])

    return serve_with

def make_refrigerate(args, recipe):
    def refrigerate(env):
        recipe.ip = len(recipe.instructions)

    return refrigerate
