import sys

def num(n):
    if n is None or n == 'the':
    	return 1
    return int(n)

def make_put(args, recipe):
    def put():
        recipe.mixing_bowls[num(args[2])].append(recipe.ingredients[args[0]])
    return put

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

def make_serve(args, recipe):
    def serve():
        n = num(args)
        for i in range(1, n+1):
            dish = recipe.baking_dishes[i]
            while len(dish) > 0:
            	ing = dish.pop()
                if ing.state == 'dry':
                	sys.stdout.write(ing.value)
                else:
                	sys.stdout.write(chr(ing.value))

    return serve
