from dataclasses import dataclass
from .ast import SourceSpan
from .errors import LexError

@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    span: SourceSpan

KEYWORDS = {"begin", "end", "if", "then", "else", "while", "do", "skip"}

def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i, line, col = 0, 1, 1
    n = len(source)
    while i < n:
        ch = source[i]
        if ch in " \t\r":
            i += 1; col += 1; continue
        if ch == "\n":
            i += 1; line += 1; col = 1; continue
        start_line, start_col = line, col
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            value = source[i:j]
            kind = value.upper() if value in KEYWORDS else "IDENT"
        elif ch.isdigit():
            j = i + 1
            while j < n and source[j].isdigit(): j += 1
            value, kind = source[i:j], "NUMBER"
        elif source.startswith(":=", i):
            j, value, kind = i + 2, ":=", "ASSIGN"
        elif source.startswith(">=", i) or source.startswith("!=", i):
            raise LexError("У SIPL підтримуються лише оператори = та >", SourceSpan(line,col,line,col+2))
        elif ch in "+-*=>;()":
            j, value = i + 1, ch
            kind = {"+":"PLUS","-":"MINUS","*":"STAR","=":"EQ",">":"GT",
                    ";":"SEMI","(":"LPAREN",")":"RPAREN"}[ch]
        elif ch in "¬∨":
            j, value, kind = i + 1, ch, ("NOT" if ch == "¬" else "OR")
        else:
            raise LexError(f"Невідомий символ: {ch!r}", SourceSpan(line,col,line,col+1))
        tokens.append(Token(kind, value, SourceSpan(start_line,start_col,line,col+(j-i))))
        col += j - i
        i = j
    tokens.append(Token("EOF", "", SourceSpan(line,col,line,col)))
    return tokens
