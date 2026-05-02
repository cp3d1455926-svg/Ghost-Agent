# -*- coding: utf-8 -*-
"""
Ghost Agent v2.1 - Three-Core Fusion + Pluggable AI Backend
Authors: Ghost & Jake

Architecture:
    Ghost Agent = Pluggable AI + OpenClaw Execution + Hermes Memory + ClaudeCode Coding

AI Backends (swappable):
    - TemplateBackend: Template matching (default, no API needed)
    - OpenAIBackend: ChatGPT API
    - OllamaBackend: Local models
    
Usage:
    # Default (template matching, no API key)
    agent = GhostAgent()
    
    # With ChatGPT
    agent = GhostAgent(ai=OpenAIBackend(api_key="sk-xxx"))
    
    # With local Ollama
    agent = GhostAgent(ai=OllamaBackend(model="codellama"))
"""
import subprocess, os, sys, json, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
PROJECTS_DIR = WORKSPACE / "projects"
LOGS_DIR = WORKSPACE / "logs"
MEMORY_DIR = WORKSPACE / "memory_v2"
MAX_FIX_ROUNDS = 5
TIMEOUT = 30

for d in [PROJECTS_DIR, LOGS_DIR, MEMORY_DIR]:
    d.mkdir(exist_ok=True)


# ============================================================
# AI Backend Interface - Pluggable
# ============================================================
class AIBackend:
    """Base class for all AI backends"""
    
    def generate_code(self, requirement, language="python", context=None):
        raise NotImplementedError
    
    def fix_code(self, code, error, language="python"):
        raise NotImplementedError


class TemplateBackend(AIBackend):
    """Template matching backend (default) - no API key needed"""
    
    def __init__(self):
        self.templates = TemplateLibrary()
    
    def generate_code(self, requirement, language="python", context=None):
        return self.templates.generate(requirement, language)
    
    def fix_code(self, code, error, language="python"):
        return code


class LongCatBackend(AIBackend):
    """LongCat model backend"""
    
    def __init__(self, api_key=None, model="LongCat-2.0-Preview", base_url=None):
        self.model = model
        self.api_key = api_key or os.environ.get("LONGCAT_API_KEY", "")
        self.base_url = base_url or os.environ.get("LONGCAT_BASE_URL", "https://api.longcat.chat/openai/v1")
        # If no API key provided, try to load from OpenClaw config
        if not self.api_key:
            self._load_from_openclaw_config()
    
    def _load_from_openclaw_config(self):
        """Try to load API key from OpenClaw models.json"""
        config_paths = [
            Path(os.path.expanduser("~/.openclaw/agents/main/agent/models.json")),
            Path("C:/Users/shenz/.openclaw/agents/main/agent/models.json"),
        ]
        for p in config_paths:
            if p.exists():
                try:
                    config = json.loads(p.read_text(encoding="utf-8"))
                    providers = config.get("providers", {})
                    # Try different provider names
                    for name in ["longcat", "longCat"]:
                        if name in providers:
                            self.api_key = providers[name].get("apiKey", "")
                            self.base_url = providers[name].get("baseUrl", self.base_url)
                            # Find the model id
                            for m in providers[name].get("models", []):
                                if self.model in m.get("id", ""):
                                    self.model = m["id"]
                                    break
                            break
                except Exception:
                    pass
    
    def generate_code(self, requirement, language="python", context=None):
        prompt = "You are a professional " + language + " programmer. Generate complete, runnable code.\nRequirement: " + requirement + "\nReturn code only, no explanation:"
        return self._call(prompt)
    
    def fix_code(self, code, error, language="python"):
        prompt = "Fix the " + language + " code error:\nCode:\n" + code + "\nError:\n" + error + "\nReturn fixed code only:"
        return self._call(prompt)
    
    def _call(self, prompt):
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 2000,
            }).encode()
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = "Bearer " + self.api_key
            req = urllib.request.Request(
                self.base_url + "/chat/completions",
                data=data, headers=headers
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                content = result["choices"][0]["message"]["content"]
                match = re.search(r"```(?:python|javascript|js)?\s*\n(.*?)```", content, re.DOTALL)
                return match.group(1).strip() if match else content.strip()
        except Exception as e:
            print("[LongCatBackend] Error: " + str(e))
            return "# Generation failed: " + str(e)


class OpenAIBackend(LongCatBackend):
    """ChatGPT API backend (same interface as LongCat)"""
    
    def __init__(self, api_key, model="gpt-4", base_url="https://api.openai.com/v1"):
        super().__init__(api_key=api_key, model=model, base_url=base_url)


class OllamaBackend(AIBackend):
    """Local Ollama backend"""
    
    def __init__(self, model="codellama", host="http://localhost:11434"):
        self.model = model
        self.host = host
    
    def generate_code(self, requirement, language="python", context=None):
        prompt = "[INST] You are a professional " + language + " programmer. Generate complete, runnable code.\nRequirement: " + requirement + "\nReturn code only [/INST]"
        return self._call(prompt)
    
    def fix_code(self, code, error, language="python"):
        prompt = "[INST] Fix the " + language + " code error:\nCode:\n" + code + "\nError:\n" + error + "\nReturn fixed code only [/INST]"
        return self._call(prompt)
    
    def _call(self, prompt):
        try:
            import urllib.request
            data = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
            req = urllib.request.Request(self.host + "/api/generate", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "").strip()
        except Exception as e:
            print("[OllamaBackend] Error: " + str(e))
            return "# Generation failed: " + str(e)


# ============================================================
# Template Library
# ============================================================
class TemplateLibrary:
    """Pre-built code templates"""
    
    def generate(self, req, lang):
        if lang != "python":
            return "// TODO: " + req
        req_l = req.lower()
        generators = [
            (["data", "analysis", "analyze", "stat"], self._data_analysis),
            (["math", "calc", "calculator"], self._math_calc),
            (["api", "server", "web server"], self._api_server),
            (["file", "organize", "cleanup"], self._file_organizer),
            (["web", "scrape", "crawl", "spider"], self._web_scraper),
            (["image", "picture", "photo"], self._image_proc),
            (["auto", "schedule", "cron"], self._auto_script),
            (["bot", "spider"], self._web_bot),
            (["game", "guess"], self._game),
        ]
        for keywords, gen in generators:
            if any(k in req_l for k in keywords):
                return gen(req)
        return self._generic(req)

    def _data_analysis(self, req):
        return (
            '"""' + req + '"""\n'
            'from collections import Counter\n'
            'import math\n'
            '\n'
            'def analyze(data):\n'
            '    if not data: return {"error": "empty"}\n'
            '    r = {"count": len(data)}\n'
            '    if all(isinstance(x, (int, float)) for x in data):\n'
            '        s = sorted(data); n = len(data); avg = sum(data)/n\n'
            '        r["min"] = min(data)\n'
            '        r["max"] = max(data)\n'
            '        r["sum"] = sum(data)\n'
            '        r["avg"] = avg\n'
            '        r["median"] = s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2\n'
            '        r["std"] = math.sqrt(sum((x-avg)**2 for x in data)/n)\n'
            '    if all(isinstance(x, str) for x in data):\n'
            '        lens = [len(x) for x in data]\n'
            '        r["shortest"] = min(lens)\n'
            '        r["longest"] = max(lens)\n'
            '        r["avg_len"] = sum(lens)/len(lens)\n'
            '        r["common"] = Counter(data).most_common(5)\n'
            '    return r\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    nums = [23,45,67,12,89,34,56,78,91,15,62,37]\n'
            '    for k,v in analyze(nums).items():\n'
            '        print("  " + str(k) + ": " + str(v))\n'
        )

    def _math_calc(self, req):
        return (
            '"""' + req + '"""\n'
            'import math\n'
            '\n'
            'def add(a,b): return a+b\n'
            'def sub(a,b): return a-b\n'
            'def mul(a,b): return a*b\n'
            'def div(a,b): return a/b if b else float("inf")\n'
            'def power(a,b): return a**b\n'
            'def sqrt(a): return math.sqrt(a) if a>=0 else None\n'
            'def fact(n): return math.factorial(n) if n>=0 else None\n'
            'def fib(n):\n'
            '    if n<=0: return []\n'
            '    f=[0,1]\n'
            '    for i in range(2,n): f.append(f[-1]+f[-2])\n'
            '    return f if n>1 else [0]\n'
            'def is_prime(n):\n'
            '    if n<2: return False\n'
            '    return all(n%i for i in range(2,int(math.sqrt(n))+1))\n'
            'gcd = math.gcd\n'
            'def lcm(a,b): return abs(a*b)//math.gcd(a,b)\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    print("2+3=" + str(add(2,3)) + " 10-4=" + str(sub(10,4)))\n'
            '    print("6*7=" + str(mul(6,7)) + " 100/3=" + str(round(div(100,3),2)))\n'
            '    print("2^10=" + str(power(2,10)) + " sqrt(144)=" + str(sqrt(144)))\n'
            '    print("10!=" + str(fact(10)))\n'
            '    print("fib(15)=" + str(fib(15)))\n'
            '    print("is_prime(17)=" + str(is_prime(17)))\n'
            '    print("gcd(12,18)=" + str(gcd(12,18)) + " lcm=" + str(lcm(12,18)))\n'
        )

    def _api_server(self, req):
        return (
            '"""' + req + '"""\n'
            'import json\n'
            'from http.server import HTTPServer, BaseHTTPRequestHandler\n'
            'from datetime import datetime\n'
            '\n'
            'class H(BaseHTTPRequestHandler):\n'
            '    routes={}\n'
            '    @classmethod\n'
            '    def route(cls,p):\n'
            '        def d(fn): cls.routes[p]=fn; return fn\n'
            '        return d\n'
            '    def do_GET(self):\n'
            '        from urllib.parse import urlparse\n'
            '        p=urlparse(self.path)\n'
            '        fn=H.routes.get(p.path,lambda s,x:{"error":"404"})\n'
            '        self._j(fn(self,p))\n'
            '    def _j(self,data,st=200):\n'
            '        self.send_response(st)\n'
            '        self.send_header("Content-Type","application/json;charset=utf-8")\n'
            '        self.end_headers()\n'
            '        self.wfile.write(json.dumps(data,ensure_ascii=False).encode())\n'
            '    def log_message(self,*a): pass\n'
            '\n'
            '@H.route("/")\n'
            'def home(h,p): return {"msg":"Ghost Agent API","time":datetime.now().isoformat()}\n'
            '@H.route("/health")\n'
            'def health(h,p): return {"status":"ok"}\n'
            '@H.route("/time")\n'
            'def time(h,p): return {"time":datetime.now().isoformat()}\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    s=HTTPServer(("localhost",8080),H)\n'
            '    print("API: http://localhost:8080")\n'
            '    s.serve_forever()\n'
        )

    def _file_organizer(self, req):
        return (
            '"""' + req + '"""\n'
            'from pathlib import Path\n'
            'import shutil\n'
            'from collections import defaultdict\n'
            '\n'
            'def organize(d):\n'
            '    p=Path(d)\n'
            '    if not p.exists(): print("Dir not found: " + d); return\n'
            '    tm={".py":"Python",".js":"JS",".html":"HTML",".css":"CSS",\n'
            '        ".json":"JSON",".md":"Markdown",".txt":"Text",\n'
            '        ".jpg":"Images",".png":"Images",".gif":"Images",\n'
            '        ".mp4":"Videos",".mp3":"Audio",".zip":"Archives",\n'
            '        ".pdf":"PDF",".doc":"Documents",".xls":"Sheets",".exe":"Executables"}\n'
            '    stats=defaultdict(list)\n'
            '    for f in p.iterdir():\n'
            '        if f.is_file():\n'
            '            folder=tm.get(f.suffix.lower(),"Others")\n'
            '            t=p/folder; t.mkdir(exist_ok=True)\n'
            '            shutil.move(str(f),str(t/f.name))\n'
            '            stats[folder].append(f.name)\n'
            '    total=sum(len(v) for v in stats.values())\n'
            '    print("Organized " + str(total) + " files")\n'
            '    for folder,files in sorted(stats.items()):\n'
            '        print("  [" + folder + "]: " + str(len(files)))\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    import sys\n'
            '    organize(sys.argv[1] if len(sys.argv)>1 else ".")\n'
        )

    def _web_scraper(self, req):
        return (
            '"""' + req + '"""\n'
            'import urllib.request, re\n'
            '\n'
            'def fetch(url):\n'
            '    req=urllib.request.Request(url,headers={"User-Agent":"GhostAgent/2.0"})\n'
            '    with urllib.request.urlopen(req,timeout=10) as r:\n'
            '        return r.read().decode("utf-8",errors="ignore")\n'
            '\n'
            'def links(html): return re.findall(r\'href="(https?://[^"]+)\',html)\n'
            'def text(html):\n'
            '    t=re.sub(r"<[^>]+>","",html)\n'
            '    return re.sub(r"\\s+"," ",t).strip()\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    html=fetch("https://example.com")\n'
            '    print("Links: " + str(len(links(html))))\n'
            '    print("Text: " + text(html)[:200])\n'
        )

    def _image_proc(self, req):
        return (
            '"""' + req + '"""\n'
            'Need: pip install Pillow\n'
            '"""\n'
            'from pathlib import Path\n'
            '\n'
            'def info(fp):\n'
            '    try:\n'
            '        from PIL import Image\n'
            '        img=Image.open(fp)\n'
            '        return {"format":img.format,"size":img.size,"mode":img.mode}\n'
            '    except ImportError: return {"error":"pip install Pillow"}\n'
            '    except Exception as e: return {"error":str(e)}\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    import sys\n'
            '    if len(sys.argv)>1:\n'
            '        for k,v in info(sys.argv[1]).items():\n'
            '            print("  " + str(k) + ": " + str(v))\n'
        )

    def _auto_script(self, req):
        return (
            '"""' + req + '"""\n'
            'import time\n'
            'from datetime import datetime\n'
            '\n'
            'def task():\n'
            '    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")\n'
            '    print("[" + ts + "] Task executed!")\n'
            '\n'
            'def run_loop(interval=60):\n'
            '    print("Running every " + str(interval) + "s")\n'
            '    try:\n'
            '        while True: task(); time.sleep(interval)\n'
            '    except KeyboardInterrupt: print("\\nStopped")\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    import sys\n'
            '    run_loop() if "--loop" in sys.argv else task()\n'
        )

    def _web_bot(self, req):
        return (
            '"""' + req + '"""\n'
            'import urllib.request, re, time\n'
            '\n'
            'class WebBot:\n'
            '    def __init__(self): self.visited=set()\n'
            '    def fetch(self,url):\n'
            '        req=urllib.request.Request(url,headers={"User-Agent":"GhostBot/2.0"})\n'
            '        with urllib.request.urlopen(req,timeout=10) as r:\n'
            '            return r.read().decode("utf-8",errors="ignore")\n'
            '    def crawl(self,start,max_p=5):\n'
            '        q=[start]\n'
            '        while q and len(self.visited)<max_p:\n'
            '            url=q.pop(0)\n'
            '            if url in self.visited: continue\n'
            '            try:\n'
            '                html=self.fetch(url)\n'
            '                self.visited.add(url)\n'
            '                print("Crawled: " + url + " (" + str(len(html)) + " bytes)")\n'
            '                q.extend(re.findall(r\'href="(https?://[^"]+)\',html)[:3])\n'
            '                time.sleep(1)\n'
            '            except Exception as e: print("  Error: " + str(e))\n'
            '        print("Done! " + str(len(self.visited)) + " pages")\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    WebBot().crawl("https://example.com")\n'
        )

    def _game(self, req):
        return (
            '"""' + req + '"""\n'
            'import random\n'
            '\n'
            'def guess():\n'
            '    s=random.randint(1,100); n=0\n'
            '    print("Guess the number (1-100)")\n'
            '    while True:\n'
            '        try:\n'
            '            g=int(input("Your guess: ")); n+=1\n'
            '            if g<s: print("Too low!")\n'
            '            elif g>s: print("Too high!")\n'
            '            else: print("Correct! Tries: " + str(n)); break\n'
            '        except: print("Enter a number!")\n'
            '\n'
            'if __name__ == "__main__": guess()\n'
        )

    def _generic(self, req):
        return (
            '"""' + req + '"""\n'
            'Ghost Agent v2.1\n'
            '"""\n'
            'def main():\n'
            '    print("Hello from Ghost Agent!")\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        )


# ============================================================
# Hermes Memory System
# ============================================================
class HermesMemory:
    def __init__(self):
        self.l0 = {}
        self.l1 = self._load("warm.json")
        self.l2 = self._load("cold.json")
        self.errors = self._load("errors.json")
    
    def _load(self, f):
        p = MEMORY_DIR / f
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    
    def _save(self, data, f):
        (MEMORY_DIR / f).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def remember(self, key, val, layer="l1"):
        e = {"key": key, "value": val, "time": datetime.now().isoformat()}
        if layer == "l0": self.l0[key] = e
        elif layer == "l1": self.l1[key] = e; self._save(self.l1, "warm.json")
        elif layer == "l2": self.l2[key] = e; self._save(self.l2, "cold.json")
    
    def recall(self, key):
        for layer in [self.l0, self.l1, self.l2]:
            if key in layer: return layer[key]["value"]
        return None
    
    def remember_error(self, etype, detail, fix, ok):
        if "list" not in self.errors: self.errors["list"] = []
        self.errors["list"].append({"type": etype, "detail": detail[:200], "fix": fix, "ok": ok, "time": datetime.now().isoformat()})
        self.errors["list"] = self.errors["list"][-100:]
        self._save(self.errors, "errors.json")
    
    def find_fix(self, etype):
        for e in reversed(self.errors.get("list", [])):
            if e["type"] == etype and e["ok"]: return e["fix"]
        return None


# ============================================================
# OpenClaw Executor
# ============================================================
class OpenClawExecutor:
    def run_python(self, code, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        wd.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        f = wd / ("_run_" + ts + ".py")
        f.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", str(f)], capture_output=True, text=True, timeout=TIMEOUT, cwd=str(wd), env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired: return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e: return {"success": False, "stdout": "", "stderr": str(e)}
    
    def run_shell(self, cmd, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, cwd=str(wd), shell=True)
            return {"success": r.returncode == 0, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
        except subprocess.TimeoutExpired: return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e: return {"success": False, "stdout": "", "stderr": str(e)}
    
    def run_node(self, code, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        wd.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        f = wd / ("_run_" + ts + ".js")
        f.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=TIMEOUT, cwd=str(wd))
            return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired: return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e: return {"success": False, "stdout": "", "stderr": str(e)}


# ============================================================
# SmartFixer V2
# ============================================================
class SmartFixerV2:
    def __init__(self, memory): self.memory = memory
    
    def fix(self, code, error, lang="python"):
        fixes = []
        if lang == "python":
            m = re.search(r"NameError: name '(\w+)' is not defined\. Did you mean: '(\w+)'", error)
            if m: code = code.replace(m.group(1), m.group(2)); fixes.append("Spelling: " + m.group(1) + " -> " + m.group(2))
            m = re.search(r"No module named '(\w+)'", error)
            if m: fixes.append("pip install " + m.group(1))
            m = re.search(r"SyntaxError.*line (\d+)", error)
            if m:
                ln = int(m.group(1)); lines = code.split("\n")
                if 0 < ln <= len(lines):
                    for kw in ["for","if","elif","else","def","class","while","try","except","with"]:
                        if lines[ln-1].strip().startswith(kw) and not lines[ln-1].rstrip().endswith(":"):
                            lines[ln-1] = lines[ln-1].rstrip() + ":"; code = "\n".join(lines); fixes.append("L" + str(ln) + ": add colon"); break
            if "expected an indented block" in error:
                m = re.search(r"line (\d+)", error)
                if m:
                    ln = int(m.group(1)); lines = code.split("\n")
                    if 0 < ln <= len(lines): lines[ln-1] = "    " + lines[ln-1].lstrip(); code = "\n".join(lines); fixes.append("L" + str(ln) + ": add indent")
            if "KeyError" in error: fixes.append("Use .get() for missing key")
            if "IndexError" in error: fixes.append("Index out of range")
            if "FileNotFoundError" in error: fixes.append("File not found")
            if "ZeroDivisionError" in error: fixes.append("Division by zero")
            if "AttributeError" in error: fixes.append("Attribute error")
            if "TypeError" in error: fixes.append("Type error")
        return code, "; ".join(fixes) if fixes else "Cannot auto-fix", len(fixes) > 0


# ============================================================
# Task Planner
# ============================================================
class TaskPlanner:
    def plan(self, req):
        req = req.lower()
        if any(k in req for k in ["create","new","write","generate","build","make"]):
            return [{"action":"generate","desc":"Generate code"},{"action":"run","desc":"Run test"},{"action":"fix","desc":"Auto-fix"}]
        if any(k in req for k in ["modify","change","fix","update"]):
            return [{"action":"read","desc":"Read code"},{"action":"modify","desc":"Modify"},{"action":"test","desc":"Test"}]
        if any(k in req for k in ["organize","clean","sort"]):
            return [{"action":"scan","desc":"Scan directory"},{"action":"execute","desc":"Execute"}]
        return [{"action":"generate","desc":"Generate code"},{"action":"run","desc":"Run test"}]


# ============================================================
# Ghost Agent v2.1 Main Class
# ============================================================
class GhostAgent:
    """
    Ghost Agent v2.1 - Three-Core Fusion + Pluggable AI Backend
    
    Usage:
        agent = GhostAgent()                                    # Default (template)
        agent = GhostAgent(ai=OpenAIBackend(api_key="sk-xxx"))  # ChatGPT
        agent = GhostAgent(ai=OllamaBackend(model="codellama")) # Local model
    """
    
    def __init__(self, ai=None):
        self.ai = ai or TemplateBackend()
        self.memory = HermesMemory()
        self.executor = OpenClawExecutor()
        self.planner = TaskPlanner()
        self.fixer = SmartFixerV2(self.memory)
        self.history = []

    def do(self, requirement, language="python", project_dir=None):
        print("=" * 60)
        print("Ghost Agent v2.1")
        print("AI Backend: " + self.ai.__class__.__name__)
        print("=" * 60)
        print("Requirement: " + requirement)
        print("Language: " + language)
        print()

        # Plan
        steps = self.planner.plan(requirement)
        print("[Plan] " + " -> ".join(s["desc"] for s in steps))
        print()

        # Generate code
        print("[Generate]")
        context = None
        if project_dir and Path(project_dir).exists():
            r = self.executor.run_shell("dir /b " + project_dir)
            if r["success"]:
                context = {"files": r["stdout"].split("\n")[:10]}
        code = self.ai.generate_code(requirement, language, context)
        print("  Generated " + str(len(code.splitlines())) + " lines")
        print()

        # Run + Auto-fix
        print("[Run + Auto-fix]")
        current_code = code
        fixes = []
        rnd = 0
        for rnd in range(1, MAX_FIX_ROUNDS + 1):
            print("  --- Round " + str(rnd) + " ---")
            result = self.executor.run_python(current_code, project_dir) if language == "python" else self.executor.run_node(current_code, project_dir)
            if result["success"]:
                print("  Success! (round " + str(rnd) + ")")
                break
            else:
                err = result["stderr"]
                print("  Failed: " + err[:100])
                
                # Try SmartFixer first
                new_code, desc, fixed = self.fixer.fix(current_code, err, language)
                if fixed:
                    print("  Fixed: " + desc)
                    fixes.append({"round": rnd, "fix": desc})
                    current_code = new_code
                else:
                    # Try AI backend
                    print("  SmartFixer cannot fix, trying AI...")
                    ai_fixed = self.ai.fix_code(current_code, err, language)
                    if ai_fixed and ai_fixed != current_code:
                        print("  AI fix applied")
                        fixes.append({"round": rnd, "fix": "AI auto-fix"})
                        current_code = ai_fixed
                    else:
                        print("  Cannot fix: " + desc)
                        fixes.append({"round": rnd, "fix": "Cannot fix: " + desc})
                        for p in ["NameError","TypeError","SyntaxError","ModuleNotFoundError","IndentationError","KeyError","IndexError","FileNotFoundError","ZeroDivisionError","AttributeError"]:
                            if p in err:
                                mem_fix = self.memory.find_fix(p)
                                if mem_fix: print("  Memory hint: " + mem_fix)
                                break
                        if rnd == MAX_FIX_ROUNDS: print("  Max rounds reached")
        else:
            result = self.executor.run_python(current_code, project_dir) if language == "python" else self.executor.run_node(current_code, project_dir)

        # Reflect + Remember
        success = result["success"]
        if not success:
            etype = "Unknown"
            for p in ["NameError","TypeError","SyntaxError","ModuleNotFoundError","IndentationError","KeyError","IndexError","FileNotFoundError","ZeroDivisionError","AttributeError"]:
                if p in result["stderr"]: etype = p; break
            self.memory.remember_error(etype, result["stderr"], str(fixes), success)

        self.memory.remember("task:" + requirement[:50], {"requirement": requirement, "success": success, "rounds": rnd, "fixes": fixes})

        print()
        print("=" * 60)
        if success:
            print("TASK COMPLETE!")
            print("Rounds: " + str(rnd))
            if result["stdout"]: print("Output:\n" + result["stdout"][:300])
        else:
            print("TASK FAILED")
            print("Rounds: " + str(rnd))
            print("Error: " + result["stderr"][:200])
        print("=" * 60)

        report = {"success": success, "requirement": requirement, "language": language, "rounds": rnd, "fixes": fixes, "output": result.get("stdout", ""), "error": result.get("stderr", "") if not success else None, "code": current_code}
        self.history.append({"time": datetime.now().isoformat(), "requirement": requirement, "success": success})
        return report


def create_agent(config_path=None):
    """Create Ghost Agent from config file"""
    if config_path is None:
        config_path = Path("ghost_agent_config.json")
    
    if not config_path.exists():
        return GhostAgent()  # Default
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    backend = config.get("backend", "template")
    
    if backend == "longcat":
        return GhostAgent(ai=LongCatBackend(
            model=config.get("longcat_model", "longcat/LongCat-2.0-Preview"),
            base_url=config.get("longcat_base_url", "") or None,
            api_key=config.get("longcat_api_key", "") or None,
        ))
    elif backend == "openai":
        return GhostAgent(ai=OpenAIBackend(
            api_key=config.get("openai_key", ""),
            model=config.get("openai_model", "gpt-4"),
        ))
    elif backend == "ollama":
        return GhostAgent(ai=OllamaBackend(
            model=config.get("ollama_model", "codellama"),
            host=config.get("ollama_host", "http://localhost:11434"),
        ))
    else:
        return GhostAgent()  # Template default


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        # Interactive config mode
        from config import main as config_main
        config_main()
    elif len(sys.argv) > 1:
        agent = create_agent()
        agent.do(" ".join(sys.argv[1:]))
    else:
        print("Usage:")
        print("  python ghost_v21.py --config          # Configure AI backend")
        print("  python ghost_v21.py <requirement>      # Run task")
        print()
        agent = create_agent()
        agent.do("write a data analysis script")
