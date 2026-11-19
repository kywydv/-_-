# Minimal Debug Adapter Protocol transport scaffold.
# The adapter exposes the project trace as debugger stops; integration testing in VS Code is required.
import json, sys, os, subprocess, threading

def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line: return None
        if line in (b"\r\n", b"\n"): break
        k, _, v = line.decode("utf-8").partition(":")
        headers[k.lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))

def send(msg):
    body = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode()+body)
    sys.stdout.buffer.flush()

seq = 1
def response(req, body=None, success=True, message=None):
    global seq
    out={"seq":seq,"type":"response","request_seq":req["seq"],"command":req["command"],
         "success":success,"body":body or {}}
    if message: out["message"]=message
    seq += 1; send(out)

def event(name, body=None):
    global seq
    send({"seq":seq,"type":"event","event":name,"body":body or {}})
    seq += 1

def main():
    global seq
    program=None; trace=[]; index=0; breakpoints=[]; variables={}
    while True:
        req=read_message()
        if req is None: break
        cmd=req.get("command"); args=req.get("arguments",{})
        if cmd=="initialize":
            response(req,{"supportsConfigurationDoneRequest":True,"supportsStepInTargetsRequest":False,
                          "supportsEvaluateForHovers":True,"supportsTerminateRequest":True})
            event("initialized")
        elif cmd=="launch":
            program=args.get("program")
            if not program or not os.path.isfile(program):
                response(req,success=False,message="Не знайдено SIPL-файл"); continue
            # Run trace through the installed package, preserving structured events.
            root=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
            env=os.environ.copy()
            env["PYTHONPATH"]=os.path.join(root,"src")+os.pathsep+env.get("PYTHONPATH","")
            proc=subprocess.run([sys.executable,"-m","sipl.cli","trace",program,"--json"],
                                capture_output=True,text=True,env=env)
            try: trace=json.loads(proc.stdout).get("trace",[])
            except Exception: trace=[]
            index=0; variables={}
            response(req)
        elif cmd=="setBreakpoints":
            src=args.get("source",{}).get("path","")
            requested=args.get("breakpoints",[])
            breakpoints=[b.get("line") for b in requested]
            response(req,{"breakpoints":[{"verified":True,"line":n} for n in breakpoints]})
        elif cmd=="configurationDone":
            response(req)
            if args.get("stopOnEntry",True): event("stopped",{"reason":"entry","threadId":1})
            else: event("stopped",{"reason":"step","threadId":1})
        elif cmd=="threads":
            response(req,{"threads":[{"id":1,"name":"SIPL main"}]})
        elif cmd=="stackTrace":
            response(req,{"stackFrames":[{"id":1,"name":"SIPL execution","line":
                (trace[index].get("line",1) if index<len(trace) else 1),"column":1,
                "source":{"name":os.path.basename(program or "program.sipl"),"path":program or ""}}],
                "totalFrames":1})
        elif cmd=="scopes":
            response(req,{"scopes":[{"name":"Variables","variablesReference":1,"expensive":False}]})
        elif cmd=="variables":
            if index<len(trace): variables=trace[index].get("state",{})
            response(req,{"variables":[{"name":k,"value":str(v),"type":"int","variablesReference":0}
                                      for k,v in variables.items()]})
        elif cmd=="evaluate":
            response(req,{"result":"Доступні змінні: "+", ".join(f"{k}={v}" for k,v in variables.items()),
                          "variablesReference":0})
        elif cmd in ("next","stepIn","continue"):
            if index < len(trace)-1: index += 1
            if index<len(trace):
                event("stopped",{"reason":"step","threadId":1})
            else:
                event("terminated")
            response(req,{"allThreadsContinued":True})
        elif cmd in ("disconnect","terminate"):
            response(req); event("terminated"); break
        else:
            response(req,success=False,message="Команда DAP поки не підтримується: "+str(cmd))

if __name__=="__main__":
    main()
