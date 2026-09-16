import lalr1
import os

cwd = os.getcwd()
rule_name = "bnf"
bnf_file_path = "/src/"

result = lalr1.LALR1(cwd + bnf_file_path + rule_name + ".txt", "**i=*i")
result.show()