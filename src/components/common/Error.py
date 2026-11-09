from .Data import InputToken
from collections import deque
from .Syntax import Syntax

class ParserParseError(Exception):
  def __init__(self, message:str, tokens:list, row:int, start_index:int):
    self.start_index = start_index
    self.row = row
    self.tokens = tokens
    super().__init__(message)

  def __str__(self):
    result_string = ""
    for token in self.tokens[self.start_index:]:
      match token:
        case InputToken():
          if token.char == "\n":
            break
          result_string += token.char
        case str():
          result_string += token
    return f"\n{self.args[0]}\n[{self.row}]{result_string} <-"

class TokenizerTokenizeError(Exception):
  def __init__(self, message:str, tokens:list, row_count:int, error_index:int):
    self.tokens = tokens
    self.row_count = row_count
    self.error_index = error_index
    super().__init__(message)

  def __str__(self):
    result_string = ""
    end = len(self.tokens) + 1
    start = 0
    for i, token in enumerate(self.tokens[self.error_index:]):
      match token:
        case "\n":
          end = self.error_index + i
          break
        case _:
          result_string += token
    for i, token in enumerate(reversed(self.tokens[:self.error_index + 1])):
      match token:
        case "\n":
          start = self.error_index - i + 1
          break
        case _:
          result_string += token
    return f"\n{self.args[0]}\n[{self.row_count}]{"".join(self.tokens[start:self.error_index])} -> {"".join(self.tokens[self.error_index:end])}"

class ReduceReduceConflict(Exception):
  def __init__(self, message:str, table1:dict, table2:dict, la, state:int, syntax:Syntax):
    self.table1 = table1
    self.table2 = table2
    self.state = state
    self.la = la
    self.syntax = syntax
    super().__init__(message)

  def __str__(self):
    table1_string = self.syntax.rule_to_string(self.table1.get("value"))
    table2_string = self.syntax.rule_to_string(self.table2.get("value"))
    return f'''\n{self.args[0]}
Reduce/Reduce Conflict

State: {self.state}
Lookahead: {self.la}

Rule
  1, {table1_string}
  2, {table2_string}
'''