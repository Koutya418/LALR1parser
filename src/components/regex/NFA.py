from dataclasses import dataclass
from collections import deque
from components.common.Data import Token, InputToken

@dataclass
class NFA_state:
  sym: str|None
  goto: set[int]
  mode: str|None = None

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

class NFA:
  def __init__(self, ast: Token):
    self.table:dict[int, NFA_state] = {}
    end_id = self.nfa_table_gen(ast)
    self.end_id = end_id.end
    self.class_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    self.class_lower_alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    self.class_upper_alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

  def nfa_table_gen(self, ast: Token|InputToken|str):
    ret = None
    match ast:
      case str():
        ret = self.literal_gen(ast)
      case InputToken():
        ret = self.literal_gen(ast.char)
      case Token():
        match ast.token_sym:
          case "<concatenation>":
            ret = self.concatenation_gen(ast)
          case "<alternation>":
            ret = self.alternation_gen(ast)
          case "<star>":
            ret = self.star_gen(ast)
          case "<group>":
            ret = self.nfa_table_gen(ast.next_token[0])
    return ret

  def star_gen(self, ast: Token):
    id0 = len(self.table)
    self.table[id0] = NFA_state(None, set())
    tok0 = ast.next_token[0]
    match ast.next_token[0]:
      case str() | InputToken():
        ret0 = self.literal_gen(tok0)
      case Token():
        ret0 = self.nfa_table_gen(tok0)
    id1 = len(self.table)
    self.table[id1] = NFA_state(None, set())
    id2 = len(self.table)
    mode = None
    if len(ast.next_token) > 1:
      match ast.next_token[1]:
        case "!":
          mode = "lazy"
    self.table[id2] = NFA_state(None, set(), mode)
    self.set_table(id0, [ret0.start, id2])
    self.set_table(id1, [ret0.start, id2])
    self.set_table(ret0.end, [id1])
    return NFA_ret(id0, id2)

  def concatenation_gen(self, ast: Token) -> NFA_ret:
    tok0 = ast.next_token[0]
    tok1 = ast.next_token[1]
    match tok0:
      case str() | InputToken():
        ret0 = self.literal_gen(tok0)
      case Token():
        ret0 = self.nfa_table_gen(tok0)
    id0 = len(self.table)
    self.table[id0] = NFA_state(None, set())
    match tok1:
      case str() | InputToken():
        ret1 = self.literal_gen(tok1)
      case Token():
        ret1 = self.nfa_table_gen(tok1)
    self.set_table(ret0.end, id0)
    self.set_table(id0, ret1.start)
    id1 = len(self.table)
    self.table[id1] = NFA_state(None, set())
    self.set_table(ret1.end, id1)
    return NFA_ret(ret0.start, id1)

  def alternation_gen(self, ast: Token) -> NFA_ret:
    id0 = len(self.table)
    self.table[id0] = NFA_state(None, set())
    tok0 = ast.next_token[0]
    tok1 = ast.next_token[1]
    match tok0:
      case str() | InputToken():
        ret0 = self.literal_gen(tok0)
      case Token():
        ret0 = self.nfa_table_gen(tok0)
    match tok1:
      case str() | InputToken():
        ret1 = self.literal_gen(tok1)
      case Token():
        ret1 = self.nfa_table_gen(tok1)
    id1 = len(self.table)
    self.table[id1] = NFA_state(None, set())
    id2 = len(self.table)
    self.table[id2] = NFA_state(None, set())
    id3 = len(self.table)
    self.table[id3] = NFA_state(None, set())
    self.set_table(id0, [ret0.start, ret1.start])
    self.set_table(ret0.end, id1)
    self.set_table(ret1.end, id2)
    self.set_table(id1, id3)
    self.set_table(id2, id3)
    return NFA_ret(id0, id3)

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
    for _, input_sym in enumerate(input): #C
      consume_flag = False
      next_states = set()
      worklist = deque(states)
      while len(worklist) > 0: #B
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
            if input_sym in self.class_lower_alphabet or input_sym in self.class_upper_alphabet or input_sym == "_":
              next_states |= goto_list
              consume_flag = True
          case "<class-meta-digits-alphabet>":
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
        for state_id in next_states:
          if self.table[state_id].mode is None:
            continue
          return Regex_ret(input[:count], count, return_value)
      states = next_states
    if max(result) >= len(input) and self.end_id in states:
      return_value = 0
    return Regex_ret(input[:max(result)], max(result), return_value)