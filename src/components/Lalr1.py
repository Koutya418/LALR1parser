from .common.Syntax import _Syntax, Syntax
from .common.States import States
from .common.Data import LR0Item, State, EOF, InputToken
from .common.Nodes import SyntaxTreeNode
from collections import deque
from pathlib import Path
from .common.Error import *
import copy
import json

class LALR1:
  def __init__(self, syntax:_Syntax|Syntax, states:States, table_json_path:Path = None, debug:bool = False):
    self.syntax = syntax
    self.states = states
    self.table:dict[int, dict[str, dict[str, str]]] = {}
    if table_json_path is None:
      self.lalr1_table_gen(debug)
    else:
      self.json_table_load(table_json_path)

  def lalr1_table_gen(self, debug):
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
          add_table = {"action":"reduce", "value":item.rule_id}
          for symbol in state.la[item]:
            if symbol in self.table[i]:
              self.shift_reduce_conflict_solver(i, symbol, add_table, self.table[i][symbol])
              continue
            self.table[i][symbol] = add_table
          continue
        value = None
        if next_symbol in next_state_cores:
          value = self.states.get_id(frozenset(next_state_cores[next_symbol]))
        if value is None:
          print("テーブル生成時に問題が発生しました")
        action = "shift"
        if self.syntax.is_nonterm(next_symbol):
          action = "goto"
        add_table = {"action":action, "value": value}
        if next_symbol in self.table[i]:
          self.shift_reduce_conflict_solver(i, next_symbol, self.table[i][next_symbol], add_table)
          continue
        self.table[i][next_symbol] = add_table

  def json_table_output(self):
    result = {}
    for i, state in self.table.items():
      result[i] = {}
      for symbol, action in state.items():
        add_symbol = symbol
        if add_symbol is EOF:
          add_symbol = "__class__:EOF"
        result[i][add_symbol] = action
    return result

  def json_table_load(self, path:Path):
    with path.open(mode="r", encoding="utf-8") as f:
      json_data:dict = json.load(f)
      table_data:dict[int, dict[str, dict[str, str]]] = json_data.get("lalr1")
      for i, state in table_data.items():
        self.table[int(i)] = {}
        for symbol, action in state.items():
          if symbol == "__class__:EOF":
            self.table[int(i)][EOF] = action
          else:
            self.table[int(i)][symbol] = action
          

  def shift_reduce_conflict_solver(self, state, symbol, reduce_table:dict, shift_table:dict):
    if not isinstance(self.syntax, Syntax):
      return
    if reduce_table == shift_table:
      return
    #print(f"テーブル生成時に衝突が発生しました{reduce_table}, {shift_table}")
    if reduce_table.get("action") != "reduce":
      return
    if shift_table.get("action") != "shift":
      return
    reduce_precedence:dict = self.syntax.get_rule(int(reduce_table.get("value"))).prec
    shift_precedence:dict = self.syntax.term_precedences.get(symbol)
    if reduce_precedence is not None:
      reduce_precedence = reduce_precedence.get("precedence")
    if shift_precedence is not None:
      shift_precedence = shift_precedence.get("precedence")
    add_table = shift_table
    if shift_precedence is None or reduce_precedence is None:
      pass
    elif shift_precedence > reduce_precedence:
      pass
    elif shift_precedence < reduce_precedence:
      add_table = reduce_table
    elif shift_precedence == reduce_precedence:
      associativity = self.syntax.term_precedences.get(symbol)
      if associativity is None:
        return
      associativity = associativity.get("associativity")
      match associativity:
        case "left":
          add_table = reduce_table
        case "right":
          pass
        case "nonassoc":
          raise ValueError
    self.table[state][symbol] = add_table


  def parse(self, input:list):
    input_deque = deque(input)
    stack = [0]
    node_stack = []
    result = []
    row_count = 1
    row_start = 0
    while len(input_deque) > 0:
      ignore_flag = True
      while ignore_flag:
        if isinstance(input_deque[0], InputToken):
          if input_deque[0].char == "\n":
            row_count += 1
            row_start = len(input) - len(input_deque) + 1
          if input_deque[0].token_type == "skip":
            input_deque.popleft()
          else:
            ignore_flag = False
        else:
          ignore_flag = False
      input_token = input_deque[0]
      if isinstance(input_token, InputToken):
        input_token = input_token.token_type
      action_data = self.table.get(stack[-1]).get(input_token)
      if action_data is None:
        raise ParserParseError(
          "構文解析でエラーが発生しました",
          copy.deepcopy(input),
          row_count,
          row_start
        )
      action = action_data.get("action")
      value = action_data.get("value")
      match action:
        case "shift":
          node = input_deque.popleft()
          node_stack.append(node)
          stack.append(value)
        case "reduce":
          result.append(value)
          add_nodes = []
          for _ in range(len(self.syntax.get_rule(value).re)):
            stack.pop()
            node = node_stack.pop()
            add_nodes.append(node)
          add_nodes.reverse()
          le = self.syntax.get_rule(value).le
          node_stack.append(SyntaxTreeNode("nonterm", le, add_nodes))
          goto_data = self.table[stack[-1]][le]
          stack.append(goto_data["value"])
        case "accept":
          if len(node_stack) != 1:
            raise ValueError
          return node_stack[0]

  def tree_gen(self, result:list[int], input:list, result_deque:deque = None, input_deque:deque = None):
    if result_deque is None:
      result_deque:deque = deque(result)
    if input_deque is None:
      input_deque:deque = deque(input)
    reduce_rule = self.syntax.get_rule(result_deque.pop())
    reduce_symbol_type = self.syntax.get_symbol_type(reduce_rule.le)
    reduce_re = reversed(reduce_rule.re)
    root_node = SyntaxTreeNode(reduce_symbol_type, reduce_rule.le, [])
    for symbol in reduce_re:
      input_token = input_deque[-1]
      if type(input_token) == InputToken:
        input_token = input_token.token_type
      if symbol == input_token:
        add_item = None
        add_item_symbol_type = self.syntax.get_symbol_type(symbol)
        match add_item_symbol_type:
          case "nonterm":
            add_item = SyntaxTreeNode(add_item_symbol_type, symbol, [input_deque[-1]])
          case "term":
            add_item = symbol
            if type(input_deque[-1]) == InputToken:
              add_item = input_deque[-1]
        root_node.next_nodes.append(add_item)
        input_deque.pop()
      else:
        root_node.next_nodes.append(self.tree_gen(result, input, result_deque, input_deque))
    root_node.next_nodes.reverse()
    return root_node