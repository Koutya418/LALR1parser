from .Data import InputToken

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