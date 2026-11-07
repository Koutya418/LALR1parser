from pathlib import Path

base_dir = Path(__file__).resolve().parent / "test"


TOKENIZER = r'''int = "/d/d*"
id = "(/z|_)/w*"
operator = "+|-|\*|\/|^|\(|\)"'''


tests: list[dict[str, str|list[dict]]] = [

    # 1. 基本的な四則演算の優先順位
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= <expression> "+" <expression>
               | <expression> "-" <expression>
               | <expression> "*" <expression>
               | <expression> "/" <expression>
               | "(" <expression> ")"
               | int;

%left "+" "-"
%left "*" "/"
''',
        "cases": [
            {"test": "1+2", "answer": "(1+2)"},
            {"test": "1+2*3", "answer": "(1+(2*3))"},
            {"test": "1*2+3", "answer": "((1*2)+3)"},
            {"test": "1+2*3-4", "answer": "((1+(2*3))-4)"},
            {"test": "1*2/3", "answer": "((1*2)/3)"},
            {"test": "1+2+3", "answer": "((1+2)+3)"},
            {"test": "1*2*3", "answer": "((1*2)*3)"},
            {"test": "(1+2)*3", "answer": "((1+2)*3)"},
            {"test": "1*(2+3)", "answer": "(1*(2+3))"},
        ]
    },

    # 2. 右結合
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= <expression> "^" <expression>
               | "(" <expression> ")"
               | int;

%right "^"
''',
        "cases": [
            {"test": "1^2", "answer": "(1^2)"},
            {"test": "1^2^3", "answer": "(1^(2^3))"},
            {"test": "1^2^3^4", "answer": "(1^(2^(3^4)))"},
            {"test": "(1^2)^3", "answer": "((1^2)^3)"},
        ]
    },

    # 3. 単項マイナスと %prec
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= <expression> "+" <expression>
               | <expression> "-" <expression>
               | <expression> "*" <expression>
               | "-" <expression> %prec UMINUS
               | "(" <expression> ")"
               | int;

%left "+" "-"
%left "*"
%right UMINUS
''',
        "cases": [
            {"test": "-1", "answer": "(-1)"},
            {"test": "-1+2", "answer": "((-1)+2)"},
            {"test": "-1*2", "answer": "((-1)*2)"},
            {"test": "1+-2", "answer": "(1+(-2))"},
            {"test": "-1*2+3", "answer": "(((-1)*2)+3)"},
            {"test": "--1", "answer": "(-(-1))"},
            {"test": "-1+-2", "answer": "((-1)+(-2))"},
        ]
    },

    # 4. 優先順位の宣言がない場合
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= <expression> "+" <expression>
               | <expression> "*" <expression>
               | int;
''',
        "cases": [
            {"test": "1+2+3", "answer": "(1+(2+3))"},
            {"test": "1*2*3", "answer": "(1*(2*3))"},
            {"test": "1+2*3", "answer": "(1+(2*3))"},
            {"test": "1*2+3", "answer": "(1*(2+3))"},
        ]
    },

    # 5. Reduce側のみ優先順位が存在する場合
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= <expression> "+" <expression>
               | <expression> "*" <expression>
               | int;

%left "+"
''',
        "cases": [
            {"test": "1+2*3", "answer": "(1+(2*3))"},
            {"test": "1+2+3", "answer": "((1+2)+3)"},
        ]
    },

    # 6. Shift側のみ優先順位が存在する場合
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= <expression> "+" <expression>
               | <expression> "*" <expression>
               | int;

%left "*"
''',
        "cases": [
            {"test": "1*2+3", "answer": "(1*(2+3))"},
            {"test": "1*2*3", "answer": "((1*2)*3)"},
        ]
    },

    # 7. 非終端記号そのものがεを導出する
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= int
               | "<eps>";
''',
        "cases": [
            {"test": "", "answer": "<eps>"},
            {"test": "1", "answer": "1"},
            {"test": "123", "answer": "123"},
        ]
    },

    # 8. 再帰的な生成規則の終端条件としてεを使用する
    {
        "tokenizer": TOKENIZER,
        "rule": r'''
S' ::= <expression>;

<expression> ::= int <expression_tail>;

<expression_tail> ::= "+" int <expression_tail>
                    | "<eps>";
''',
        "cases": [
            {"test": "1", "answer": "1"},
            {"test": "1+2", "answer": "(1+2)"},
            {"test": "1+2+3", "answer": "(1(+2(+3))))"},
            {"test": "1+2+3+4", "answer": "(1(+2(+3(+4))))"},
        ]
    },

    # 9 .生成規則の途中にεを導出する非終端記号が存在する
    {
        "tokenizer": 'digit = "/d"\n'
                    'operator = "+|-|\\*|\\/|^|\\(|\\)"',
        "rule": r'''
S' ::= <expression>;

<expression> ::= digit <optional> digit;

<optional> ::= "+"
             | "<eps>";
''',
        "cases": [
            {"test": "12", "answer": "(12)"},
            {"test": "1+2", "answer": "(1+2)"},
        ]
    }
]


for i1, test in enumerate(tests):
  test_dir = base_dir / f"test_{i1}"
  test_dir.mkdir()
  tokenizer = test.get("tokenizer")
  tokenizer_file = test_dir / "tokenizer.txt"
  tokenizer_file.touch()
  tokenizer_file.write_text(tokenizer, encoding='utf-8')
  rule = test.get("rule")
  rule_file = test_dir / "rule.txt"
  rule_file.touch()
  rule_file.write_text(rule, encoding='utf-8')
  cases = test.get("cases")
  case_dir = test_dir / "case"
  case_dir.mkdir()
  for i2, case in enumerate(cases):
    case_dir = test_dir / "case" / f"case_{i2}"
    case_dir.mkdir()
    test_text = case.get("test")
    test_file = case_dir / "test.txt"
    test_file.touch()
    test_file.write_text(test_text, encoding='utf-8')
    answer = case.get("answer")
    answer_file = case_dir / "answer.txt"
    answer_file.touch()
    answer_file.write_text(answer, encoding='utf-8')