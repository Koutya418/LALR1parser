import src.components.common.Syntax as Syntax
import src.components.common.States as States
import src.components.Lalr1 as Lalr1
from src.components.common.Data import EOF, Propagation_symbol
from pathlib import Path
import json
import pprint

base_dir = Path(__file__).resolve().parent
regex_bnf_file_path = base_dir / "src" / "rule" / "regex_rule.txt"
output_path = base_dir / "src" / "json" / "regex_rule.json"

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is EOF:
            return {
                "__type__": "EOF"
            }

        if obj is Propagation_symbol:
            return {
                "__type__": "Propagation_symbol",
            }

        return super().default(obj)

with output_path.open(mode="w", encoding="utf-8") as f:
  result:dict = {}
  syntax = Syntax._Syntax(regex_bnf_file_path)
  states = States.States()
  states.LR0_table_gen(syntax)
  states.lalr1_gen(syntax)
  lalr1 = Lalr1.LALR1(syntax, states)
  result["syntax"] = syntax.json_table_output()
  result["states"] = states.json_output()
  result["lalr1"] = lalr1.json_table_output()
  pprint.pprint(result.get("lalr1"))
  json.dump(result, f, indent=2, cls=CustomEncoder)