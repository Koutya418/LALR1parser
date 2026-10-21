from dataclasses import dataclass
from collections import deque
from components.common.Data import InputToken
import json, os

cwd = os.getcwd()
bnf_json_path = "/src/components/common/json/regex_nfa.json"

@dataclass
class NFA_state:
  sym: str|None
  goto: set[int]

@dataclass
class NFA_ret:
  start: int
  end: int

@dataclass
class Regex_ret:
  accepts: list
  count: int
  return_value: int

@dataclass
class Regex_state:
  state: int

class Bnf_nfa:
  def __init__(self, path):
    self.table:dict[int, NFA_state] = {}
    self.end_id:int
    self.load(path)
    self.class_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    self.class_lower_alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    self.class_upper_alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

  def load(self, path):
    with open(cwd + path, mode="rt", encoding="utf-8") as f:
      load_json = json.load(f)
      self.end_id = load_json["end_id"]
      load_table:dict = load_json["table"]
      for key, value in load_table.items():
        self.table[int(key)] = NFA_state(value["sym"], set(value["goto"]))

  def literal_gen(self, in_sym: str | InputToken):
    id0 = len(self.table)
    sym = in_sym
    if type(in_sym) == InputToken:
      sym = in_sym.char
    self.table[id0] = NFA_state(sym, set())
    id1 = len(self.table)
    self.table[id1] = NFA_state(None, set())
    self.set_table(id0, id1)
    return NFA_ret(id0, id1)

  def set_table(self, id, item):
    add_items = item
    match item:
      case set():
        pass
      case list() | tuple():
        add_items = set(item)
      case int():
        add_items = set([item])
    self.table[id].goto |= add_items

  def eps_closure(self, states):
    worklist = deque(states)
    result = set(states)
    while len(worklist) > 0:
      state = worklist.popleft()
      consume = self.table[state].sym
      goto_list = self.table[state].goto
      if consume is None:
        result |= goto_list
        worklist.extend(goto_list)
    return result

  def reg(self, input):
    states = self.eps_closure(set([0]))
    return_value = -1
    count = 0
    result = [0]
    for i, input_sym in enumerate(input):
      consume_flag = False
      next_states = set()
      worklist = deque(states)
      while len(worklist) > 0:
        state = worklist.popleft()
        consume = self.table[state].sym
        goto_list = self.table[state].goto
        match consume:
          case "<class-digits>":
            if input_sym in self.class_digits:
              next_states |= goto_list
              consume_flag = True
          case "<class-lower-alphabet>":
            if input_sym in self.class_lower_alphabet:
              next_states |= goto_list
              consume_flag = True
          case "<class-upper-alphabet>":
            if input_sym in self.class_upper_alphabet:
              next_states |= goto_list
              consume_flag = True
          case "<class-alphabet>":
            if input_sym in self.class_lower_alphabet or input_sym in self.class_upper_alphabet:
              next_states |= goto_list
              consume_flag = True
          case "<class-meta-alphabet>":
            if input_sym in self.class_lower_alphabet or input_sym in self.class_upper_alphabet or input_sym in self.class_digits or input_sym == "_":
              next_states |= goto_list
              consume_flag = True
          case "<comma>":
            if input_sym != " " and input_sym != "\n":
              next_states |= goto_list
              consume_flag = True
          case "<dot>":
            next_states |= goto_list
            consume_flag = True
          case None:
            continue
          case _:
            if input_sym == consume:
              next_states |= goto_list
              consume_flag = True
      if consume_flag:
        count += 1
      next_states = self.eps_closure(next_states)
      if self.end_id in next_states:
        result.append(count)
      states = next_states
    if max(result) >= len(input) and self.end_id in states:
      return_value = 0
    return Regex_ret(input[:max(result)], max(result), return_value)

def bnf_tokenizer(bnf_path:str):
  nfa = Bnf_nfa(bnf_json_path)
  result = []
  with open(cwd + bnf_path, mode="r", encoding="utf-8") as f:
    input_stream = f.read()
    input_deque = deque(input_stream)
    while len(input_deque) > 0:
      input_st = "".join(input_deque)
      ret = nfa.reg(input_st)
      result.append("".join(ret.accepts))
      for sym in ret.accepts:
        if sym == input_deque[0]:
          input_deque.popleft()
    result = [token for token in result if token != " " and token != "\n"]
    return result