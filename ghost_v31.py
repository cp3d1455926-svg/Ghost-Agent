# -*- coding: utf-8 -*-
"""
Ghost Agent v3.1 - mem0 Memory Integration
Authors: Ghost & Jake

New in v3.1:
- Replaced MemUMemory with mem0 (open-source memory framework)
  * Semantic search via mem0 (no API key needed for local mode)
  * BM25 keyword + entity extraction + semantic fusion
  * Auto memory extraction from conversations
  * Multi-user support
  * Persistent storage via Qdrant (local)
- Backward compatible with all v2.x features

Usage:
    agent = GhostAgent()                         # Default (mem0 local)
    agent = GhostAgent(ai=StepfunBackend())      # With AI backend
"""
import subprocess, os, sys, json, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
PROJECTS_DIR = WORKSPACE / "projects"
LOGS_DIR = WORKSPACE / "logs"
MEMORY_DIR = WORKSPACE / "memory_v3"
MAX_FIX_ROUNDS = 5
TIMEOUT = 30

for d in [PROJECTS_DIR, LOGS_DIR, MEMORY_DIR]:
    d.mkdir(exist_ok=True)


# ============================================================
# mem0 Memory Adapter
# ============================================================
class Mem0Memory:
    """
    Ghost Agent v3.1 Memory System powered by mem0.
    
    Features:
    - Semantic search (vector + BM25 + entity fusion)
    - Auto memory extraction from conversations
    - Local storage via Qdrant (no cloud needed)
    - Multi-user / multi-agent support
    - Persistent across sessions
    
    Falls back to local JSON if mem0 is not installed.
    """
    
    def __init__(self, user_id="ghost_agent", agent_id="main", api_key=None):
        self.user_id = user_id
        self.agent_id = agent_id
        self._mem0_available = False
        self._fallback = {}
        
        # Read API key from parameter, then environment variable
        self.api_key = api_key or os.environ.get("MEM0_API_KEY", "")
        
        try:
            from mem0 import Memory
            
            if self.api_key:
                # Cloud mode: use mem0 platform API (handles vector storage + LLM + embeddings)
                self.memory = Memory(api_key=self.api_key)
                self._mem0_available = True
                print("[mem0] Cloud mode initialized (API key: " + self.api_key[:8] + "...)")
            else:
                # Local mode: try local Qdrant + Ollama
                try:
                    self.memory = Memory()
                    self._mem0_available = True
                    print("[mem0] Local mode initialized")
                except Exception as e:
                    print("[mem0] Local init failed: " + str(e)[:80])
                    print("[mem0] Set MEM0_API_KEY env var for cloud mode")
            
        except ImportError:
            print("[mem0] Not installed, using JSON fallback. Run: pip install mem0ai")
        except Exception as e:
            print("[mem0] Init failed: " + str(e)[:80] + ", using JSON fallback")
    
    def remember(self, key, value, layer="l1"):
        """Store a memory entry"""
        entry = json.dumps({"key": key, "value": value}, ensure_ascii=False)
        
        if self._mem0_available:
            try:
                self.memory.add(
                    [{"role": "user", "content": entry}],
                    user_id=self.user_id,
                    metadata={"layer": layer, "key": key}
                )
                return
            except Exception as e:
                pass  # Fall through to JSON
        
        # JSON fallback
        if layer not in self._fallback:
            self._fallback[layer] = {}
        self._fallback[layer][key] = value
        self._save_fallback()
    
    def recall(self, key):
        """Recall a memory by exact key"""
        if self._mem0_available:
            try:
                results = self.memory.search(
                    query=key, user_id=self.user_id, limit=1
                )
                if results.get("results"):
                    content = results["results"][0].get("memory", "")
                    try:
                        return json.loads(content).get("value", content)
                    except:
                        return content
            except:
                pass
        
        # JSON fallback
        for layer in self._fallback.values():
            if key in layer:
                return layer[key]
        return None
    
    def recall_relevant(self, query, limit=5):
        """Find relevant memories using mem0 semantic search"""
        if self._mem0_available:
            try:
                results = self.memory.search(
                    query=query, user_id=self.user_id, limit=limit
                )
                if results.get("results"):
                    return [
                        {
                            "key": r.get("metadata", {}).get("key", "unknown"),
                            "value": r.get("memory", ""),
                            "score": r.get("score", 0),
                        }
                        for r in results["results"]
                    ]
            except:
                pass
        
        # JSON fallback: keyword search
        results = []
        query_lower = query.lower()
        for layer_name, layer in self._fallback.items():
            for key, value in layer.items():
                value_str = json.dumps(value, ensure_ascii=False).lower()
                if query_lower in key.lower() or query_lower in value_str:
                    results.append({"key": key, "value": value, "score": 0.5})
        return results[:limit]
    
    def remember_error(self, error_type, detail, fix, success):
        """Remember an error and its fix"""
        entry = json.dumps({
            "type": error_type, "detail": detail[:200],
            "fix": fix, "ok": success
        }, ensure_ascii=False)
        
        if self._mem0_available:
            try:
                self.memory.add(
                    [{"role": "user", "content": entry}],
                    user_id=self.user_id,
                    metadata={"type": "error_fix", "error_type": error_type}
                )
                return
            except:
                pass
        
        # JSON fallback
        if "errors" not in self._fallback:
            self._fallback["errors"] = []
        self._fallback["errors"].append({
            "type": error_type, "detail": detail[:200],
            "fix": fix, "ok": success, "time": datetime.now().isoformat()
        })
        self._fallback["errors"] = self._fallback["errors"][-100:]
        self._save_fallback()
    
    def find_fix(self, error_type):
        """Find a known fix for an error type"""
        if self._mem0_available:
            try:
                results = self.memory.search(
                    query="error fix " + error_type,
                    user_id=self.user_id, limit=3
                )
                for r in results.get("results", []):
                    try:
                        data = json.loads(r.get("memory", "{}"))
                        if data.get("ok"):
                            return data.get("fix", "")
                    except:
                        pass
            except:
                pass
        
        # JSON fallback
        for entry in reversed(self._fallback.get("errors", [])):
            if entry["type"] == error_type and entry["ok"]:
                return entry["fix"]
        return None
    
    def get_context_summary(self, max_chars=2000):
        """Get a compact context summary for LLM prompts"""
        if self._mem0_available:
            try:
                results = self.memory.get_all(user_id=self.user_id, limit=20)
                if results.get("results"):
                    parts = []
                    total = 0
                    for r in results["results"]:
                        line = r.get("memory", "")[:150]
                        if total + len(line) > max_chars:
                            break
                        parts.append(line)
                        total += len(line)
                    return "\n".join(parts)
            except:
                pass
        
        # JSON fallback
        parts = []
        total = 0
        for layer in self._fallback.values():
            if isinstance(layer, dict):
                for key, value in list(layer.items())[:10]:
                    line = key + ": " + json.dumps(value, ensure_ascii=False)[:100]
                    if total + len(line) > max_chars:
                        break
                    parts.append(line)
                    total += len(line)
        return "\n".join(parts)
    
    def flush(self):
        """Flush - mem0 auto-persists, no action needed"""
        pass
    
    def stats(self):
        """Return memory statistics"""
        if self._mem0_available:
            try:
                results = self.memory.get_all(user_id=self.user_id, limit=1000)
                count = len(results.get("results", []))
                return {"total": count, "backend": "mem0", "user_id": self.user_id}
            except:
                pass
        
        total = sum(len(v) if isinstance(v, dict) else 0 for v in self._fallback.values())
        return {"total": total, "backend": "json_fallback"}
    
    def _save_fallback(self):
        """Save fallback JSON"""
        (MEMORY_DIR / "fallback.json").write_text(
            json.dumps(self._fallback, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# ============================================================
# AI Backend Interface (same as v3.0)
# ============================================================
class AIBackend:
    def generate_code(self, requirement, language="python", context=None):
        raise NotImplementedError
    def fix_code(self, code, error, language="python"):
        raise NotImplementedError


class TemplateBackend(AIBackend):
    def __init__(self):
        try:
            from ghost_v21 import TemplateLibrary
            self.templates = TemplateLibrary()
        except ImportError:
            self.templates = None
    
    def generate_code(self, requirement, language="python", context=None):
        if self.templates:
            return self.templates.generate(requirement, language)
        return "# Template library not available\nprint('Hello from Ghost Agent v3.1')"
    
    def fix_code(self, code, error, language="python"):
        return code


class StepfunBackend(AIBackend):
    def __init__(self, api_key=None, model="step-3.5-flash", base_url=None):
        self.model = model
        self.api_key = api_key or os.environ.get("STEPFUN_API_KEY", "")
        self.base_url = base_url or "https://api.stepfun.com/v1"
        if not self.api_key:
            self._load_from_openclaw_config()
    
    def _load_from_openclaw_config(self):
        config_paths = [
            Path(os.path.expanduser("~/.openclaw/agents/main/agent/models.json")),
            Path("C:/Users/shenz/.openclaw/agents/main/agent/models.json"),
        ]
        for p in config_paths:
            if p.exists():
                try:
                    config = json.loads(p.read_text(encoding="utf-8"))
                    providers = config.get("providers", {})
                    if "stepfun" in providers:
                        self.api_key = providers["stepfun"].get("apiKey", "")
                        self.base_url = providers["stepfun"].get("baseUrl", self.base_url)
                        for m in providers["stepfun"].get("models", []):
                            if "3.5" in m.get("id", "") and "flash" in m.get("id", ""):
                                self.model = m["id"]
                                break
                except Exception:
                    pass
    
    def generate_code(self, requirement, language="python", context=None):
        prompt = "你是一个专业的 " + language + " 程序员。根据需求生成完整可运行的代码。\n需求: " + requirement + "\n要求：1. 代码必须包含 if __name__ == \"__main__\" 入口 2. 必须有 print 输出 3. 只返回代码，不要解释:"
        return self._call(prompt)
    
    def fix_code(self, code, error, language="python"):
        prompt = "修复 " + language + " 代码错误:\n代码:\n" + code + "\n错误:\n" + error + "\n只返回修复后代码:"
        return self._call(prompt)
    
    def _call(self, prompt):
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2, "max_tokens": 4000,
            }).encode()
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = "Bearer " + self.api_key
            req = urllib.request.Request(self.base_url + "/chat/completions", data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                content = result["choices"][0]["message"]["content"]
                match = re.search(r"```(?:python|javascript|js)?\s*\n(.*?)```", content, re.DOTALL)
                return match.group(1).strip() if match else content.strip()
        except Exception as e:
            print("[StepfunBackend] Error: " + str(e))
            return "# Generation failed: " + str(e)


class LongCatBackend(StepfunBackend):
    def __init__(self, api_key=None, model="LongCat-2.0-Preview", base_url=None):
        super().__init__(api_key=api_key, model=model, base_url=base_url or "https://api.longcat.chat/openai/v1")
    
    def generate_code(self, requirement, language="python", context=None):
        prompt = "You are a professional " + language + " programmer. Generate complete, runnable code.\nRequirement: " + requirement + "\nReturn code only, no explanation:"
        return self._call(prompt)
    
    def fix_code(self, code, error, language="python"):
        prompt = "Fix the " + language + " code error:\nCode:\n" + code + "\nError:\n" + error + "\nReturn fixed code only:"
        return self._call(prompt)


class OpenAIBackend(LongCatBackend):
    def __init__(self, api_key, model="gpt-4", base_url="https://api.openai.com/v1"):
        super().__init__(api_key=api_key, model=model, base_url=base_url)


class OllamaBackend(AIBackend):
    def __init__(self, model="codellama", host="http://localhost:11434"):
        self.model = model
        self.host = host
    
    def generate_code(self, requirement, language="python", context=None):
        prompt = "[INST] Generate code. Requirement: " + requirement + " [/INST]"
        return self._call(prompt)
    
    def fix_code(self, code, error, language="python"):
        prompt = "[INST] Fix error: " + error + " in code: " + code + " [/INST]"
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
            r = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, cwd=str(wd), env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}
    
    def run_node(self, code, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        wd.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        f = wd / ("_run_" + ts + ".js")
        f.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, cwd=str(wd))
            return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}


# ============================================================
# SmartFixer V2
# ============================================================
class SmartFixerV2:
    def __init__(self, memory):
        self.memory = memory
    
    def fix(self, code, error, lang="python"):
        fixes = []
        if lang == "python":
            m = re.search(r"NameError: name '(\w+)' is not defined\. Did you mean: '(\w+)'", error)
            if m:
                code = code.replace(m.group(1), m.group(2))
                fixes.append("Spelling: " + m.group(1) + " -> " + m.group(2))
            m = re.search(r"No module named '(\w+)'", error)
            if m:
                fixes.append("pip install " + m.group(1))
            m = re.search(r"SyntaxError.*line (\d+)", error)
            if m:
                ln = int(m.group(1))
                lines = code.split("\n")
                if 0 < ln <= len(lines):
                    for kw in ["for", "if", "elif", "else", "def", "class", "while", "try", "except", "with"]:
                        if lines[ln - 1].strip().startswith(kw) and not lines[ln - 1].rstrip().endswith(":"):
                            lines[ln - 1] = lines[ln - 1].rstrip() + ":"
                            code = "\n".join(lines)
                            fixes.append("L" + str(ln) + ": add colon")
                            break
            if "expected an indented block" in error:
                m = re.search(r"line (\d+)", error)
                if m:
                    ln = int(m.group(1))
                    lines = code.split("\n")
                    if 0 < ln <= len(lines):
                        lines[ln - 1] = "    " + lines[ln - 1].lstrip()
                        code = "\n".join(lines)
                        fixes.append("L" + str(ln) + ": add indent")
            if "KeyError" in error: fixes.append("Use .get()")
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
        if any(k in req for k in ["create", "new", "write", "generate", "build", "make"]):
            return [{"action": "generate", "desc": "Generate code"}, {"action": "run", "desc": "Run test"}, {"action": "fix", "desc": "Auto-fix"}]
        if any(k in req for k in ["modify", "change", "fix", "update"]):
            return [{"action": "read", "desc": "Read code"}, {"action": "modify", "desc": "Modify"}, {"action": "test", "desc": "Test"}]
        if any(k in req for k in ["organize", "clean", "sort"]):
            return [{"action": "scan", "desc": "Scan directory"}, {"action": "execute", "desc": "Execute"}]
        return [{"action": "generate", "desc": "Generate code"}, {"action": "run", "desc": "Run test"}]


# ============================================================
# Ghost Agent v3.1 Main Class
# ============================================================
class GhostAgent:
    """
    Ghost Agent v3.1 - mem0 Memory + All v2.x Features
    
    Usage:
        agent = GhostAgent()                                    # Default
        agent = GhostAgent(ai=StepfunBackend())                  # With AI
    """
    
    def __init__(self, ai=None, user_id="ghost_agent"):
        self.ai = ai or TemplateBackend()
        self.memory = Mem0Memory(user_id=user_id)
        self.executor = OpenClawExecutor()
        self.planner = TaskPlanner()
        self.fixer = SmartFixerV2(self.memory)
        self.history = []
    
    def do(self, requirement, language="python", project_dir=None):
        print("=" * 60)
        print("Ghost Agent v3.1 - mem0 Memory")
        print("AI Backend: " + self.ai.__class__.__name__)
        print("Memory: " + str(self.memory.stats()))
        print("=" * 60)
        print("Requirement: " + requirement)
        print("Language: " + language)
        print()
        
        # Plan
        steps = self.planner.plan(requirement)
        print("[Plan] " + " -> ".join(s["desc"] for s in steps))
        print()
        
        # Check memory for relevant past experience
        relevant = self.memory.recall_relevant(requirement, limit=3)
        context = None
        if relevant:
            print("[Memory] Found " + str(len(relevant)) + " relevant memories")
            for r in relevant:
                print("  - " + r["key"] + " (score: " + str(r["score"])[:4] + ")")
            context = {"memories": relevant}
        
        # Generate code
        print("[Generate]")
        if project_dir and Path(project_dir).exists():
            r = self.executor.run_shell("dir /b " + project_dir)
            if r["success"]:
                if context is None: context = {}
                context["files"] = r["stdout"].split("\n")[:10]
        
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
                
                new_code, desc, fixed = self.fixer.fix(current_code, err, language)
                if fixed:
                    print("  Fixed: " + desc)
                    fixes.append({"round": rnd, "fix": desc})
                    current_code = new_code
                else:
                    mem_fix = self.memory.find_fix("NameError" if "NameError" in err else "SyntaxError" if "SyntaxError" in err else "TypeError" if "TypeError" in err else "")
                    if mem_fix:
                        print("  Memory hint: " + mem_fix)
                    
                    print("  SmartFixer cannot fix, trying AI...")
                    ai_fixed = self.ai.fix_code(current_code, err, language)
                    if ai_fixed and ai_fixed != current_code:
                        print("  AI fix applied")
                        fixes.append({"round": rnd, "fix": "AI auto-fix"})
                        current_code = ai_fixed
                    else:
                        print("  Cannot fix: " + desc)
                        fixes.append({"round": rnd, "fix": "Cannot fix: " + desc})
                        if rnd == MAX_FIX_ROUNDS:
                            print("  Max rounds reached")
        else:
            result = self.executor.run_python(current_code, project_dir) if language == "python" else self.executor.run_node(current_code, project_dir)
        
        # Reflect + Remember
        success = result["success"]
        if not success:
            etype = "Unknown"
            for p in ["NameError", "TypeError", "SyntaxError", "ModuleNotFoundError", "IndentationError", "KeyError", "IndexError", "FileNotFoundError", "ZeroDivisionError", "AttributeError"]:
                if p in result["stderr"]:
                    etype = p
                    break
            self.memory.remember_error(etype, result["stderr"], str(fixes), success)
        
        self.memory.remember(
            "task:" + requirement[:50],
            {"requirement": requirement, "success": success, "rounds": rnd, "fixes": fixes}
        )
        
        print()
        print("=" * 60)
        if success:
            print("TASK COMPLETE!")
            print("Rounds: " + str(rnd))
            if result["stdout"]:
                print("Output:\n" + result["stdout"][:300])
        else:
            print("TASK FAILED")
            print("Rounds: " + str(rnd))
            print("Error: " + result["stderr"][:200])
        print("=" * 60)
        
        report = {
            "success": success, "requirement": requirement,
            "language": language, "rounds": rnd, "fixes": fixes,
            "output": result.get("stdout", ""),
            "error": result.get("stderr", "") if not success else None,
            "code": current_code,
        }
        self.history.append({
            "time": datetime.now().isoformat(),
            "requirement": requirement, "success": success,
        })
        return report


def create_agent(config_path=None):
    """Create Ghost Agent v3.1 from config file"""
    if config_path is None:
        config_path = Path("ghost_agent_config.json")
    
    if not config_path.exists():
        return GhostAgent()
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    backend = config.get("backend", "template")
    
    ai = None
    if backend == "stepfun":
        ai = StepfunBackend(
            model=config.get("stepfun_model", "step-3.5-flash"),
            base_url=config.get("stepfun_base_url", "") or None,
            api_key=config.get("stepfun_api_key", "") or None,
        )
    elif backend == "longcat":
        ai = LongCatBackend(
            model=config.get("longcat_model", "LongCat-2.0-Preview"),
            base_url=config.get("longcat_base_url", "") or None,
            api_key=config.get("longcat_api_key", "") or None,
        )
    elif backend == "openai":
        ai = OpenAIBackend(
            api_key=config.get("openai_key", ""),
            model=config.get("openai_model", "gpt-4"),
        )
    elif backend == "ollama":
        ai = OllamaBackend(
            model=config.get("ollama_model", "codellama"),
            host=config.get("ollama_host", "http://localhost:11434"),
        )
    
    return GhostAgent(ai=ai)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        agent = create_agent()
        print("\n=== Test 1: Simple task ===")
        agent.do("write a hello world script")
        print("\n=== Test 2: Data analysis ===")
        agent.do("write a data analysis script")
        print("\n=== Memory Stats ===")
        print(agent.memory.stats())
    elif len(sys.argv) > 1:
        agent = create_agent()
        agent.do(" ".join(sys.argv[1:]))
    else:
        print("Usage:")
        print("  python ghost_v31.py --test             # Run tests")
        print("  python ghost_v31.py <requirement>      # Run task")
        print()
        agent = create_agent()
        agent.do("write a hello world script")
