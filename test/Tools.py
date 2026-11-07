from .Node import *
from src.components.common.Nodes import SyntaxTreeNode
from src.components.common.Data import InputToken

def AST_gen(Node):
  result = []
  if not isinstance(Node, SyntaxTreeNode):
    if isinstance(Node, InputToken):
      return Node.char
    return Node
  for next_node in Node.next_nodes:
    result.append(AST_gen(next_node))
  result = [node for node in result if node is not None]
  next_node_length = len(result)
  if next_node_length == 1:
    return AST_gen(result[0])
  elif next_node_length == 3:
    if result[0] == "(" and result[2] == ")":
      return result[1]
    else:
      return Binary_expression_node(result[0], result[2], result[1])
  elif next_node_length == 2:
    return Unary_expression_node(result[1], result[0])
  elif next_node_length == 0:
    return None
  else:
    return AST_node(result)

def AST_to_String(Node):
  if isinstance(Node, Binary_expression_node):
    left = AST_to_String(Node.left)
    right = AST_to_String(Node.right)
    return f"({left}{Node.operator}{right})"
  elif isinstance(Node, Unary_expression_node):
    value = AST_to_String(Node.value)
    return f"({Node.operator}{value})"
  elif isinstance(Node, str):
    return Node