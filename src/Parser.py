import Lexer
import os
import components.common.BNF_Tokenizer as BNF_Toknizer
from components.regex.NFA import NFA, Regex_ret
from components.common.Data import InputToken, EOF
from components.Lalr1 import LALR1
from components.common.Syntax import Syntax
from components.common.States import States

cwd = os.getcwd()

def Tokenizer(tokenizer_path:str, file_path:str, bnf_path:str):
  result_pattern:list[str] = []
  with open(cwd + tokenizer_path, encoding='utf-8', mode='r') as f:
    input_str = f.read()
    tokens = Lexer.Toknizer("""/w*|".*!"|''',*'''| |\n|=""", input_str)
    tokens = [token for token in tokens if token != " " and token != "\n"]
    
    rule = []
    old_token = None
    for token in tokens:
      if old_token is None:
        old_token = token
        continue
      if token == "=":
        rule.append(old_token)
      else:
        if token[0:3] == "'''":
          add_token = token[3:-3]
        else:
          add_token = token[1:-1]
        rule.append(add_token)
        result_pattern.append(rule)
        old_token = None
        rule = []

  result_strings = []
  with open(cwd + file_path, encoding='utf-8', mode='r') as f:
    input_str = f.read()
    toknizer_pattern = ""
    ignore_chars:list = []
    for pattern in result_pattern:
      rule_name = pattern[0]
      rule_chars = pattern[1].split("|")
      for i, char in enumerate(rule_chars):
        if char == "\\n":
          rule_chars[i] = "\n"
      if rule_name == "skip":
        ignore_chars = rule_chars
      rule_chars = "|".join(rule_chars)
      toknizer_pattern += rule_chars
      toknizer_pattern += "|"
    toknizer_pattern = toknizer_pattern[:-1]
    tokens = Lexer.Toknizer(toknizer_pattern, input_str)
    result_strings = [token for token in tokens if token not in ignore_chars]

  tokens = []
  NFAs:list[tuple[str, NFA]] = []
  for pattern in result_pattern:
    NFAs.append([pattern[0], Lexer.NFA_gen(pattern[1])])
  for string in result_strings:
    for nfa in NFAs:
      result:Regex_ret = nfa[1].reg(string)
      if result.accepts == string:
        tokens.append([nfa[0], string])
        break

  reserved_word = []
  result_tokens:list = []
  result_bnf = BNF_Toknizer.bnf_tokenizer(bnf_path)
  for token in result_bnf:
    if token[0] == '"' and token[-1] == '"':
      reserved_word.append(token[1:-1])
  for token_data in tokens:
    token_type = token_data[0]
    token = token_data[1]
    if token in reserved_word:
      result_tokens.append(token)
    else:
      result_tokens.append(InputToken(token_type, token))
  return result_tokens

input = Tokenizer('/src/tokenizer.txt', '/src/test.txt', '/src/bnf.txt')
syntax = Syntax('/src/bnf.txt')
states = States()
states.LR0_table_gen(syntax)
states.lalr1_gen(syntax)
lalr1 = LALR1(syntax, states)
input.append(EOF)
result = lalr1.parse(input)
result = lalr1.tree_gen(result, input[:-1])
result.show()