from dataclasses import dataclass

@dataclass
class Node:
  pass

@dataclass
class AST_node(Node):
  next_nodes:list

@dataclass
class Binary_expression_node(Node):
  left:str|int|AST_node
  right:str|int|AST_node
  operator:str

@dataclass
class Unary_expression_node(Node):
  value:str|int|AST_node
  operator:str