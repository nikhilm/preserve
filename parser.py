from pprint import pprint
from collections import namedtuple
import re

import funcparserlib.parser as p
from funcparserlib.lexer import make_tokenizer, Spec
from funcparserlib.contrib.lexer import space, newline
from funcparserlib.contrib.common import sometok, unarg

from common import *

pos = 0

# order matters
instruction_spec = [
    Spec(x.lower().split()[0], x) for x in [
        'Take', 'Put', 'Fold', 'Add', 'Remove', 'Combine', 'Divide', 'Stir', 'Mix', 'Clean', 'Pour', 'Set aside', 'Refrigerate', 'from', 'into', 'the', 'to', 'contents of the', 'until', 'refrigerator'
    ]
]

instruction_spec.insert(0, Spec('add_dry', 'Add dry'))
instruction_spec.insert(0, Spec('liquefy', 'Liquefy|Liquify'))
instruction_spec.append(Spec('serve_with', r'Serve with'))

instruction_spec.append(Spec('bowl', 'mixing bowl'))
instruction_spec.append(Spec('dish', 'baking dish'))
instruction_spec.append(space)
instruction_spec.append(Spec('string', '[a-z]+'))
instruction_spec.append(Spec('ordinal', '[0-9]+(st|nd|rd|th)'))

tokens = [
    Spec('ingredients_start', 'Ingredients'),
    Spec('method_start', r'^Method', re.MULTILINE),
    Spec('dry_measure', r' g | kg | pinch[es]? '),
    Spec('liquid_measure', r' ml | l | dash[es]? '),
    Spec('mix_measure', r'cup[s]?|teaspoon[s]?|tablespoon[s]?'),
    Spec('measure_type', 'heaped|level'),
    Spec('time_unit', '(hour|minute)[s]?'),
    # TODO hours minutes
    Spec('cooking_time', r'Cooking time:'),
    # TODO gas mark
    Spec('oven', r'Pre\-heat oven to'),
    Spec('oven_temp', 'degrees Celcius'),
    # serve is treated separate here as it is
    # not necessary for it to appear
    # following 'Method.'
    # But it is treated as just another
    # instruction by the interpreter
    Spec('serve', r'^Serves', re.MULTILINE),
    Spec('number', '[0-9]+'),
    space,
    Spec('period', r'\.'),
    Spec('string', r'[^\.\r\n]+'),
]

def tokenize_minus_whitespace(token_list, input):
    return [x for x in make_tokenizer(token_list)(input) if x.type not in ['space']]
    
def tokenize_instruction(spec):
    return tokenize_minus_whitespace(instruction_spec, spec)

def tokenize(input):
    return tokenize_minus_whitespace(tokens, input)

def parse_instruction(spec):
    string = sometok('string')
    ordinal = sometok('ordinal')
    bowl = sometok('bowl')
    the = sometok('the')
    dish = sometok('dish')

    concat = lambda list: ' '.join(list)

    take_i = sometok('take') + p.many(string) + sometok('from') + sometok('refrigerator')

    put_i = sometok('put') + (p.oneplus(string) >> concat)  + sometok('into') + (ordinal|the) + bowl

    liquefy_1 = sometok('liquefy') + sometok('contents') + p.maybe(ordinal) + bowl
    liquefy_2 = sometok('liquefy') + p.many(string)
    liquefy_i = liquefy_1 | liquefy_2

    pour_i = sometok('pour') + sometok('contents') + p.maybe(ordinal) + bowl + sometok('into') + the + p.maybe(ordinal) + dish

    instruction = ( take_i
                  | put_i
                  | liquefy_i
                  | pour_i
                  ) >> (lambda x: Instruction(x[0].lower(), x[1:]))

    return instruction.parse(tokenize_instruction(spec))

def parse(input):
    period = sometok('period')
    string = sometok('string')
    number = sometok('number')

    title = string + p.skip(period) >> RecipeTitle
    ingredients_start = sometok('ingredients_start') + p.skip(period) >> IngredientStart

    dry_measure = p.maybe(sometok('measure_type')) + sometok('dry_measure')
    liquid_measure = sometok('liquid_measure')
    mix_measure = sometok('mix_measure')

    # is this valid ? 'g of butter', unit w/o initial_value
    ingredient = (p.maybe(number)
                  + p.maybe(dry_measure
                           | liquid_measure
                           | mix_measure)
                  + string >> unarg(Ingredient)
                 )

    ingredients = p.many(ingredient)

    cooking_time = (p.skip(sometok('cooking_time'))
                    + (number
                      + p.maybe(sometok('time_unit')
                      ) >> unarg(CookingTime))

                    + p.skip(sometok('period'))
                   )

    oven_temp = (p.skip(sometok('oven'))
                + p.many(number)
                + p.skip(sometok('oven_temp'))
                >> unarg(Oven)
                )

    method_start = sometok('method_start') + p.skip(period)

    comment_part = p.maybe(period) + string
    comment = string + comment_part + p.maybe(period)
    header = title + p.maybe(comment)

    instruction = (string
                   + p.skip(period)
                  ) >> parse_instruction

    instructions = p.many(instruction)

    program = (p.skip(method_start) >> (MethodStart)) + instructions

    serves = sometok('serve') + ( p.oneplus(number) >> unarg(Serve) ) + period

    recipe = ( header
             + ingredients_start
             + ingredients
             + p.maybe(cooking_time)
             + p.maybe(oven_temp)
             + p.maybe(program)
             + p.maybe(serves)
             )

    main_parser = recipe

    #pprint(tokenize(input))
    return main_parser.parse(tokenize(input))
