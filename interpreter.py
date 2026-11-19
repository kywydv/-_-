from dataclasses import dataclass, asdict
from typing import Any, Iterator
from .ast import *
from .errors import RuntimeSIPLError

@dataclass
class TraceEvent:
    event: str
    line: int
    column: int
    statement: str
    state: dict[str, int]
    details: dict[str, Any]

@dataclass
class ExecutionResult:
    state: dict[str, int]
    trace: list[TraceEvent]
    steps: int

class Interpreter:
    def __init__(self, max_steps: int = 10000):
        self.max_steps = max_steps
        self.state: dict[str,int] = {}
        self.trace: list[TraceEvent] = []
        self.steps = 0

    def _event(self, event: str, node: Node, statement: str, **details: Any) -> None:
        self.trace.append(TraceEvent(event,node.span.line,node.span.column,statement,
                                     dict(self.state),details))

    def eval_expr(self, e: Expr) -> int:
        if isinstance(e, Number): return e.value
        if isinstance(e, Variable):
            if e.name not in self.state:
                raise RuntimeSIPLError(f"Змінна '{e.name}' не ініціалізована",e.span)
            return self.state[e.name]
        if isinstance(e, BinaryArithmetic):
            a,b = self.eval_expr(e.left),self.eval_expr(e.right)
            if e.op == "+": return a+b
            if e.op == "-": return a-b
            if e.op == "*": return a*b
        raise RuntimeSIPLError("Невідомий арифметичний вираз",e.span)

    def eval_condition(self, c: Condition) -> bool:
        if isinstance(c, Comparison):
            a,b = self.eval_expr(c.left),self.eval_expr(c.right)
            return a == b if c.op == "=" else a > b
        if isinstance(c, BooleanNot): return not self.eval_condition(c.operand)
        if isinstance(c, BooleanBinary):
            if c.op == "∨": return self.eval_condition(c.left) or self.eval_condition(c.right)
        raise RuntimeSIPLError("Невідома умова",c.span)

    def execute(self, program: Program, initial_state: dict[str,int] | None = None) -> ExecutionResult:
        self.state = dict(initial_state or {})
        self.trace, self.steps = [],0
        self._exec(program.statement)
        self._event("ProgramFinished",program,"program")
        return ExecutionResult(dict(self.state),list(self.trace),self.steps)

    def _exec(self, s: Statement) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            raise RuntimeSIPLError(f"Перевищено ліміт кроків ({self.max_steps}); можливий нескінченний цикл",s.span)
        label = type(s).__name__
        self._event("BeforeStatement",s,label)
        if isinstance(s, Assign):
            value = self.eval_expr(s.expression)
            old = self.state.get(s.name)
            self.state[s.name] = value
            self._event("VariableChanged",s,label,name=s.name,old=old,new=value)
        elif isinstance(s, Sequence):
            self._exec(s.first); self._exec(s.second)
        elif isinstance(s, Block):
            self._exec(s.statement)
        elif isinstance(s, If):
            result = self.eval_condition(s.condition)
            self._event("ConditionChecked",s,label,result=result,kind="if")
            self._exec(s.then_branch if result else s.else_branch)
        elif isinstance(s, While):
            while self.eval_condition(s.condition):
                self._event("ConditionChecked",s,label,result=True,kind="while")
                self._exec(s.body)
                self.steps += 1
                if self.steps > self.max_steps:
                    raise RuntimeSIPLError(f"Перевищено ліміт кроків ({self.max_steps}); можливий нескінченний цикл",s.span)
            self._event("ConditionChecked",s,label,result=False,kind="while")
        elif isinstance(s, Skip):
            pass
        else:
            raise RuntimeSIPLError("Невідомий оператор",s.span)
        self._event("AfterStatement",s,label)
