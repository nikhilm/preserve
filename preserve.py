import fileinput
from pprint import pprint

from parser import parse

mixing_bowls = {}
baking_dishes = {}

d = []
for line in fileinput.input():
    d.append(line.strip())

pprint(parse('\n'.join(d)))
