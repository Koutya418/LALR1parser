from .components.common.Syntax import _Syntax
from .components.common.States import States
from .components.common.Data import EOF, InputToken
from .components.Lalr1 import LALR1
from .components.regex.NFA import NFA
from .components.regex.AST_Generator import ast_gen

from pathlib import Path
from collections import deque
import pprint

base_dir = Path(__file__).resolve().parent

regex_bnf_json_path = base_dir / "json" / "regex_rule.json"

def NFA_gen(input_pattern:str):
  syntax = _Syntax(regex_bnf_json_path, True)


  lalr1 = LALR1(syntax, States(), regex_bnf_json_path)

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
  result = ast_gen(result)
  return NFA(result)

def Toknizer(pattern:str|Path, input_str:str):
  if isinstance(pattern, str):
    nfa = NFA_gen(pattern)
  elif isinstance(pattern, Path):
    nfa = NFA(pattern)
  else:
    raise ValueError
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