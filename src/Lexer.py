from components.common.Syntax import Syntax
from components.common.States import States
from components.common.Data import EOF, InputToken
from components.Lalr1 import LALR1
from components.regex.NFA import NFA
from components.regex.AST_Generator import ast_gen
import copy

from collections import deque

import os
cwd = os.getcwd()

def NFA_gen(input_pattern:str):
  syntax = Syntax("/src/bnf/regex_bnf.txt")

  states = States()

  states.LR0_table_gen(syntax)
  states.lalr1_gen(syntax)

  lalr1 = LALR1(syntax, states)

  pattern = list(input_pattern)

  invalidchars = ["|", "*", "?", ".", "(", ")", "$", ",", "!"]
  tokens = []
  literal_flag = False
  class_flag = False
  for token in pattern:
    add_token = token
    if literal_flag:
      literal_flag = False
      add_token = InputToken("<ordinary_character>", add_token)
      tokens.append(add_token)
      continue
    if class_flag:
      match add_token:
        case "d":
          add_token = InputToken("<ordinary_character>", "<class-digits>")
        case "a":
          add_token = InputToken("<ordinary_character>", "<class-lower-alphabet>")
        case "A":
          add_token = InputToken("<ordinary_character>", "<class-upper-alphabet>")
        case "z":
          add_token = InputToken("<ordinary_character>", "<class-alphabet>")
        case "Z":
          add_token = InputToken("<ordinary_character>", "<class-meta-alphabet>")
        case "w":
          add_token = InputToken("<ordinary_character>", "<class-meta-digits-alphabet>")
      class_flag = False
      tokens.append(add_token)
      continue
    if token == "\\":
      literal_flag = True
      continue
    if token == "/":
      class_flag = True
      continue
    if add_token not in invalidchars:
      add_token = InputToken("<ordinary_character>", add_token)
    tokens.append(add_token)
  tokens.append(EOF)

  result = lalr1.parse(tokens)
  result = lalr1.tree_gen(result, tokens[:-1])
  result = ast_gen(result)
  return NFA(result)

def Toknizer(pattern:str, input_str:str):
  nfa = NFA_gen(pattern)
  result = []
  input_deque = deque(input_str)
  count = 0
  while len(input_deque) > 0:
    input_chars = "".join(input_deque)
    ret = nfa.reg(input_chars)
    result.append("".join(ret.accepts))
    consume_flag = True
    for sym in ret.accepts:
      if sym == input_deque[0]:
        input_deque.popleft()
        consume_flag = False
    if consume_flag:
      count += 1
    else:
      count = 0
    if count > 2:
      return -1
  return result