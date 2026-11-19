import argparse, json, sys
from pathlib import Path
from .parser import parse
from .interpreter import Interpreter
from .errors import SIPLError
from .serialize import to_dict

def main(argv=None):
    p = argparse.ArgumentParser(prog="sipl",description="Інструментарій мови SIPL")
    p.add_argument("command",choices=["parse","check","run","trace"])
    p.add_argument("file")
    p.add_argument("--state",default="{}",help="Початковий стан у JSON")
    p.add_argument("--max-steps",type=int,default=10000)
    p.add_argument("--json",action="store_true",help="Вивести структурований JSON")
    args = p.parse_args(argv)
    try:
        source = Path(args.file).read_text(encoding="utf-8")
        program = parse(source)
        if args.command == "parse":
            result = {"ok":True,"ast":to_dict(program)}
        elif args.command == "check":
            result = {"ok":True,"message":"Синтаксис коректний"}
        else:
            state = json.loads(args.state)
            if not isinstance(state,dict) or any(not isinstance(v,int) for v in state.values()):
                raise ValueError("--state має бути JSON-об'єктом з цілими значеннями")
            execution = Interpreter(args.max_steps).execute(program,state)
            result = {"ok":True,"state":execution.state,"steps":execution.steps}
            if args.command == "trace": result["trace"] = to_dict(execution.trace)
        if args.json or args.command in ("parse","trace"):
            print(json.dumps(result,ensure_ascii=False,indent=2))
        else:
            print(result.get("message", "Виконання завершено."))
            if "state" in result: print("Стан:",json.dumps(result["state"],ensure_ascii=False))
        return 0
    except (SIPLError,ValueError,json.JSONDecodeError,OSError) as exc:
        error = {"ok":False,"error":str(exc)}
        print(json.dumps(error,ensure_ascii=False) if args.json else f"Помилка: {exc}",file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
