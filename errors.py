from dataclasses import dataclass
from .ast import SourceSpan

@dataclass
class SIPLError(Exception):
    message: str
    span: SourceSpan | None = None
    def __str__(self) -> str:
        if self.span:
            return f"{self.message} (рядок {self.span.line}, колонка {self.span.column})"
        return self.message

class LexError(SIPLError):
    pass

class ParseError(SIPLError):
    pass

class RuntimeSIPLError(SIPLError):
    pass
