from .Data import Rule, Propagation_symbol, EOF
from .BNF_Tokenizer import bnf_tokenizer
from collections import deque
from dataclasses import dataclass
from .Nodes import *
import pprint
from pathlib import Path
import json

def object_hook(obj):
    if obj.get("__type__") == "EOF":
        return EOF
    elif obj.get("__type__") == "Propagation_symbol":
      return Propagation_symbol

    return obj

class _Syntax:
  def __init__(self, rule, json_load_flag = None):
    self.rules:tuple[Rule]
    self.symbols:set[str]
    self.nonterm_symbols:set[str]
    self.nonterm_to_rules:dict[str, set]
    if json_load_flag:
      self.json_table_load(rule)
    else:
      (
        self.rules,
        self.symbols,
        self.nonterm_symbols,
        self.nonterm_to_rules
      ) = self.gen_rule(rule)
      self.nullable_symbols:set = set(["<eps>"])
      self.nullable_symbols_gen()
      self.first_set:dict[str, set] = self.first_set_gen()
      self.first_set[Propagation_symbol] = set([Propagation_symbol])
      self.first_set[EOF] = set([EOF])

  def gen_rule(self, path):
    result_rules:list = []
    result_symbols:set = set()
    result_nonterm_symbols:set = set()
    result_nonterm_to_rules:dict[str, set] = {}
    bnf_stream = bnf_tokenizer(path)
    old_bnf_token = None
    le = None
    rule_id = None
    re:list = []
    for bnf_token in bnf_stream:
      if old_bnf_token is None:
        old_bnf_token = bnf_token
        continue
      elif bnf_token == "::=" and old_bnf_token is not None:
        le = old_bnf_token
        result_symbols.add(le)
        result_nonterm_symbols.add(le)
        continue
      elif le is not None:
        match bnf_token:
          case "|" | ";":
            rule_id = len(result_rules)
            if le not in result_nonterm_to_rules:
              result_nonterm_to_rules[le] = set()
            result_nonterm_to_rules[le].add(rule_id)
            result_rules.append(Rule(rule_id, le, tuple(re)))
            re = []
            if bnf_token == ";":
              le = None
          case _:
            append_re = bnf_token
            if bnf_token[-1] == bnf_token[0] == '"':
              append_re = bnf_token[1:-1]
            if append_re == "<eps>":
              continue
            result_symbols.add(append_re)
            re.append(append_re)
      old_bnf_token = bnf_token
    return result_rules, result_symbols, result_nonterm_symbols, result_nonterm_to_rules

  def nullable_symbols_gen(self):
    old_nullable_symbols: set = set()
    while self.nullable_symbols != old_nullable_symbols:
      old_nullable_symbols = self.nullable_symbols.copy()
      for rule in self.rules:
        if len(set(rule.re) & self.nullable_symbols) == len(rule.re):
          self.nullable_symbols.add(rule.le)

  def is_nullable(self, key):
    result = key in self.nullable_symbols
    return None if key is None else result

  def json_table_output(self):
    result:dict = {}
    result["rules"] = {}
    result["symbols"] = tuple(self.symbols)
    result["nonterm_symbols"] = tuple(self.nonterm_symbols)
    result["nonterm_to_rule"] = {}
    result["nullable_symbols"] = tuple(self.nullable_symbols)
    result["first_set"] = {}
    result["rules"] = [{"rule_id":rule.rule_id, "le":rule.le, "re":rule.re, "prec":rule.prec} for rule in self.rules]
    result["nonterm_to_rule"] = [{"nonterm":nonterm, "rules":tuple(rules)} for nonterm, rules in self.nonterm_to_rules.items()]
    result["first_set"] = [{"symbol":symbol, "symbol_set":tuple(symbol_set)} for symbol, symbol_set in self.first_set.items()]
    return result

  def json_table_load(self, path:Path):
    with path.open(mode="r", encoding="utf-8") as f:
      data:dict = json.load(f, object_hook=object_hook)
      data:dict[str, list[dict]|set|dict] = data.get("syntax")
      self.symbols = data.get("symbols")
      self.nonterm_symbols = data.get("nonterm_symbols")
      self.nullable_symbols = data.get("nullable_symbols")
      self.rules = [Rule(rule.get("rule_id"), rule.get("le"), tuple(rule.get("re")), rule.get("prec")) for rule in data.get("rules")]
      self.nonterm_to_rules = {}
      self.first_set = {}
      for item in data.get("nonterm_to_rule"):
        self.nonterm_to_rules[item.get("nonterm")] = set(item.get("rules"))
      for item in data.get("first_set"):
        self.first_set[item.get("symbol")] = set(item.get("symbol_set"))

  def first_set_gen(self):
    result:dict[str, set] = {}
    link: dict[str, set] = {}
    for symbol in self.symbols - self.nonterm_symbols:
      result[symbol] = set([symbol])
    for rule in self.rules: #nullableを使ってfirst集合の繋がりのリストを作る。
      for symbol in rule.re:
        if symbol not in link:
          link[symbol] = set()
        if self.is_nullable(symbol) is None:
          continue
        if not self.is_nullable(symbol):
          link[symbol].add(rule.le)
          break
        if symbol not in link:
          link[symbol] = set()
        link[symbol].add(rule.le)

    worklist:deque = deque(list(self.symbols - self.nonterm_symbols)) #ワークリストに終端記号全てを追加
    while len(worklist) > 0:
      work_symbol = worklist.popleft()
      for link_symbol in link.get(work_symbol, []):
        if link_symbol not in result:
          result[link_symbol] = set()
        if result[work_symbol] & result[link_symbol] != result[work_symbol]:
          worklist.append(link_symbol)
        result[link_symbol] |= result[work_symbol]
    return result

  def lalr1_first_set(self, re: tuple[str], la: set):
    result: set = set()
    all_nullable_flag = True
    for symbol in re:
      if self.is_nullable(symbol) is None:
        continue
      if not self.is_nullable(symbol):
        result |= self.first_set[symbol]
        all_nullable_flag = False
        break
      result |= self.first_set[symbol]

    if all_nullable_flag:
      for symbol in la:
        result |= self.first_set[symbol]
    return result

  def is_term(self, symbol):
    result = None
    if symbol in self.symbols:
      result = symbol not in self.nonterm_symbols
    return result

  def is_nonterm(self, symbol):
    result = None
    if symbol in self.symbols:
      result = symbol in self.nonterm_symbols
    return result

  def get_symbol_type(self, symbol):
    result = self.is_term(symbol)
    if result is None:
      result = None
    elif result:
      result = "term"
    else:
      result = "nonterm"
    return result

  def get_rule(self, key:int):
    result = None
    if type(key) == int and len(self.rules) > key:
      result = self.rules[key]
    return result

  def get_nonterm_to_rule_id(self, key:str):
    result = None
    if self.is_nonterm(key):
      result = self.nonterm_to_rules.get(key)
    return result

  def rule_to_string(self, rule_id:int):
    rule = self.get_rule(rule_id)
    if rule is None:
      return ""
    result = f"{rule.le} ::="
    for symbol in rule.re:
      result += " "
      result += symbol
    return result

class Syntax(_Syntax):
  def __init__(self, rule):
    self.rules:tuple[Rule]
    self.symbols:set[str]
    self.nonterm_symbols:set[str]
    self.nonterm_to_rules:dict[str, set]
    self.term_precedences:dict[str, dict[str, int|str]]
    (
      self.rules,
      self.symbols,
      self.nonterm_symbols,
      self.nonterm_to_rules,
      self.term_precedences
    ) = self.gen_rule(rule)
    self.nullable_symbols:set = set(["<eps>"])
    self.nullable_symbols_gen()
    self.first_set:dict[str, set] = self.first_set_gen()
    self.first_set[Propagation_symbol] = set([Propagation_symbol])
    self.first_set[EOF] = set([EOF])

  def gen_rule(self, node:SyntaxNode):
    result_rules:list[Rule] = []
    result_symbols:set = set()
    result_nonterm_symbols:set = set()
    result_nonterm_to_rules:dict[str, set] = {}
    result_term_precedences:dict[str, dict[str, int|str]] = {}
    precedence = 0
    if not isinstance(node, SyntaxNode):
      raise ValueError
    for rules in node.rules:
      match rules:
        case PrecDefinitionNode():
          associativity = None
          match rules.prec:
            case "%left":
              associativity = "left"
            case "%right":
              associativity = "right"
            case "%nonassoc":
              associativity = "nonassoc"
          for symbol in rules.symbols:
            if symbol in result_term_precedences:
              raise ValueError
            result_term_precedences[symbol] = {"precedence":precedence, "associativity":associativity}
          precedence += 1
        case RuleDefinitionNode():
          le = rules.lhs
          result_symbols.add(le)
          result_nonterm_symbols.add(le)
          for rule in rules.rules:
            if not isinstance(rule, RuleNode):
              raise ValueError
            re = rule.rule_items
            if "<eps>" in re:
              re = [symbol for symbol in re if symbol != "<eps>"]
            result_symbols |= set(re)
            rule_id = len(result_rules)
            if le not in result_nonterm_to_rules:
              result_nonterm_to_rules[le] = set()
            result_nonterm_to_rules[le].add(rule_id)
            result_rules.append(Rule(rule_id, le, tuple(re), rule.prec))
    terms = result_symbols - result_nonterm_symbols
    for rule in result_rules:
      if rule.prec is not None:
        rule.prec = result_term_precedences.get(rule.prec)
        continue
      if not (set(rule.re) & terms):
        continue
      for symbol in reversed(rule.re):
        if symbol in terms:
          rule.prec = result_term_precedences.get(symbol)
          break
    return result_rules, result_symbols, result_nonterm_symbols, result_nonterm_to_rules, result_term_precedences