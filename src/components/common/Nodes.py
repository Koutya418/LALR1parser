from dataclasses import dataclass
from .Data import InputToken

@dataclass
class SyntaxTreeNode:
  node_type: str
  node_sym: str
  next_nodes: list

  def show(self, nest = 0):
    indent = ""
    for _ in range(nest):
        indent += " "
    print(f"{indent}{self.node_sym}")
    for node in self.next_nodes:
      match node:
        case str():
          print(indent + " " + node)
        case InputToken():
          node.show(indent + " ")
        case SyntaxTreeNode():
          node.show(nest + 1)
        case AstNode():
          node.show(indent, nest)

@dataclass
class AstNode:
  def show(self, indent:str = "", nest:int = 0):
    pass

  def nodes_show(self, indent:str, nest:int, node_type:str, print_list:list):
    print(f"{indent} {node_type}")
    for node in print_list:
      match node:
        case InputToken():
          node.show(indent + "  ")
        case SyntaxTreeNode():
          node.show(nest + 2)
        case str():
          print(f"{indent}  {node}")
        case AstNode():
          node.show(indent + " ", nest + 1)
        case None:
          print(f"{indent}  {node}")

@dataclass
class SyntaxNode(AstNode):
  rules:list

  def show(self, indent:str = "", nest:int = 0):
    print_list = self.rules
    self.nodes_show(indent, nest, "<syntax>", print_list)

@dataclass
class RuleItemsNode(AstNode):
  items:list

  def show(self, indent:str = "", nest:int = 0):
    print_list = self.items
    self.nodes_show(indent, nest, "<rule_items>", print_list)

@dataclass
class RuleDefinitionNode(AstNode):
  lhs:str
  rules:list

  def show(self, indent:str = "", nest:int = 0):
    print_list = [self.lhs] + self.rules
    self.nodes_show(indent, nest, "<rule_definition>", print_list)

@dataclass
class PrecDefinitionNode(AstNode):
  prec:str
  symbols:list

  def show(self, indent:str = "", nest:int = 0):
    print_list = [self.prec] + self.symbols
    self.nodes_show(indent, nest, "<prec_definition>", print_list)

@dataclass 
class RuleNode(AstNode):
  rule_items:list
  prec:str|None

  def show(self, indent:str = "", nest:int = 0):
    print_list = self.rule_items + [self.prec]
    self.nodes_show(indent, nest, "<rule>", print_list)