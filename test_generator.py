from pathlib import Path

base_dir = Path(__file__).resolve().parent / "test_cases"


TOKENIZER = r'''int = "/d/d*"
id = "(/z|_)/w*"
operator = "+|-|\*|\/|^|\(|\)"
skip = "\n| "
'''


tests: dict[str, list[dict[str, str|list[dict]]]] = {
   "valid_case":[
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
                {"test": "1+2", "answer": "(1(+2))"},
                {"test": "1+2+3", "answer": "(1(+2(+3)))"},
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
        },

        #10 .複数行の入力のテスト
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
                # 演算子の後で改行
                {"test": "1+\n2", "answer": "(1+2)"},
                {"test": "1*\n2", "answer": "(1*2)"},

                # オペランドの後で改行
                {"test": "1\n+2", "answer": "(1+2)"},
                {"test": "1\n*2", "answer": "(1*2)"},

                # 演算子を複数行に分割
                {"test": "1+\n2*\n3", "answer": "(1+(2*3))"},
                {"test": "1*\n2+\n3", "answer": "((1*2)+3)"},

                # 複数行にまたがる括弧
                {"test": "(\n1+2\n)", "answer": "(1+2)"},
                {"test": "1+(\n2*3\n)", "answer": "(1+(2*3))"},

                # 空行を含む
                {"test": "1+\n\n2", "answer": "(1+2)"},
                {"test": "1\n\n+\n\n2", "answer": "(1+2)"},
            ]
        }
    ],
    "parse_error":[
        #11 .入力に誤りがあるケースのテスト
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
                # 先頭に演算子
                {"test": "+2", "answer": "\n構文解析でエラーが発生しました\n[1]+2 <-"},
                {"test": "*2", "answer": "\n構文解析でエラーが発生しました\n[1]*2 <-"},

                # 演算子の後にオペランドがない
                {"test": "1+", "answer": "\n構文解析でエラーが発生しました\n[1]1+ <-"},
                {"test": "1*", "answer": "\n構文解析でエラーが発生しました\n[1]1* <-"},

                # 演算子が連続
                {"test": "1++2", "answer": "\n構文解析でエラーが発生しました\n[1]1++2 <-"},
                {"test": "1**2", "answer": "\n構文解析でエラーが発生しました\n[1]1**2 <-"},

                # オペランドが連続
                {"test": "1 2", "answer": "\n構文解析でエラーが発生しました\n[1]1 2 <-"},
                {"test": "1(2)", "answer": "\n構文解析でエラーが発生しました\n[1]1(2) <-"},

                # 括弧の不整合
                {"test": "(1+2", "answer": "\n構文解析でエラーが発生しました\n[1](1+2 <-"},
                {"test": "1+2)", "answer": "\n構文解析でエラーが発生しました\n[1]1+2) <-"},
                {"test": "((1+2)", "answer": "\n構文解析でエラーが発生しました\n[1]((1+2) <-"},

                # 空の括弧
                {"test": "()", "answer": "\n構文解析でエラーが発生しました\n[1]() <-"},
                {"test": "(+1)", "answer": "\n構文解析でエラーが発生しました\n[1](+1) <-"},

                # 演算子の位置がおかしい
                {"test": "1+*2", "answer": "\n構文解析でエラーが発生しました\n[1]1+*2 <-"},
                {"test": "1/*2", "answer": "\n構文解析でエラーが発生しました\n[1]1/*2 <-"},
            ]
        },

        #12 .複数行の入力でのエラー表示のテスト
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
                # 2行目でオペランドが連続
                {
                    "test": "1+2\n3",
                    "answer": "\n構文解析でエラーが発生しました\n[2]3 <-"
                },
                {
                    "test": "1+2\n3+4",
                    "answer": "\n構文解析でエラーが発生しました\n[2]3+4 <-"
                },

                # 2行目で不正な演算子
                {
                    "test": "1+\n*2",
                    "answer": "\n構文解析でエラーが発生しました\n[2]*2 <-"
                },
                {
                    "test": "1+\n/2",
                    "answer": "\n構文解析でエラーが発生しました\n[2]/2 <-"
                },

                # 2行目で括弧が不正
                {
                    "test": "(1+2\n3)",
                    "answer": "\n構文解析でエラーが発生しました\n[2]3) <-"
                },
                {
                    "test": "1+2\n)",
                    "answer": "\n構文解析でエラーが発生しました\n[2]) <-"
                },
                {
                    "test": "1+\n)",
                    "answer": "\n構文解析でエラーが発生しました\n[2]) <-"
                },

                # 3行目でエラー
                {
                    "test": "1+\n2\n3",
                    "answer": "\n構文解析でエラーが発生しました\n[3]3 <-"
                },
                {
                    "test": "1+\n2*\n+3",
                    "answer": "\n構文解析でエラーが発生しました\n[3]+3 <-"
                },

                # 空行を挟んだエラー
                {
                    "test": "1+2\n\n3",
                    "answer": "\n構文解析でエラーが発生しました\n[3]3 <-"
                },

                # 括弧を閉じずにEOF
                {
                    "test": "(1+2\n",
                    "answer": "\n構文解析でエラーが発生しました\n[2] <-"
                },
            ]
        }
    ],
    "tokenizer_error":[
        {
            "tokenizer": 'digit = "/d"\n'
                        'operator = "+|-|\\*|\\/|^|\\(|\\)"\n'
                        'skip = "\\n| "',
            "rule": r'''
S' ::= int;
''',
            "cases": [
                {
                    "test": "1a",
                    "answer": "\n字句解析でエラーが発生しました\n[1]1 -> a"
                },
                {
                    "test": "11+\n1a",
                    "answer": "\n字句解析でエラーが発生しました\n[2]1 -> a"
                },
                {
                    "test": "11+\n\n1a",
                    "answer": "\n字句解析でエラーが発生しました\n[3]1 -> a"
                },
                {
                    "test": "1\n2\n3a",
                    "answer": "\n字句解析でエラーが発生しました\n[3]3 -> a"
                },
                {
                    "test": "1\n\n\n@",
                    "answer": "\n字句解析でエラーが発生しました\n[4] -> @"
                },
                {
                    "test": "1+2\n3*4\n5&6",
                    "answer": "\n字句解析でエラーが発生しました\n[3]5 -> &6"
                },
                {
                    "test": "1\n2\n\n\nabc",
                    "answer": "\n字句解析でエラーが発生しました\n[5] -> abc"
                },
                {
                    "test": "1\n2\n3\n4\n5@",
                    "answer": "\n字句解析でエラーが発生しました\n[5]5 -> @"
                }
            ]
        }
    ]
}

for key, test_case in tests.items():
  test_case_dir = base_dir / key
  test_case_dir.mkdir()
  for i1, test in enumerate(test_case):
    test_dir = test_case_dir / f"test_{i1}"
    test_dir.mkdir()
    tokenizer = test.get("tokenizer")
    tokenizer_file = test_dir / "tokenizer.txt"
    tokenizer_file.write_text(tokenizer, encoding='utf-8')
    rule = test.get("rule")
    rule_file = test_dir / "rule.txt"
    rule_file.write_text(rule, encoding='utf-8')
    cases = test.get("cases")
    case_dir = test_dir / "case"
    case_dir.mkdir()
    for i2, case in enumerate(cases):
        case_dir = test_dir / "case" / f"case_{i2}"
        case_dir.mkdir()
        test_text = case.get("test")
        test_file = case_dir / "test.txt"
        test_file.write_text(test_text, encoding='utf-8')
        answer = case.get("answer")
        answer_file = case_dir / "answer.txt"
        answer_file.write_text(answer, encoding='utf-8')