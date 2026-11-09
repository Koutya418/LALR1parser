from pathlib import Path
import src.Parser as Parser
from test_cases.Tools import *

if __name__ == "__main__":
  base_dir = Path(__file__).resolve().parent
  examples_path = base_dir / "examples"
  clac_path = examples_path / "clac"
  rule_path = clac_path / "rule.txt"
  tokenizer_path = clac_path / "tokenizer.txt"
  file_path = clac_path / "test.txt"

  input_str = input("数式を入力してください: ")
  file_path.write_text(input_str, encoding="utf-8")
  result = Parser.parse(tokenizer_path, rule_path, file_path)
  result = AST_gen(result)
  result = AST_to_String(result)
  print(result)
