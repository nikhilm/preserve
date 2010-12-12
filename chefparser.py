from pprint import pprint
from collections import namedtuple
import re
import logging

import funcparserlib.parser as p
from funcparserlib.lexer import make_tokenizer, Spec
from funcparserlib.contrib.lexer import space, newline
from funcparserlib.contrib.common import sometok, unarg

from common import *

log = logging.getLogger('preserve.chefparser')
#log.addHandler(logging.StreamHandler())
#log.setLevel(logging.DEBUG)

pos = 0

# order matters
instruction_spec = [
    Spec(x.lower().split()[0], x) for x in [
        'Take', 'Put', 'Fold', 'Add', 'Remove', 'Combine', 'Divide', 'Stir', 'Mix', 'Clean', 'Pour', 'Set aside', 'Refrigerate', 'from', 'into', 'the', 'for', 'contents of the', 'until', 'refrigerator', 'minute', 'minutes', 'hour', 'hours', 'well'
    ]
]
instruction_spec.insert(0, Spec('to', r'\wto\w'))
instruction_spec.insert(0, Spec('add_dry', 'Add dry ingredients'))
instruction_spec.insert(0, Spec('liquefy', 'Liquefy|Liquify'))
instruction_spec.append(Spec('serve_with', r'Serve with'))

instruction_spec.append(Spec('bowl', 'mixing bowl'))
instruction_spec.append(Spec('dish', 'baking dish'))
instruction_spec.append(space)
instruction_spec.append(Spec('string', '[A-Za-z]+'))
instruction_spec.append(Spec('ordinal', '[0-9]+(st|nd|rd|th)'))
instruction_spec.append(Spec('number', '[0-9]+'))

tokens = [
    Spec('ingredients_start', 'Ingredients'),
    Spec('method_start', r'^Method', re.MULTILINE),
    Spec('dry_measure', r' g | kg | pinch[es]? '),
    Spec('liquid_measure', r' ml | l | dash[es]? '),
    Spec('mix_measure', r'cup[s]?|teaspoon[s]?|tablespoon[s]?'),
    Spec('measure_type', 'heaped|level'),
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
    string = p.oneplus(sometok('string')) >> (lambda x: ' '.join(x))
    ordinal = sometok('ordinal')
    bowl = sometok('bowl')
    the = sometok('the')
    dish = sometok('dish')
    to = sometok('to')
    into = sometok('into')

    concat = lambda list: ' '.join(list)

    take_i = sometok('take') + (p.oneplus(string) >> concat) + sometok('from') + sometok('refrigerator')

    put_i = sometok('put') + p.skip(p.maybe(the)) + (p.oneplus(string) >> concat)  + sometok('into') + p.maybe(ordinal|the) + bowl

    liquefy_1 = sometok('liquefy') + sometok('contents') + p.maybe(ordinal) + bowl
    liquefy_2 = sometok('liquefy') + (p.oneplus(string) >> concat)
    liquefy_i = liquefy_1 | liquefy_2

    pour_i = sometok('pour') + sometok('contents') + p.maybe(ordinal) + bowl + sometok('into') + the + p.maybe(ordinal) + dish

    fold_i = sometok('fold') + p.skip(p.maybe(the)) + (p.oneplus(string) >> concat) + into + p.maybe(ordinal|the) + bowl

    # cleanup repitition
    add_i = sometok('add') + (p.oneplus(string) >> concat) + p.maybe(to + p.maybe(ordinal|the) + bowl)

    remove_i = sometok('remove') + (p.oneplus(string) >> concat) + p.maybe(sometok('from') + p.maybe(ordinal|the) + bowl)

    combine_i = sometok('combine') + (p.oneplus(string) >> concat) + p.maybe(into + p.maybe(ordinal|the) + bowl)

    divide_i = sometok('divide') + (p.oneplus(string) >> concat) + p.maybe(into + p.maybe(ordinal|the) + bowl)

    add_dry_i = sometok('add_dry') + p.maybe(to + p.maybe(ordinal|the) + bowl)

    stir_1 = sometok('stir') + p.maybe(the + p.maybe(ordinal|the) + bowl) + sometok('for') + sometok('number') + (sometok('minute')|sometok('minutes'))
    stir_2 = sometok('stir') + (p.oneplus(string) >> concat) + into + the + p.maybe(ordinal) + bowl
    stir_i = stir_1 | stir_2

    mix_i = sometok('mix') + p.maybe(the + p.maybe(ordinal) + bowl) + sometok('well')

    clean_i = sometok('clean') + p.maybe(ordinal|the) + bowl

    loop_start_i = (sometok('string') + p.maybe(the) + (p.oneplus(string) >> concat)) >> (lambda x: ('loop_start', x))
    loop_end_i = (sometok('string') + p.maybe(p.maybe(the) + (p.oneplus(string) >> concat)) + sometok('until') + string) >> (lambda x: ('loop_end', x))

    set_aside_i = sometok('set') >> (lambda x: (x, None))

    serve_with_i = sometok('serve_with') + (p.oneplus(string) >> concat)

    refrigerate_i = sometok('refrigerate') + p.maybe(sometok('for') + sometok('number') + (sometok('hour')|sometok('hours')))

    instruction = ( take_i
                  | put_i
                  | liquefy_i
                  | pour_i
                  | add_i
                  | fold_i
                  | remove_i
                  | combine_i
                  | divide_i
                  | add_dry_i
                  | stir_i
                  | mix_i
                  | clean_i
                  | loop_end_i      # -| ORDER matters
                  | loop_start_i    # -|
                  | set_aside_i
                  | serve_with_i
                  | refrigerate_i
                  ) >> (lambda x: Instruction(x[0].lower().replace(' ', '_'), x[1:]))

    return instruction.parse(tokenize_instruction(spec))

def parse(input):
    period = sometok('period')
    string = p.oneplus(sometok('string')) >> (lambda x: ' '.join(x))
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
                      >> unarg(CookingTime))

                    + p.skip(sometok('period'))
                   )

    oven_temp = (p.skip(sometok('oven'))
                + p.many(number)
                + p.skip(sometok('oven_temp'))
                >> unarg(Oven)
                )

    method_start = sometok('method_start') + p.skip(period)

    comment = p.skip(p.many(string|period))
    header = title + p.maybe(comment)

    instruction = (string
                   + p.skip(period)
                  ) >> parse_instruction

    instructions = p.many(instruction)

    program = (method_start + instructions) >> unarg(MethodStart)

    serves = (sometok('serve') + number >> (lambda x: Serve('serve', x[1])) ) + p.skip(period)

    ingredients_section = (ingredients_start + ingredients) >> unarg(IngredientSection)

    recipe = ( header
             + p.maybe(ingredients_section)
             + p.maybe(cooking_time)
             + p.maybe(oven_temp)
             + p.maybe(program)
             + p.maybe(serves)
             ) >> RecipeNode

    main_parser = p.oneplus(recipe)
    return main_parser.parse(tokenize(input))
