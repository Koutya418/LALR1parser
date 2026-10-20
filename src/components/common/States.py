from __future__ import annotations
from components.common.Data import State, LR0Item, Propagation_symbol, EOF
from collections import deque

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from components.common.Syntax import Syntax

class States:
  def __init__(self):
    self.states:dict[int, State] = {}
    self.core_to_state:dict[frozenset[LR0Item], int] = {}

  def add_state(self, core:frozenset[LR0Item]):
    state_id = None
    if core not in self.core_to_state:
      state_id = len(self.states)
      self.states[state_id] = State(core)
      self.core_to_state[core] = state_id
    return state_id

  def get_id(self, core:frozenset[LR0Item]):
    return self.core_to_state.get(frozenset(core))

  def lr0_closure(self, syntax:Syntax, state_id:int):
    return self.states[state_id].lr0_closure(syntax)

  def LR0_table_gen(self, syntax:Syntax):
    state_id = self.add_state(frozenset([LR0Item(0, 0)]))
    worklist:deque = deque([state_id])
    while len(worklist) > 0:
      state = worklist.popleft()
      next_core_states = self.lr0_closure(syntax, state)
      for next_core in next_core_states.values():
        state_id = self.add_state(frozenset(next_core))
        if state_id is not None:
          worklist.append(state_id)

  def lalr1_gen(self, syntax:Syntax):
    propagation_link:dict[int, dict[LR0Item, dict[int, set[LR0Item]]]] = {}
    spontaneous_la: dict[int, dict[LR0Item, set]] = {}
    start_item = LR0Item(0, 0)
    for i in range(len(self.states)):
      propagation_link[i] = {}
      self.states[i].la_init()
      for core_item in self.states[i].core:
        self.states[i].la_set(core_item, set([Propagation_symbol]))
      next_core_states, links, spontaneous = self.states[i].lr1_closure(syntax)
      for next_core in next_core_states.values():
        state_id = self.get_id(next_core)
        for core_item in next_core:
          propagation_source_items = links[LR0Item(core_item.rule_id, core_item.dot - 1)]
          for propagation_source_item in propagation_source_items:
            if propagation_source_item not in propagation_link[i]:
              propagation_link[i][propagation_source_item] = {}
            if state_id not in propagation_link[i][propagation_source_item]:
              propagation_link[i][propagation_source_item][state_id] = set()
            propagation_link[i][propagation_source_item][state_id].add(core_item)

          for core_item, la in spontaneous.items():
            if core_item in next_core:
              if state_id not in spontaneous_la:
                spontaneous_la[state_id] = {}
              if core_item not in spontaneous_la[state_id]:
                spontaneous_la[state_id][core_item] = set()
              spontaneous_la[state_id][core_item] |= la

    for i in range(len(self.states)):
      self.states[i].la_init()
      state = self.states[i]
      for core_item in state.core:
        state.la_set(core_item, set())
        if i in spontaneous_la:
          if core_item in spontaneous_la[i]:
            state.la_add(core_item, spontaneous_la[i][core_item])
        if core_item == start_item:
          state.la_add(core_item, set([EOF]))

    sources = []
    for source_state_id, source_dict in propagation_link.items():
      for source_item in source_dict.keys():
        sources.append(tuple([source_state_id, source_item]))
    worklist:deque = deque(sources)
    while len(worklist) > 0:
      source = worklist.popleft()
      source_la = self.states[source[0]].la[source[1]]
      for state, targets in propagation_link[source[0]][source[1]].items():
        for target in targets:
          add_flag = False
          la = self.states[state].la.get(target)
          if la is None:
            add_flag = True
          elif la & source_la != source_la:
            add_flag = True
          self.states[state].la_add(target, source_la)
          if add_flag:
            if state in propagation_link:
              if target in propagation_link[state]:
                worklist.append(tuple([state, target]))
    for i in range(len(self.states)):
      state = self.states[i]
      state.lr1_closure(syntax)