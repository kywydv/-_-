__version__ = "0.1.0"
from .parser import parse
from .interpreter import Interpreter, ExecutionResult
__all__ = ["parse", "Interpreter", "ExecutionResult"]
