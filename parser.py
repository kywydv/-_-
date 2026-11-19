from .ast import *
from .lexer import tokenize, Token
from .errors import ParseError

class Parser:
    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def accept(self, kind: str) -> Token | None:
        if self.current.kind == kind:
            t = self.current; self.pos += 1; return t
        return None

    def expect(self, kind: str, expected: str | None = None) -> Token:
        t = self.accept(kind)
        if t: return t
        raise ParseError(f"Очікувалося {expected or kind}, отримано {self.current.value or 'кінець файлу'}",
                         self.current.span)

    def span(self, start: Token, end: Token | None = None) -> SourceSpan:
        e = end or start
        return SourceSpan(start.span.line, start.span.column, e.span.end_line, e.span.end_column)

    def parse(self) -> Program:
        start = self.expect("BEGIN", "begin")
        stmt = self.statement()
        end = self.expect("END", "end")
        self.expect("EOF")
        return Program(self.span(start,end), stmt)

    def statement(self) -> Statement:
        node = self.atom()
        while (semi := self.accept("SEMI")) is not None:
            right = self.atom()
            node = Sequence(SourceSpan(node.span.line,node.span.column,
                                        right.span.end_line,right.span.end_column), node, right)
        return node

    def atom(self) -> Statement:
        t = self.current
        if self.accept("SKIP"):
            return Skip(t.span)
        if self.accept("IDENT"):
            self.expect("ASSIGN", ':=')
            e = self.expression()
            return Assign(SourceSpan(t.span.line,t.span.column,e.span.end_line,e.span.end_column), t.value, e)
        if self.accept("BEGIN"):
            s = self.statement()
            end = self.expect("END", "end")
            return Block(self.span(t,end), s)
        if self.accept("IF"):
            cond = self.condition()
            self.expect("THEN", "then")
            yes = self.atom()
            self.expect("ELSE", "else")
            no = self.atom()
            return If(SourceSpan(t.span.line,t.span.column,no.span.end_line,no.span.end_column),cond,yes,no)
        if self.accept("WHILE"):
            cond = self.condition()
            self.expect("DO", "do")
            body = self.atom()
            return While(SourceSpan(t.span.line,t.span.column,body.span.end_line,body.span.end_column),cond,body)
        raise ParseError("Очікувався оператор присвоювання, if, while, begin або skip", t.span)

    def expression(self, min_prec: int = 0) -> Expr:
        t = self.current
        if self.accept("NUMBER"):
            left: Expr = Number(t.span,int(t.value))
        elif self.accept("IDENT"):
            left = Variable(t.span,t.value)
        elif self.accept("LPAREN"):
            left = self.expression()
            self.expect("RPAREN", "')'")
        else:
            raise ParseError("Очікувалося число, ім'я змінної або '('", t.span)
        prec = {"PLUS":10,"MINUS":10,"STAR":20}
        while self.current.kind in prec and prec[self.current.kind] >= min_prec:
            op = self.current; self.pos += 1
            right = self.expression(prec[op.kind] + 1)
            left = BinaryArithmetic(SourceSpan(left.span.line,left.span.column,
                                               right.span.end_line,right.span.end_column),
                                    op.value,left,right)
        return left

    def condition(self, min_prec: int = 0) -> Condition:
        t = self.current
        if self.accept("NOT"):
            operand = self.condition(30)
            left: Condition = BooleanNot(SourceSpan(t.span.line,t.span.column,
                                                       operand.span.end_line,operand.span.end_column),operand)
        elif self.accept("LPAREN"):
            left = self.condition()
            self.expect("RPAREN", "')'")
        else:
            a = self.expression()
            op = self.current
            if op.kind not in ("EQ","GT"):
                raise ParseError("Очікувався оператор порівняння '=' або '>'", op.span)
            self.pos += 1
            b = self.expression()
            left = Comparison(SourceSpan(a.span.line,a.span.column,b.span.end_line,b.span.end_column),
                              op.value,a,b)
        while self.current.kind == "OR" and min_prec <= 10:
            op = self.current; self.pos += 1
            right = self.condition(11)
            left = BooleanBinary(SourceSpan(left.span.line,left.span.column,
                                             right.span.end_line,right.span.end_column),op.value,left,right)
        return left

def parse(source: str) -> Program:
    return Parser(source).parse()
