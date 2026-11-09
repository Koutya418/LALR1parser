import src.Parser as Parser
import test.Tools as Tools
import unittest
from src.components.common.Error import *

from pathlib import Path

class Test(unittest.TestCase):
  def test_valid_cases(self):
    base_dir = Path(__file__).resolve().parent
    test_dir = base_dir / "test" / "valid_case"
    for item in test_dir.iterdir():
      if not item.is_dir():
        continue
      if item.name == "__pycache__":
        continue
      test_dir = item
      case_dir = test_dir / "case"
      tokenizer_file = test_dir / "tokenizer.txt"
      bnf_file = test_dir / "rule.txt"
      for case in case_dir.iterdir():
        if not case.is_dir():
          continue
        test_file = case / "test.txt"
        result = Parser.parse(tokenizer_file, bnf_file, test_file)
        result = Tools.AST_gen(result)
        result = Tools.AST_to_String(result)
        answer_file = case / "answer.txt"
        with answer_file.open(mode="r", encoding="utf-8") as f:
          answer = f.read()
          if answer == "<eps>":
            answer = None
          self.assertEqual(answer, result, msg=f"test:{test_dir.name} case:{case.name}")

  def test_parse_error_cases(self):
    base_dir = Path(__file__).resolve().parent
    test_dir = base_dir / "test" / "parse_error"
    for item in test_dir.iterdir():
      if not item.is_dir():
        continue
      if item.name == "__pycache__":
        continue
      test_dir = item
      case_dir = test_dir / "case"
      tokenizer_file = test_dir / "tokenizer.txt"
      bnf_file = test_dir / "rule.txt"
      for case in case_dir.iterdir():
        if not case.is_dir():
          continue
        test_file = case / "test.txt"
        with self.assertRaises(ParserParseError, msg=f"test:{test_dir.name} case:{case.name}") as exc:
          result = Parser.parse(tokenizer_file, bnf_file, test_file)
          result = Tools.AST_gen(result)
          result = Tools.AST_to_String(result)
        answer_file = case / "answer.txt"
        with answer_file.open(mode="r", encoding="utf-8") as f:
          answer = f.read()
          if answer == "<eps>":
            answer = None
          self.assertEqual(str(exc.exception), answer, msg=f"test:{test_dir.name} case:{case.name}")

if __name__ == '__main__':
    unittest.main()