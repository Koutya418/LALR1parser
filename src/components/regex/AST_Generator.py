from ..common.Data import InputToken
from ..common.Nodes import SyntaxTreeNode

def ast_gen(node:SyntaxTreeNode):
  tok_sym = node.node_sym
  if len(node.next_nodes) > 1:
    ret_tok_list = []
    for tok in node.next_nodes:
      ret = tok
      if type(tok) == SyntaxTreeNode:
        ret = ast_gen(tok)
        if type(ret) != InputToken:
          match ret:
            case "*": #量化子処理用
              if node.node_sym == "<repetition>":
                tok_sym = "<star>"
                continue
      if tok == "|" or tok == "(" or tok == ")":
        continue
      ret_tok_list.append(ret)
    return SyntaxTreeNode(node.node_type, tok_sym, ret_tok_list)
  elif len(node.next_nodes) == 1:
    ret = node.next_nodes[0]
    if type(ret) == InputToken:
      ret = ret
    elif type(ret) == SyntaxTreeNode:
      ret = ast_gen(ret)
    elif type(ret) == str:
      ret = ret
      match ret:
        case ".":
          ret = "<dot>"
        case ",":
          ret = "<comma>"
    return ret
  else:
    return node.node_sym