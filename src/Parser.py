from components.common.Syntax import Syntax
from components.common.States import States
from components.common.Data import EOF
from components.Lalr1 import LALR1

syntax = Syntax("/src/bnf/bnf.txt")

states = States()

states.LR0_table_gen(syntax)
states.lalr1_gen(syntax)

lalr1 = LALR1(syntax, states)

test = "**i=*i"

test = list(test)
test.append(EOF)

result = lalr1.parse(test)
result = lalr1.tree_gen(result, test[:-1])
result.show()