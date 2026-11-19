from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class SourceSpan:
    line: int
    column: int
    end_line: int
    end_column: int

@dataclass(frozen=True)
class Node:
    span: SourceSpan

@dataclass(frozen=True)
class Number(Node):
    value: int

@dataclass(frozen=True)
class Variable(Node):
    name: str

@dataclass(frozen=True)
class BinaryArithmetic(Node):
    op: str
    left: "Expr"
    right: "Expr"

@dataclass(frozen=True)
class Comparison(Node):
    op: str
    left: "Expr"
    right: "Expr"

@dataclass(frozen=True)
class BooleanBinary(Node):
    op: str
    left: "Condition"
    right: "Condition"

@dataclass(frozen=True)
class BooleanNot(Node):
    operand: "Condition"

Expr = Union[Number, Variable, BinaryArithmetic]
Condition = Union[Comparison, BooleanBinary, BooleanNot]

@dataclass(frozen=True)
class Assign(Node):
    name: str
    expression: Expr

@dataclass(frozen=True)
class Sequence(Node):
    first: "Statement"
    second: "Statement"

@dataclass(frozen=True)
class If(Node):
    condition: Condition
    then_branch: "Statement"
    else_branch: "Statement"

@dataclass(frozen=True)
class While(Node):
    condition: Condition
    body: "Statement"

@dataclass(frozen=True)
class Block(Node):
    statement: "Statement"

@dataclass(frozen=True)
class Skip(Node):
    pass

Statement = Union[Assign, Sequence, If, While, Block, Skip]

@dataclass(frozen=True)
class Program(Node):
    statement: Statement
