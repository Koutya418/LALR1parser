from . import Lexer
from .components.common import BNF_Tokenizer
from .components.regex.NFA import NFA, Regex_ret
from .components.common.Data import InputToken, EOF
from .components.Lalr1 import LALR1
from .components.common.Syntax import _Syntax, Syntax
from .components.common.States import States
from pathlib import Path
from . import SyntaxAstGenerator
from .components.common.Nodes import SyntaxTreeNode

base_dir = Path(__file__).resolve().parent

bnf_tokenizer_path = base_dir / "rule" / "syntax_rule_tokenizer.txt"
syntax_rule_bnf_path = base_dir / "rule" / "syntax_rule.txt"
tokenizer_file_path = base_dir / "tokenizer.txt"
bnf_file_path = base_dir / "bnf.txt"
file = base_dir / "test.txt"
tokenizer_tokenizer_file_path = base_dir / "json" / "Tokenizer_NFA.json"

def Tokenizer(tokenizer_path:Path, bnf_path:Path, file_path:Path, terms:set = None):
  result_pattern:list[str] = []
  with tokenizer_path.open(encoding='utf-8', mode='r') as f:
    input_str = f.read()
    tokens = Lexer.Toknizer(tokenizer_tokenizer_file_path, input_str)
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
  with file_path.open(encoding='utf-8', mode='r') as f:
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
  if terms is not None:
    reserved_word = terms
  else:
    result_bnf = BNF_Tokenizer.bnf_tokenizer(bnf_path)
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

def _parse(tokenizer_path:str, bnf_path:str, file_path:str):
  input = Tokenizer(tokenizer_path, bnf_path, file_path)
  syntax = _Syntax(bnf_path)
  states = States()
  states.LR0_table_gen(syntax)
  states.lalr1_gen(syntax)
  lalr1 = LALR1(syntax, states)
  input.append(EOF)
  result = lalr1.parse(input)
  return result

def parse(tokenizer_path:str, bnf_path:str, file_path:str) -> SyntaxTreeNode:
  syntax = _parse(bnf_tokenizer_path, syntax_rule_bnf_path, bnf_path)
  syntax = SyntaxAstGenerator.sytanx_ast_generator(syntax)
  syntax = Syntax(syntax)
  states = States()
  states.LR0_table_gen(syntax)
  states.lalr1_gen(syntax)
  lalr1 = LALR1(syntax, states)
  input = Tokenizer(tokenizer_path, bnf_path, file_path, syntax.symbols - syntax.nonterm_symbols)
  input.append(EOF)
  result = lalr1.parse(input)
  return result