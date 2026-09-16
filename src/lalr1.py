
from dataclasses import dataclass, field
from collections import deque
import itertools, copy

import time

@dataclass(frozen=True)
class Rule:
  id: int
  le: str
  re: tuple[str, ...]

@dataclass(frozen=True)
class LR0Item:
  rule_id: int
  dot: int
  rules: tuple[Rule] = field(repr=False)

  def get_next_sym(self, n:int = 0):
    result = None
    rule = self.rules[self.rule_id]
    index = self.dot + n
    if len(rule.re) > index:
      result = rule.re[index]
    return result

  def get_next_item(self):
    result = None
    rule = self.rules[self.rule_id]
    if len(rule.re) > self.dot:
      result = LR0Item(self.rule_id, self.dot + 1, self.rules)
    return result

  def get_lalr1_re(self):
    result = self.rules[self.rule_id].re[self.dot + 1:] or None
    return result

  def show(self, start_add_str:str = "", end_add_str: str = ""):
    show_re = "".join(self.rules[self.rule_id].re)
    show_str = f"{start_add_str}{self.rules[self.rule_id].le} -> {show_re[:self.dot] + "・" + show_re[self.dot:]}{end_add_str}"
    print(f"{show_str}")

class Syntax:
  def __init__(self, syntax_file):
    self.rules: tuple[Rule]
    self.symbol_list: set
    self.nonterm_list: set
    self.non_term_to_rule: dict[str, tuple[int]]
    self.rules, self.symbol_list, self.nonterm_list, self.non_term_to_rule, = self.syntax_gen(syntax_file)
    self.nullable_syms: set = set(["<eps>"],)
    self.nullable_symbols_gen()
    self.first_set = self.first_set_gen()
    self.symbol_list.add("$")
    self.first_set["$"] = set(["$"])
    self.first_set["#"] = set(["#"])

  def __getitem__(self, key):
    if key is None:
      return None
    match key:
      case int() | slice():
        result = self.rules[key]
      case str():
        result = self.nonterm_to_rule(key)
    return result

  def nonterm_to_rule(self, term: str):
    result = None
    match self.get_symbol_type(term):
      case "nonterm":
        result = self.non_term_to_rule.get(term)
    return result

  def get_symbol_type(self, sym):
    result = None
    if sym in self.symbol_list:
      if sym in self.nonterm_list:
        result = "nonterm"
      else:
        result = "term"
    return result
  def syntax_gen(self, path: str):
    with open(path, "r", encoding='utf-8') as f:
      ignore_chars: list[str] = ["\n"]
      chars = [char for char in f.read() if char not in ignore_chars]
      chars: deque = deque(chars)
      rules: list[Rule] = []
      non_term_set: set[str] = set()
      symbol_set: set[str] = set()
      non_term_to_rule: dict[str, tuple] = {}
      current_syntax_token = ""
      syntax_token_stream: list = []
      old_current_char_type = 0
      is_defined_as_symbol = "::="
      syntax_char_type: dict[str, int] = {
        ";": 1,
        "|": 2,
        ":": 3,
        "=": 3,
        '"': 4,
        " ": 5,
      }
      while chars:
        current_char = chars[0]
        current_char_type = syntax_char_type.get(current_char, 0)
        if current_char_type != old_current_char_type and old_current_char_type != 5:
          syntax_token_stream.append(current_syntax_token)
          current_syntax_token = ""
        match current_char_type:
          case 1 | 2:
            current_syntax_token = current_char
          case 3:
            if "".join(list(itertools.islice(chars, 0, 3))) == is_defined_as_symbol:
              for _ in range(3):
                chars.popleft()
            current_syntax_token = is_defined_as_symbol
          case 4:
            syntax_token_stream.append(current_char)
            chars.popleft()
            current_char = chars[0]
            while syntax_char_type.get(current_char, 0) != 4:
              current_syntax_token += current_char
              chars.popleft()
              current_char = chars[0]
            syntax_token_stream.append(current_syntax_token)
            current_syntax_token = current_char
          case 0:
            current_syntax_token += current_char
        old_current_char_type = current_char_type
        chars.popleft()
      syntax_token_stream.append(current_char)
      syntax_token_stream: deque = deque(syntax_token_stream)
      le = None
      re: list = []
      le_to_rule_id: list = []
      while syntax_token_stream:
        current_token = syntax_token_stream.popleft()
        if le is None:
          le = current_token
          symbol_set.add(current_token)
          non_term_set.add(current_token)
          continue
        rule_id = len(rules)
        match current_token:
          case "|": 
            rules.append(Rule(rule_id, le, tuple(re)))
            le_to_rule_id.append(rule_id)
            re = []
          case ";":
            rules.append(Rule(rule_id, le, tuple(re)))
            le_to_rule_id.append(rule_id)
            non_term_to_rule[le] = tuple(le_to_rule_id)
            le_to_rule_id = []
            le = None
            re = []
          case "::=":
            pass
          case '"':
            current_token = syntax_token_stream.popleft()
            re.append(current_token)
            symbol_set.add(current_token)
            syntax_token_stream.popleft()
          case _:
            symbol_set.add(current_token)
            re.append(current_token)
      return tuple(rules), symbol_set , non_term_set, non_term_to_rule

  def first_set_gen(self):
    result: dict[str, set] = {}
    link: dict[str, set] = {}
    worklist: list[str] = []
    for sym in self.symbol_list - self.nonterm_list:
      result[sym] = set(sym)
    for rule in self.rules: #nullableを使ってfirst集合の繋がりのリストを作る。
      for sym in rule.re:
        if sym not in link:
          link[sym] = set()
        if self.is_nullable(sym) is None:
          continue
        if not self.is_nullable(sym):
          link[sym].add(rule.le)
          break
        if sym not in link:
          link[sym] = set()
        link[sym].add(rule.le)

    worklist: deque = deque(list(self.symbol_list - self.nonterm_list)) #ワークリストに終端記号全てを追加
    while len(worklist) > 0:
      work_sym = worklist.popleft()
      for link_sym in link.get(work_sym, []):
        if link_sym not in result:
          result[link_sym] = set()
        if result[work_sym] & result[link_sym] != result[work_sym]:
          worklist.append(link_sym)
        result[link_sym] |= result[work_sym]
    return result

  def nonterm_exp(self, sym: str, sym_set: set | None = None):
    if sym_set is None:
      sym_set = set()
    for rule in self.non_term_to_rule[sym]:
      if self[rule].re[0] != sym and sym not in sym_set:
        next_sym = self[rule].re[0]
        match self.get_symbol_type(next_sym):
          case "nonterm":
            sym_set |= self.nonterm_exp(next_sym, sym_set)
          case "term":
            sym_set.add(next_sym)
    return sym_set

  def is_nullable(self, key):
    result = key in self.nullable_syms
    return None if key is None else result

  def nullable_symbols_gen(self):
    old_nullable_syms: set = set()
    while self.nullable_syms != old_nullable_syms:
      old_nullable_syms = self.nullable_syms.copy()
      for rule in self.rules:
        if len(set(rule.re) & self.nullable_syms) == len(rule.re):
          self.nullable_syms.add(rule.le)

  def lalr1_first_set(self, re: tuple[str], la: set):
    result: set = set()
    all_nullable_flag = True
    for sym in re:
      if self.is_nullable(sym) is None:
        continue
      if not self.is_nullable(sym):
        result |= self.first_set[sym]
        all_nullable_flag = False
        break
      result |= self.first_set[sym]

    if all_nullable_flag:
      for sym in la:
        result |= self.first_set[sym]
    return result

#ツール系
def states_print(states: dict[int, dict[str, dict[str, int | str | LR0Item]]]):
  keys = states.keys()
  keys = list(keys)
  keys.sort()
  for i in keys:
    state = states.get(i)
    if state is None:
      continue
    for item_data in state.values():
      item = item_data.get("item")
      item.show(f"[I{i}] ")

def dict_in_list_append(d: dict[str | LR0Item, list], k, v):
  if k in d:
    d.get(k).append(v)
  else:
    d[k] = [v]
  return d

def LR0_clos(state: list[LR0Item], rules: Syntax):
  result: list[LR0Item] = copy.deepcopy(state)
  worklist: deque[LR0Item] = deque(result)
  while len(worklist) > 0:
    item = worklist.popleft()
    next_sym = item.get_next_sym()
    if next_sym is None:
      continue
    next_rules = rules[next_sym]
    if next_rules is None:
      continue
    for rule_id in next_rules:
      add_item = LR0Item(rule_id, 0, rules.rules)
      if add_item in result:
        continue
      result.append(add_item)
      worklist.append(add_item)
  return result

def LR0_next_core_gen(state:list[LR0Item], states: dict[int, frozenset[LR0Item]], core_to_state: dict[frozenset[LR0Item], int], worklist: deque[frozenset[LR0Item]]):
  sym_to_item: dict[str, set[LR0Item]] = {}
  for item in state:
    
    item_next_sym = item.get_next_sym()
    add_item = item.get_next_item()

    if item_next_sym is None:
      continue
    if add_item is None:
      continue

    if item_next_sym not in sym_to_item:
      sym_to_item[item_next_sym] = set()
    sym_to_item[item_next_sym].add(add_item)

  for core in sym_to_item.values():
    add_core = frozenset(core)
    if add_core in core_to_state:
      continue
    add_core_id = len(core_to_state)
    states[add_core_id] = add_core
    core_to_state[add_core] = add_core_id
    worklist.append(add_core)

def LR0_while(states: dict[int, frozenset[LR0Item]], core_to_state: dict[frozenset[LR0Item], int], rules: Syntax) -> dict[int, frozenset[LR0Item]]:
  result: dict[int, frozenset[LR0Item]] = copy.deepcopy(states)
  worklist: deque[frozenset[LR0Item]] = deque(result.values())
  while len(worklist) > 0:
    state = worklist.popleft()
    closure = LR0_clos(list(state), rules)
    LR0_next_core_gen(closure, result, core_to_state, worklist)
  return result

def LR1_clos(state: list[LR0Item], item_to_la: dict[LR0Item, set], rules: Syntax):
  result: list[LR0Item] = copy.deepcopy(state)
  link_dict: dict[LR0Item, set[LR0Item]] = {}
  worklist: deque[LR0Item] = deque(state)
  while len(worklist) > 0:
    item = worklist.popleft()
    item_la = item_to_la.get(item)
    item_next_sym = item.get_next_sym()
    if rules[item_next_sym] is None:
      continue
    for rule_id in rules[item_next_sym]:
      add_item = LR0Item(rule_id, 0, rules.rules)
      if add_item not in link_dict:
        link_dict[add_item] = set()
      add_item_re = rules.lalr1_first_set(item.get_lalr1_re() or tuple(), item_la)
      link_item = set([item])
      if link_dict.get(item) is not None:
        link_item = link_dict.get(item)
      link_dict[add_item] |= link_item
      if add_item not in result:
        result.append(add_item)
        item_to_la[add_item] = set()
      if item_to_la[add_item] & add_item_re != add_item_re:
        worklist.append(add_item)
      item_to_la[add_item] |= add_item_re
  return result, link_dict

def LALR1_state_gen(states: dict[int, frozenset[LR0Item]], states_to_la: dict[int, dict[LR0Item, set]], rules: Syntax):
  result: dict[int, frozenset[LR0Item]] = {}
  link_result: dict[int, dict[LR0Item, set[LR0Item]]] = {}
  for i in range(len(states)):
    state = states[i]
    item_to_la = states_to_la[i]
    ret, link_dict = LR1_clos(list(state), item_to_la, rules)
    result[i] = frozenset(ret)
    link_result[i] = link_dict
  return result, link_result

def link_search(in_item: LR0Item, clos_link: dict[LR0Item, set[LR0Item]], item_to_la:dict[LR0Item, set], items: set = None):
  if items is None:
    items = set()
    items.add(in_item)
  result: set = copy.deepcopy(items)
  flag = False
  sub_items = set()
  for item in items:
    if item_to_la.get(item) is None:
      sub_items.add(item)
      continue
    if '#' not in item_to_la.get(item):
      sub_items.add(item)
  items -= sub_items

  for item in items:
    if clos_link.get(item) is None:
      continue
    result |= clos_link.get(item)
    result -= set([item])
    flag = True
  if flag:
    result = link_search(in_item, clos_link, item_to_la, result)
  return result

def LALR1_link_gen(states: dict[int, frozenset[LR0Item]], core_to_state: dict[frozenset[LR0Item], int], states_to_la: dict[int, dict[LR0Item, set]], closs_link: dict[int, dict[LR0Item, set[LR0Item]]], rules: Syntax):
  result: dict[int, dict[LR0Item, dict[int, set[LR0Item]]]] = {}
  result_na_la: dict[int, dict[LR0Item, set]] = {}
  for i in range(len(states)):
    result[i] = {}
    state = states[i]
    item_to_la = states_to_la[i]
    clos_link = closs_link[i]
    sym_to_core: dict[str, set[LR0Item]] = {}
    for item in state:
      next_sym = item.get_next_sym()
      if next_sym is None:
        continue
      if next_sym not in sym_to_core:
        sym_to_core[next_sym] = set()
      sym_to_core[next_sym].add(item)
    for items in sym_to_core.values():
      core: set = set()
      for item in items:
        next_item = item.get_next_item()
        if next_item is None:
          continue
        core.add(next_item)
      link_state_id = core_to_state[frozenset(core)]
      for item in items:
        next_item = item.get_next_item()
        if '#' in item_to_la[item]:
          link_items = link_search(item, clos_link, item_to_la)
          for link_item in link_items:
            if link_item not in result[i]:
              result[i][link_item] = {}
            if link_state_id not in result[i][link_item]:
              result[i][link_item][link_state_id] = set()
            if next_item is None:
              continue
            result[i][link_item][link_state_id].add(next_item)
      for item in items:
        next_item = item.get_next_item()
        if len(item_to_la.get(item, set()) - set(['#'])) <= 0:
          continue
        if next_item is None:
          continue
        if link_state_id not in result_na_la:
          result_na_la[link_state_id] = {}
        if next_item not in result_na_la[link_state_id]:
          result_na_la[link_state_id][next_item] = set()
        result_na_la[link_state_id][next_item] |= item_to_la.get(item, set()) - set(['#'])
  return result, result_na_la

def LALR1_prop(states: dict[int, frozenset[LR0Item]], states_to_la: dict[int, dict[LR0Item, set]], link: dict[int, dict[LR0Item, dict[int, set[LR0Item]]]], lagen: dict[int, dict[LR0Item, set]], root_item: LR0Item):
  for state_id, state in states.items():
    states_to_la[state_id] = {}
    for item in state:
      states_to_la[state_id][item] = set()

  states_to_la[0][root_item] |= set(['$'])
  worklist: deque[tuple[int, LR0Item]] = deque()
  worklist.append(tuple([0, root_item]))

  for state_id, link_data in lagen.items():
    for item, la in link_data.items():
      states_to_la[state_id][item] |= la
      if link.get(state_id).get(item) is None:
        continue
      worklist.append(tuple([state_id, item]))

  while len(worklist) > 0:
    item_data = worklist.popleft()
    link_root_id, link_root_item = item_data
    prop_item_data = link[link_root_id][link_root_item]
    for prop_state_id, prop_items in prop_item_data.items():
      for prop_item in prop_items:
        prop_item_la = states_to_la[prop_state_id][prop_item]
        link_root_la = states_to_la[link_root_id][link_root_item]
        if prop_item_la & link_root_la == link_root_la :
          continue
        prop_item_la |= link_root_la 
        if prop_state_id not in link:
          continue
        if prop_item not in link[prop_state_id]:
          continue
        worklist.append(tuple([prop_state_id, prop_item]))

####パーサー
@dataclass
class Token:
  token_type: str
  token_sym: str
  next_token: list

  def show(self, nest = 0):
    indent = ""
    for _ in range(nest):
        indent += " "
    print(indent + self.token_sym)
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

class Parser_Base:
  def __init__(self, rules: Syntax):
    self.stack = []
    self.result = []
    self.rules = rules
  def parse(self, input):
    return self.result

class LALR1_Parser(Parser_Base):
  def __init__(self, rules, states, core_to_state, states_to_la):
    super().__init__(rules)
    self.table = self.table_gen(states, core_to_state, states_to_la)
    self.states = states

  def parse(self, input: list, init_flag: bool = False):
    if init_flag:
      self.stack.append(0)
      input = list(reversed(input))
    while len(input) > 0:
      state = self.table.get(self.stack[-1]).get(input[-1])
      if state is None and len(self.stack) <= 0:
        print(f"{input}を解析中にエラーが発生しました, {self.stack[-1]}, {input[-1]}")
      operation = state.get("operation")
      action_id = state.get("value")
      match operation:
        case "shift":
          input.pop()
          self.stack.append(action_id)
        case "reduce":
          self.result.append(action_id)
          re_len = len(self.rules[action_id].re)
          goto_le = self.rules[action_id].le
          for _ in range(re_len):
            self.stack.pop()
          goto_id = self.table.get(self.stack[-1]).get(goto_le).get("value")
          self.stack.append(goto_id)
        case "acc":
          break
    return self.result

  def table_write(self, table, i, sym, operation):
    if i not in table:
      table[i] = {}
    if sym not in table[i]:
      table[i][sym] = {}
    else:
      print(f"[{i}][{sym}]で生成規則の上書きが発生しました")
    table[i][sym] = operation

  def table_gen(self, states:dict[int, frozenset[LR0Item]], core_to_state: dict[frozenset, int], states_to_la: dict[int, dict[LR0Item, set]]):
    result: dict[int, dict[str, dict[str, str]]] = {}
    end_item = LR0Item(0, len(self.rules[0].re), self.rules.rules)
    for i in range(len(states)):
      state = states[i]
      item_to_la = states_to_la[i]
      state_clos, _ = LR1_clos(list(state), item_to_la, self.rules)
      sym_to_core: dict[str, set[LR0Item]] = {}
      for item in state_clos:
        next_sym = item.get_next_sym()
        if item == end_item:
          self.table_write(result, i, '$', {"operation": "acc", "value": 'acc'})
        if next_sym is None:
          if item.rule_id <= 0:
            continue
          for sym in states_to_la[i][item]:
            self.table_write(result, i, sym, {"operation": "reduce", "value": item.rule_id})
        if next_sym is None:
          continue
        if next_sym not in sym_to_core:
          sym_to_core[next_sym] = set()
        sym_to_core[next_sym].add(item.get_next_item())
      for sym, items in sym_to_core.items():
        operation = None
        match self.rules.get_symbol_type(sym):
          case "nonterm":
            operation = "goto"
          case "term":
            operation = "shift"
        self.table_write(result, i, sym, {"operation": operation, "value": core_to_state[frozenset(items)]})
    return result
    
class Parser:
  def __init__(self, rules: Syntax):
    self.parser_dict: dict[str, Parser_Base] = {}
    self.rules = rules

  def parse(self, input: list[str], parser_type: str):
    parser = self.parser_dict.get(parser_type)
    return parser.parse(input, True)

  def parser_register(self, name: str, parser: Parser_Base):
    if name not in self.parser_dict:
      self.parser_dict[name] = parser

  def tree_gen(self, ret: list[int], text: list) -> Token:
    rule = self.rules[ret.pop()]
    re = reversed(rule.re)
    ret_token = Token(self.rules.get_symbol_type(rule.le), rule.le, [])
    for sym in re:
      if sym == text[-1]:
        add_item = None
        match self.rules.get_symbol_type(sym):
          case "nonterm":
            add_item = Token(self.rules.get_symbol_type(sym), sym, [text[-1]])
          case "term":
            add_item = sym
        ret_token.next_token.append(add_item)
        text.pop()
      else:
        ret_token.next_token.append(self.tree_gen(ret, text))
    ret_token.next_token = list(reversed(ret_token.next_token))
    return ret_token

def LALR1(file_path: str, input: str):
  start = time.perf_counter()
  #初期化処理
  Rules = Syntax(file_path)

  root_item = LR0Item(0, 0, Rules.rules)
  root_core_set = frozenset([root_item])
  states: dict[int, frozenset[LR0Item]] = {}
  core_to_state: dict[frozenset[LR0Item], int] = {}
  states[0] = root_core_set
  core_to_state[root_core_set] = 0

  #LR(0)解析表の作成
  LR0_states = LR0_while(states, core_to_state, Rules)

  #LALR(1)用の初期化処理
  states_to_la: dict[int, dict[LR0Item, set]] = {} #伝搬計算用

  for state_id, state in LR0_states.items():
    states_to_la[state_id] = {}
    for item in state:
      states_to_la[state_id][item] = set(['#'])
  clos_link: dict[int, dict[LR0Item, set[LR0Item]]]
  LALR1_states, clos_link = LALR1_state_gen(LR0_states, states_to_la, Rules)

  LALR1_link, LALR1_na_lagen = LALR1_link_gen(LALR1_states, core_to_state, states_to_la, clos_link, Rules)

  LALR1_states_to_la: dict[int, dict[LR0Item, set]] = {} #解析表作成用

  LALR1_prop(LR0_states, LALR1_states_to_la, LALR1_link, LALR1_na_lagen, root_item)

  LALR1_states, _ = LALR1_state_gen(LR0_states, LALR1_states_to_la, Rules)

  parser = Parser(Rules)

  parser.parser_register('LALR1', LALR1_Parser(Rules, LALR1_states, core_to_state, LALR1_states_to_la))

  text = list(input)
  text.append('$')
  tokens = []
  for i in text:
    add_token = i
    if i == " ":
      add_token = "<eps>"
    tokens.append(add_token)

  result = parser.parse(tokens, "LALR1")

  end = time.perf_counter()

  result = parser.tree_gen(result, tokens[:-1])
  print(f"実行時間 {end - start}")
  return result