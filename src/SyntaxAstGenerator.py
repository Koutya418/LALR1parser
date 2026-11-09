from .components.common.Data import InputToken
from .components.common.Nodes import *

def syntax_ast_generator(node:SyntaxTreeNode) -> AstNode:
  node_symbol = node.node_sym
  result_node_list = []
  for next_node in node.next_nodes:
    result = next_node
    if isinstance(next_node, SyntaxTreeNode):
      result = syntax_ast_generator(result)
    result_node_list.append(result)
  match node_symbol:
    case "<syntax>":
      result = syntax_gen(node)
      return SyntaxNode(result)
    case "<rule_definition>":
      if len(node.next_nodes) == 4:
        if not isinstance(node.next_nodes[2], SyntaxTreeNode):
          return
        if node.next_nodes[2].node_sym != "<rule_list>":
          return
        return RuleDefinitionNode(result_node_list[0], rule_list_gen(node.next_nodes[2]))
    case "<rule_items>":
      result = rule_items_gen(node)
      return RuleItemsNode(result)
    case "<rule>":
      result = rule_items_gen(node.next_nodes[0])
      prec = None
      if len(node.next_nodes) == 3:
        prec = result_node_list[2]
      return RuleNode(result, prec)
    case "<prec>":
      if len(node.next_nodes) == 2:
        if not isinstance(node.next_nodes[1], SyntaxTreeNode):
          return
        if node.next_nodes[1].node_sym != "<prec_list>":
          return
        return PrecDefinitionNode(result_node_list[0], prec_list_gen(node.next_nodes[1]))
    case "<nonterm>":
      if len(node.next_nodes) == 1:
        ret = node.next_nodes[0]
        if isinstance(ret, InputToken):
          ret = ret.char
        return ret
    case "<token>":
      if len(node.next_nodes) == 1:
        ret = node.next_nodes[0]
        if isinstance(ret, InputToken):
          ret = ret.char
        return ret
    case "<term>":
      if len(node.next_nodes) == 1:
        ret = node.next_nodes[0]
        if isinstance(ret, InputToken):
          ret = ret.char
        ret = ret[1:-1]
        return ret
    case _:
      if len(node.next_nodes) > 1:
        return SyntaxTreeNode(node.node_type, node_symbol, result_node_list)
      elif len(node.next_nodes) == 1:
        ret = node.next_nodes[0]
        if type(ret) == InputToken:
          ret = ret.char
        elif type(ret) == SyntaxTreeNode:
          ret = syntax_ast_generator(ret)
        elif type(ret) == str:
          ret = ret
        return ret
      else:
        return node.node_sym

def syntax_gen(node):
  result = []
  if isinstance(node, SyntaxTreeNode):
    match node.node_sym:
      case "<syntax>":
        if len(node.next_nodes) == 2:
          result += syntax_gen(node.next_nodes[0])
          result += syntax_gen(node.next_nodes[1])
          return result
        elif len(node.next_nodes) == 1:
          return [syntax_ast_generator(node.next_nodes[0])]
      case _:
        return [syntax_ast_generator(node)]

def rule_list_gen(node):
  result = []
  if isinstance(node, SyntaxTreeNode):
    match node.node_sym:
      case "<rule_list>":
        if len(node.next_nodes) == 3:
          result += rule_list_gen(node.next_nodes[0])
          result += rule_list_gen(node.next_nodes[2])
          return result
        elif len(node.next_nodes) == 1:
          return [syntax_ast_generator(node.next_nodes[0])]
      case _:
        return [syntax_ast_generator(node)]

def rule_items_gen(node):
  result = []
  if isinstance(node, SyntaxTreeNode):
    match node.node_sym:
      case "<rule_items>":
        if len(node.next_nodes) == 2:
          result += rule_items_gen(node.next_nodes[0])
          result += rule_items_gen(node.next_nodes[1])
          return result
        elif len(node.next_nodes) == 1:
          return [syntax_ast_generator(node.next_nodes[0])]
      case _:
        return [syntax_ast_generator(node)]

def prec_list_gen(node):
  result = []
  if isinstance(node, SyntaxTreeNode):
    match node.node_sym:
      case "<prec_list>":
        if len(node.next_nodes) == 2:
          result += prec_list_gen(node.next_nodes[0])
          result += prec_list_gen(node.next_nodes[1])
          return result
        elif len(node.next_nodes) == 1:
          return [syntax_ast_generator(node.next_nodes[0])]
      case _:
        return [syntax_ast_generator(node)]