from __future__ import annotations
from dataclasses import dataclass
from collections import deque

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components.common.Syntax import Syntax

@dataclass(frozen=True)
class Propagation_symbol:
  pass

@dataclass(frozen=True)
class EOF:
  pass

@dataclass(frozen=True)
class Rule:
  rule_id: int
  le: str
  re: tuple[str, ...]

@dataclass
class Token:
  token_type: str
  token_sym: str
  next_token: list

  def show(self, nest = 0):
    indent = ""
    for _ in range(nest):
        indent += " "
    print(f"{indent}{self.token_sym}")
    for token in self.next_token:
      match token:
        case str():
          print(indent + " " + token)
        case Token():
          token.show(nest + 1)
  def show2(self, nest = 0):
    inc = 0
    indent = ""
    for _ in range(nest):
        indent += " "
    if len(self.next_token) > 1:
      print(indent + self.token_sym)
      inc = 1
    for token in self.next_token:
      match token:
        case str():
          print(indent + " " + token)
        case Token():
          token.show2(nest + inc)

@dataclass(frozen=True)
class LR0Item:
  rule_id:int
  dot:int

  def next_symbol(self, syntax:Syntax):
    rule = syntax.get_rule(self.rule_id)
    result = None
    if len(rule.re) > self.dot:
      result = rule.re[self.dot]
    return result

  def next_item_gen(self, syntax:Syntax):
    rule = syntax.get_rule(self.rule_id)
    result = None
    if len(rule.re) > self.dot:
      result = LR0Item(self.rule_id, self.dot + 1)
    return result

  def get_symbol(self, syntax:Syntax, index:int):
    rule = syntax.get_rule(self.rule_id)
    result = None
    if len(rule.re) > self.dot + index:
      result = rule.re[self.dot + index]
    return result

  def get_lalr1_re(self, syntax:Syntax):
    rule = syntax.get_rule(self.rule_id)
    result = None
    if len(rule.re) > self.dot + 1:
      result = rule.re[self.dot + 1:]
    return result

  def show(self, syntax:Syntax, front:str = None):
    rule = syntax.get_rule(self.rule_id)
    print(f"{front}[{self.rule_id}] {rule.le} -> {"".join(rule.re[:self.dot])}・{"".join(rule.re[self.dot:])}")

class State:
  def __init__(self, core:frozenset[LR0Item]):
    self.core:frozenset[LR0Item] = core
    self.items = list(core)
    self.la:dict[LR0Item, set] = {}

  def lr0_closure(self, syntax:Syntax):
    next_state_cores:dict[str, set[LR0Item]] = {}
    worklist:deque[LR0Item] = deque(self.core)
    while len(worklist) > 0:
      item = worklist.popleft()
      next_symbol = item.next_symbol(syntax)
      if next_symbol is None:
        continue
      next_rule_ids = syntax.get_nonterm_to_rule_id(next_symbol)
      if next_rule_ids is None:
        continue
      for next_rule_id in next_rule_ids:
        add_item = LR0Item(next_rule_id, 0)
        if add_item not in self.items:
          self.items.append(add_item)
          worklist.append(add_item)
    for item in self.items:
      next_symbol = item.next_symbol(syntax)
      if next_symbol is None:
        continue
      next_item = item.next_item_gen(syntax)
      if next_item is None:
        continue
      if next_symbol not in next_state_cores:
        next_state_cores[next_symbol] = set()
      next_state_cores[next_symbol].add(next_item)
    return next_state_cores

  def la_init(self):
    self.la = {}

  def la_set(self, item:LR0Item, la:set):
    self.la[item] = set()
    self.la[item] = la

  def la_add(self, item:LR0Item, la:set):
    if item not in self.la:
      self.la[item] = set()
    self.la[item] |= la

  def lr1_closure(self, syntax:Syntax):
    next_state_cores:dict[str, set[LR0Item]] = {}
    links:dict[LR0Item, set[LR0Item]] = {}
    spontaneous:dict[LR0Item, set[str]] = {}
    for core_item in self.core:
      links[core_item] = set([core_item])
    worklist:deque[LR0Item] = deque(self.core)
    while len(worklist) > 0:
      item = worklist.popleft()
      item_la = self.la.get(item)
      next_symbol = item.next_symbol(syntax)
      if next_symbol is None:
        continue
      next_rule_ids = syntax.get_nonterm_to_rule_id(next_symbol)
      if next_rule_ids is None:
        continue
      for next_rule_id in next_rule_ids:
        add_item = LR0Item(next_rule_id, 0)
        add_item_la = syntax.lalr1_first_set(item.get_lalr1_re(syntax) or tuple(), item_la)
        if Propagation_symbol in add_item_la: #伝搬記号があるアイテムの追跡
          if add_item not in links:
            links[add_item] = set()
          link_items = set([item])
          if item in links:
            link_items = links[item]
          links[add_item] |= link_items #親アイテムがリンクにある場合に親アイテムのリンクを追加する実装にすることで、コアアイテムからのリンクを生成
        add_flag = False
        if add_item not in self.items:
          self.items.append(add_item)
          add_flag = True
        if add_item not in self.la:
          self.la[add_item] = set()
          add_flag = True
        if self.la[add_item] & add_item_la != add_item_la:
          self.la[add_item] |= add_item_la
          add_flag = True
        if add_flag:
          worklist.append(add_item)

    for item in self.items:
      next_symbol = item.next_symbol(syntax)
      if next_symbol is None:
        continue
      next_item = item.next_item_gen(syntax)
      if next_item is None:
        continue
      if next_symbol not in next_state_cores:
        next_state_cores[next_symbol] = set()
      next_state_cores[next_symbol].add(next_item)
      if Propagation_symbol in self.la[item] and len(self.la[item] - set([Propagation_symbol])) > 0: #自然発生した記号の追跡
        if next_item not in spontaneous:
          spontaneous[next_item] = set()
        spontaneous[next_item] |= self.la[item] - set([Propagation_symbol])
    return next_state_cores, links, spontaneous

class InputToken:
  def __init__(self, tokentype, char):
    self.tokentype = tokentype
    self.char = char