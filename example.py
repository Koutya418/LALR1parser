from pathlib import Path
import src.Parser as Parser
from tools.Tools import *
from src.components.common.Error import *
import sys

if __name__ == "__main__":
  base_dir = Path(__file__).resolve().parent
  examples_path = base_dir / "examples"
  calc_path = examples_path / "calc"
  rule_path = calc_path / "rule.txt"
  tokenizer_path = calc_path / "tokenizer.txt"
  file_path = calc_path / "test.txt"

  input_str = input("数式を入力してください: ")
  try:
    result = Parser.parse(tokenizer_path, rule_path, input_str)
  except ParserParseError as e:
    print(str(e))
    sys.exit(1)
  except TokenizerTokenizeError as e:
    print(str(e))
    sys.exit(1)
  except ReduceReduceConflict as e:
    print(str(e))
    sys.exit(1)
  result = AST_gen(result)
  result = AST_to_String(result)
  print(result)
