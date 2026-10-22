from components.common.Data import Token, InputToken

def ast_gen(token:Token):
  tok_sym = token.token_sym
  if len(token.next_token) > 1:
    ret_tok_list = []
    for tok in token.next_token:
      ret = tok
      if type(tok) == Token:
        ret = ast_gen(tok)
        if type(ret) != InputToken:
          match ret:
            case "*": #量化子処理用
              if token.token_sym == "<repetition>":
                tok_sym = "<star>"
                continue
      if tok == "|" or tok == "(" or tok == ")":
        continue
      ret_tok_list.append(ret)
    return Token(token.token_type, tok_sym, ret_tok_list)
  elif len(token.next_token) == 1:
    ret = token.next_token[0]
    if type(ret) == InputToken:
      ret = ret
    elif type(ret) == Token:
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
    return token.token_sym