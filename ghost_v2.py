# -*- coding: utf-8 -*-
"""
Ghost Agent v2.0 — 三核融合架构
作者: 小鬼 & Jake

Ghost Agent = OpenClaw执行力 + Hermes记忆 + ClaudeCode编码
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
    def search(self, query, top_k=5):
        results = []
        for layer in [self.l0, self.l1, self.l2]:
            for k, e in layer.items():
                score = sum(1 for w in query.lower().split() if w in json.dumps(e).lower())
                if score: results.append((score, k, e["value"]))
        return sorted(results, reverse=True)[:top_k]
    def remember_error(self, etype, detail, fix, ok):
        if "list" not in self.errors: self.errors["list"] = []
        self.errors["list"].append({"type": etype, "detail": detail[:200], "fix": fix, "ok": ok, "time": datetime.now().isoformat()})
        self.errors["list"] = self.errors["list"][-100:]
        self._save(self.errors, "errors.json")
    def find_fix(self, etype):
        for e in reversed(self.errors.get("list", [])):
            if e["type"] == etype and e["ok"]: return e["fix"]
        return None

class OpenClawExecutor:
    def run_python(self, code, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        wd.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        f = wd / f"_run_{ts}.py"
        f.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", str(f)], capture_output=True, text=True, timeout=TIMEOUT, cwd=str(wd), env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired: return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e: return {"success": False, "stdout": "", "stderr": str(e)}
    def run_node(self, code, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        wd.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        f = wd / f"_run_{ts}.js"
        f.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=TIMEOUT, cwd=str(wd))
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

class SmartFixerV2:
    def __init__(self, memory): self.memory = memory
    def fix(self, code, error, lang="python"):
        fixes = []
        if lang == "python":
            m = re.search(r"NameError: name '(\w+)' is not defined\. Did you mean: '(\w+)'", error)
            if m: code = code.replace(m.group(1), m.group(2)); fixes.append(f"拼写: {m.group(1)} -> {m.group(2)}")
            m = re.search(r"No module named '(\w+)'", error)
            if m: fixes.append(f"pip install {m.group(1)}")
            m = re.search(r"SyntaxError.*line (\d+)", error)
            if m:
                ln = int(m.group(1)); lines = code.split("\n")
                if 0 < ln <= len(lines):
                    for kw in ["for","if","elif","else","def","class","while","try","except","with"]:
                        if lines[ln-1].strip().startswith(kw) and not lines[ln-1].rstrip().endswith(":"):
                            lines[ln-1] = lines[ln-1].rstrip() + ":"; code = "\n".join(lines); fixes.append(f"L{ln}: 加冒号"); break
            if "expected an indented block" in error:
                m = re.search(r"line (\d+)", error)
                if m:
                    ln = int(m.group(1)); lines = code.split("\n")
                    if 0 < ln <= len(lines): lines[ln-1] = "    " + lines[ln-1].lstrip(); code = "\n".join(lines); fixes.append(f"L{ln}: 加缩进")
            if "KeyError" in error: fixes.append("键不存在，用 .get()")
            if "IndexError" in error: fixes.append("索引越界")
            if "FileNotFoundError" in error: fixes.append("文件不存在")
            if "ZeroDivisionError" in error: fixes.append("除以零")
            if "AttributeError" in error: fixes.append("属性错误")
            if "TypeError" in error: fixes.append("类型错误")
        return code, "; ".join(fixes) if fixes else "无法自动修复", len(fixes) > 0

class TaskPlanner:
    def plan(self, req):
        req = req.lower()
        if any(k in req for k in ["创建","新建","写","生成","做"]):
            return [{"action":"generate","desc":"生成代码"},{"action":"run","desc":"运行测试"},{"action":"fix","desc":"自动修复"}]
        if any(k in req for k in ["修改","改","修复"]):
            return [{"action":"read","desc":"读取代码"},{"action":"modify","desc":"修改"},{"action":"test","desc":"测试"}]
        if any(k in req for k in ["整理","清理"]):
            return [{"action":"scan","desc":"扫描目录"},{"action":"execute","desc":"执行整理"}]
        return [{"action":"generate","desc":"生成代码"},{"action":"run","desc":"运行验证"}]

class GhostAgent:
    def __init__(self):
        self.memory = HermesMemory()
        self.executor = OpenClawExecutor()
        self.planner = TaskPlanner()
        self.fixer = SmartFixerV2(self.memory)
        self.history = []

    def do(self, requirement, language="python", project_dir=None):
        print("=" * 60)
        print("Ghost Agent v2.0 — 三核融合")
        print("=" * 60)
        print(f"需求: {requirement}")
        print(f"语言: {language}")
        print()

        # 规划
        steps = self.planner.plan(requirement)
        print("[规划] " + " -> ".join(s["desc"] for s in steps))
        print()

        # 生成代码
        print("[生成代码]")
        code = self._generate(requirement, language)
        print(f"  生成了 {len(code.splitlines())} 行")
        print()

        # 运行 + 自动修复
        print("[运行 + 自动修复]")
        current_code = code
        fixes = []
        for rnd in range(1, MAX_FIX_ROUNDS + 1):
            print(f"  --- 第 {rnd} 轮 ---")
            if language == "python":
                result = self.executor.run_python(current_code, project_dir)
            else:
                result = self.executor.run_node(current_code, project_dir)
            if result["success"]:
                print(f"  成功! (第{rnd}轮)")
                break
            else:
                err = result["stderr"]
                print(f"  失败: {err[:100]}")
                new_code, desc, fixed = self.fixer.fix(current_code, err, language)
                if fixed:
                    print(f"  修复: {desc}")
                    fixes.append({"round": rnd, "fix": desc})
                    current_code = new_code
                else:
                    print(f"  无法自动修复: {desc}")
                    fixes.append({"round": rnd, "fix": "无法修复: " + desc})
                    # 查记忆
                    for p in ["NameError","TypeError","SyntaxError","ModuleNotFoundError","IndentationError","KeyError","IndexError","FileNotFoundError","ZeroDivisionError","AttributeError"]:
                        if p in err:
                            mem_fix = self.memory.find_fix(p)
                            if mem_fix: print(f"  记忆提示: {mem_fix}")
                            break
                    if rnd == MAX_FIX_ROUNDS: print(f"  已达最大轮数")
        else:
            if language == "python":
                result = self.executor.run_python(current_code, project_dir)
            else:
                result = self.executor.run_node(current_code, project_dir)

        # 反思
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
            print("任务完成!")
            print(f"轮数: {rnd}")
            if result["stdout"]: print(f"输出:\n{result['stdout'][:300]}")
        else:
            print("任务失败")
            print(f"尝试了 {rnd} 轮")
            print(f"错误: {result['stderr'][:200]}")
        print("=" * 60)

        report = {"success": success, "requirement": requirement, "language": language, "rounds": rnd, "fixes": fixes, "output": result.get("stdout", ""), "error": result.get("stderr", "") if not success else None, "code": current_code}
        self.history.append({"time": datetime.now().isoformat(), "requirement": requirement, "success": success})
        return report

    def _generate(self, req, lang):
        if lang != "python": return f"// TODO: {req}"
        req_l = req.lower()
        if any(k in req_l for k in ["数据","分析","analyze","data"]):
            return self._data_analysis(req)
        elif any(k in req_l for k in ["计算","数学","math"]):
            return self._math_calc(req)
        elif any(k in req_l for k in ["api","服务器","server","接口"]):
            return self._api_server(req)
        elif any(k in req_l for k in ["文件","整理","organize"]):
            return self._file_organizer(req)
        elif any(k in req_l for k in ["网页","爬","scrape","crawl"]):
            return self._web_scraper(req)
        elif any(k in req_l for k in ["图片","image"]):
            return self._image_proc(req)
        elif any(k in req_l for k in ["自动化","定时","auto"]):
            return self._auto_script(req)
        elif any(k in req_l for k in ["爬虫","spider","bot"]):
            return self._web_bot(req)
        elif any(k in req_l for k in ["游戏","game"]):
            return self._game(req)
        else:
            return f'"""\n{req}\nGhost Agent v2.0\n"""\ndef main():\n    print("Hello from Ghost Agent!")\n\nif __name__ == "__main__":\n    main()\n'

    def _data_analysis(self, req):
        return '"""\n' + req + '\n"""\nfrom collections import Counter\nimport math\n\ndef analyze(data):\n    if not data: return {"error": "空数据"}\n    r = {"总数": len(data)}\n    if all(isinstance(x, (int, float)) for x in data):\n        s = sorted(data); n = len(data); avg = sum(data)/n\n        r.update({"最小值": min(data), "最大值": max(data), "总和": sum(data), "平均值": avg, "中位数": s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2, "标准差": math.sqrt(sum((x-avg)**2 for x in data)/n)})\n    if all(isinstance(x, str) for x in data):\n        lens = [len(x) for x in data]\n        r.update({"最短": min(lens), "最长": max(lens), "平均长度": sum(lens)/len(lens), "最常见": Counter(data).most_common(5)})\n    return r\n\nif __name__ == "__main__":\n    nums = [23,45,67,12,89,34,56,78,91,15,62,37]\n    for k,v in analyze(nums).items():\n        print(f"  {k}: {v}")\n'

    def _math_calc(self, req):
        return '"""\n' + req + '\n"""\nimport math\nclass C:\n    add=lambda a,b:a+b; sub=lambda a,b:a-b; mul=lambda a,b:a*b; div=lambda a,b:a/b if b else float("inf")\n    power=lambda a,b:a**b; sqrt=lambda a:math.sqrt(a) if a>=0 else None\n    fact=lambda n:math.factorial(n) if n>=0 else None\n    @staticmethod\n    def fib(n):\n        if n<=0: return []\n        f=[0,1]\n        for i in range(2,n): f.append(f[-1]+f[-2])\n        return f if n>1 else [0]\n    is_prime=lambda n:False if n<2 else all(n%i for i in range(2,int(math.sqrt(n))+1))\n    gcd=math.gcd; lcm=lambda a,b:abs(a*b)//math.gcd(a,b)\n\nif __name__ == "__main__":\n    c=C()\n    print(f"2+3={c.add(2,3)} 10-4={c.sub(10,4)} 6*7={c.mul(6,7)}")\n    print(f"2^10={c.power(2,10)} sqrt(144)={c.sqrt(144)} 10!={c.fact(10)}")\n    print(f"fib(15)={c.fib(17)} is_prime(17)={c.is_prime(17)}")\n    print(f"gcd(12,18)={c.gcd(12,18)} lcm(12,18)={c.lcm(12,18)}")\n'

    def _api_server(self, req):
        return '"""\n' + req + '\n"""\nimport json\nfrom http.server import HTTPServer, BaseHTTPRequestHandler\nfrom datetime import datetime\n\nclass H(BaseHTTPRequestHandler):\n    routes={}\n    @classmethod\n    def route(cls,p):\n        def d(fn): cls.routes[p]=fn; return fn\n        return d\n    def do_GET(self):\n        from urllib.parse import urlparse\n        p=urlparse(self.path)\n        fn=H.routes.get(p.path,lambda s,x:{"error":"404"})\n        self._j(fn(self,p))\n    def _j(self,data,st=200):\n        self.send_response(st)\n        self.send_header("Content-Type","application/json;charset=utf-8")\n        self.end_headers()\n        self.wfile.write(json.dumps(data,ensure_ascii=False).encode())\n    def log_message(self,*a): pass\n\n@H.route("/")\ndef home(h,p): return {"msg":"Ghost Agent API","time":datetime.now().isoformat()}\n@H.route("/health")\ndef health(h,p): return {"status":"ok"}\n@H.route("/time")\ndef time(h,p): return {"time":datetime.now().isoformat()}\n\nif __name__ == "__main__":\n    s=HTTPServer(("localhost",8080),H)\n    print("API: http://localhost:8080")\n    s.serve_forever()\n'

    def _file_organizer(self, req):
        return '"""\n' + req + '\n"""\nfrom pathlib import Path\nimport shutil\nfrom collections import defaultdict\n\ndef organize(d):\n    p=Path(d)\n    if not p.exists(): print(f"目录不存在: {d}"); return\n    tm={".py":"Python",".js":"JS",".html":"HTML",".css":"CSS",".json":"JSON",".md":"Markdown",".txt":"Text",".jpg":"Images",".png":"Images",".gif":"Images",".mp4":"Videos",".mp3":"Audio",".zip":"Archives",".pdf":"PDF",".doc":"Documents",".xls":"Sheets",".exe":"Executables"}\n    stats=defaultdict(list)\n    for f in p.iterdir():\n        if f.is_file():\n            folder=tm.get(f.suffix.lower(),"Others")\n            t=p/folder; t.mkdir(exist_ok=True)\n            shutil.move(str(f),str(t/f.name))\n            stats[folder].append(f.name)\n    total=sum(len(v) for v in stats.values())\n    print(f"整理了 {total} 个文件")\n    for folder,files in sorted(stats.items()):\n        print(f"  [{folder}]: {len(files)} 个")\n\nif __name__ == "__main__":\n    import sys\n    organize(sys.argv[1] if len(sys.argv)>1 else ".")\n'

    def _web_scraper(self, req):
        return '"""\n' + req + '\n"""\nimport urllib.request, re\n\ndef fetch(url):\n    req=urllib.request.Request(url,headers={"User-Agent":"GhostAgent/2.0"})\n    with urllib.request.urlopen(req,timeout=10) as r:\n        return r.read().decode("utf-8",errors="ignore")\n\ndef links(html): return re.findall(r\'href="(https?://[^"]+)\',html)\ndef text(html):\n    t=re.sub(r"<[^>]+>","",html)\n    return re.sub(r"\\s+"," ",t).strip()\n\nif __name__ == "__main__":\n    html=fetch("https://example.com")\n    print(f"链接: {len(links(html))}")\n    print(f"文本: {text(html)[:200]}")\n'

    def _image_proc(self, req):
        return '"""\n' + req + '\n需要: pip install Pillow\n"""\nfrom pathlib import Path\n\ndef info(fp):\n    try:\n        from PIL import Image\n        img=Image.open(fp)\n        return {"格式":img.format,"尺寸":img.size,"模式":img.mode}\n    except ImportError: return {"error":"pip install Pillow"}\n    except Exception as e: return {"error":str(e)}\n\nif __name__ == "__main__":\n    import sys\n    if len(sys.argv)>1:\n        for k,v in info(sys.argv[1]).items(): print(f"  {k}: {v}")\n'

    def _auto_script(self, req):
        return '"""\n' + req + '\n"""\nimport time\nfrom datetime import datetime\n\ndef task(): print(f"[{datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}] 执行!")\n\ndef run_loop(interval=60):\n    print(f"定时执行 (每{interval}秒)")\n    try:\n        while True: task(); time.sleep(interval)\n    except KeyboardInterrupt: print("\\n停止")\n\nif __name__ == "__main__":\n    import sys\n    run_loop() if "--loop" in sys.argv else task()\n'

    def _web_bot(self, req):
        return '"""\n' + req + '\n"""\nimport urllib.request, re, time\n\nclass WebBot:\n    def __init__(self): self.visited=set()\n    def fetch(self,url):\n        req=urllib.request.Request(url,headers={"User-Agent":"GhostBot/2.0"})\n        with urllib.request.urlopen(req,timeout=10) as r: return r.read().decode("utf-8",errors="ignore")\n    def crawl(self,start,max_p=5):\n        q=[start]\n        while q and len(self.visited)<max_p:\n            url=q.pop(0)\n            if url in self.visited: continue\n            try:\n                html=self.fetch(url); self.visited.add(url)\n                print(f"爬取: {url} ({len(html)} 字节)")\n                q.extend(re.findall(r\'href="(https?://[^"]+)\',html)[:3])\n                time.sleep(1)\n            except Exception as e: print(f"  错误: {e}")\n        print(f"完成! {len(self.visited)} 页")\n\nif __name__ == "__main__":\n    WebBot().crawl("https://example.com")\n'

    def _game(self, req):
        return '"""\n' + req + '\n"""\nimport random\n\ndef guess():\n    s=random.randint(1,100); n=0\n    print("猜数字 (1-100)")\n    while True:\n        try:\n            g=int(input("你的猜测: ")); n+=1\n            if g<s: print("太小了!")\n            elif g>s: print("太大了!")\n            else: print(f"恭喜! {n}次猜中!"); break\n        except: print("请输入数字!")\n\nif __name__ == "__main__": guess()\n'

if __name__ == "__main__":
    import sys
    agent = GhostAgent()
    if len(sys.argv) > 1:
        agent.do(" ".join(sys.argv[1:]))
    else:
        print("用法: python ghost_v2.py <需求描述>")
        print()
        agent.do("写一个数据分析脚本")
