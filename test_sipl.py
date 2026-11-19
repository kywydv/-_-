import pytest
from sipl import parse, Interpreter
from sipl.errors import ParseError, RuntimeSIPLError

def run(src, state=None, limit=1000):
    return Interpreter(limit).execute(parse(src),state)

def test_assignment_and_arithmetic():
    r=run("begin X := 2 + 3 * 4 end")
    assert r.state == {"X":14}

def test_sequence_and_skip():
    r=run("begin X := 10; skip; X := X - 3 end")
    assert r.state["X"] == 7

def test_if_true():
    r=run("begin if X > 0 then Y := 1 else Y := 2 end",{"X":5})
    assert r.state["Y"] == 1

def test_if_false():
    r=run("begin if X > 0 then Y := 1 else Y := 2 end",{"X":0})
    assert r.state["Y"] == 2

def test_while():
    r=run("begin Y := 3; while Y > 0 do Y := Y - 1 end")
    assert r.state["Y"] == 0

def test_boolean_or_not():
    r=run("begin if ¬(X > 0) ∨ X = 0 then Y := 1 else Y := 0 end",{"X":0})
    assert r.state["Y"] == 1

def test_block():
    r=run("begin begin X := 4 end end")
    assert r.state["X"] == 4

def test_uninitialized_variable():
    with pytest.raises(RuntimeSIPLError):
        run("begin X := Y + 1 end")

def test_syntax_error():
    with pytest.raises(ParseError):
        parse("begin X = 2 end")

def test_missing_end():
    with pytest.raises(ParseError):
        parse("begin X := 2")

def test_infinite_loop_limit():
    with pytest.raises(RuntimeSIPLError):
        run("begin while X = 0 do skip end",{"X":0},limit=5)

def test_trace_events():
    r=run("begin X := 1 end")
    names=[e.event for e in r.trace]
    assert "BeforeStatement" in names
    assert "AfterStatement" in names
    assert "VariableChanged" in names
    assert "ProgramFinished" in names
