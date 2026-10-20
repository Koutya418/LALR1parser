from components.common.Syntax import Syntax
from components.common.States import States
from components.common.Data import LR0Item, State, EOF, Token
from collections import deque

class LALR1:
  def __init__(self, syntax:Syntax, states:States):
    self.syntax = syntax
    self.states = states
    self.table:dict[int, dict[str, dict[str, str]]] = {}
    self.lalr1_table_gen()

  def lalr1_table_gen(self):
    end_item = LR0Item(0, len(self.syntax.get_rule(0).re))
    for i in range(len(self.states.states)):
      state:State = self.states.states[i]
      next_state_cores, _, _ = state.lr1_closure(self.syntax)
      self.table[i] = {}
      for item in state.items:
        next_symbol = item.next_symbol(self.syntax)
        if item == end_item:
          self.table[i][EOF] = {"action":"accept", "value":"accept"}
          continue
        if next_symbol is None:
          for symbol in state.la[item]:
            self.table[i][symbol] = {"action":"reduce", "value":item.rule_id}
          continue
        action = "shift"
        value = None
        if next_symbol in next_state_cores:
          value = self.states.get_id(frozenset(next_state_cores[next_symbol]))
        if value is None:
          print("テーブル生成時に問題が発生しました")
        if self.syntax.is_term(next_symbol):
          self.table[i][next_symbol] = {"action":action, "value": value}
        else:
          action = "goto"
          self.table[i][next_symbol] = {"action":action, "value": value}

  def parse(self, input:list):
    input_deque = deque(input)
    stack = [0]
    result = []
    while len(input_deque) > 0:
      action_data = self.table[stack[-1]][input_deque[0]]
      action = action_data.get("action")
      value = action_data.get("value")
      match action:
        case "shift":
          input_deque.popleft()
          stack.append(value)
        case "reduce":
          result.append(value)
          for _ in range(len(self.syntax.get_rule(value).re)):
            stack.pop()
          le = self.syntax.get_rule(value).le
          goto_data = self.table[stack[-1]][le]
          stack.append(goto_data["value"])
        case "accept":
          return result

  def tree_gen(self, result:list[int], input:list, result_deque:deque = None, input_deque:deque = None):
    if result_deque is None:
      result_deque:deque = deque(result)
    if input_deque is None:
      input_deque:deque = deque(input)
    reduce_rule = self.syntax.get_rule(result_deque.pop())
    reduce_symbol_type = self.syntax.get_symbol_type(reduce_rule.le)
    reduce_re = reversed(reduce_rule.re)
    root_token = Token(reduce_symbol_type, reduce_rule.le, [])
    for symbol in reduce_re:
      if symbol == input_deque[-1]:
        add_item = None
        add_item_symbol_type = self.syntax.get_symbol_type(symbol)
        match add_item_symbol_type:
          case "nonterm":
            add_item = Token(add_item_symbol_type, symbol, [input_deque[-1]])
          case "term":
            add_item = symbol
        root_token.next_token.append(add_item)
        input_deque.pop()
      else:
        root_token.next_token.append(self.tree_gen(result, input, result_deque, input_deque))
    root_token.next_token.reverse()
    return root_token