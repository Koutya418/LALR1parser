from .Data import InputToken
from collections import deque

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

class TokenizerTokneizeError(Exception):
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