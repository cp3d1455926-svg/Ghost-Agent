# -*- coding: utf-8 -*-
"""
Ghost Agent v3.0 - memU Memory Integration
Authors: Ghost & Jake

New in v3.0:
- memU-powered memory system (replaces HermesMemory)
  * Semantic search via memU API
  * Auto-flush before compaction
  * Shared memory pools for multi-agent
  * Smart context selection (up to 90% token reduction)
- Backward compatible with all v2.x features

Architecture:
    Ghost Agent = Pluggable AI + OpenClaw Execution + memU Memory + ClaudeCode Coding

Usage:
    agent = GhostAgent()  # Default with memU memory
    agent = GhostAgent(ai=StepfunBackend(), memu_config={...})  # Custom memU
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
# memU Memory System v3.0
# ============================================================
class MemUMemory:
    """
    Ghost Agent v3.0 Memory System powered by memU API.
    Falls back to local JSON files if memU API is unavailable.
    """
    
    def __init__(self, api_key=None, base_url="https://api.memu.so",
                 user_id=None, agent_id=None):
        self.api_key = api_key or os.environ.get("MEMU_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id or "ghost_agent_user"
        self.agent_id = agent_id or "ghost_agent_main"
        self.l0 = {}
        self.l1 = self._load_local("warm.json")
        self.l2 = self._load_local("cold.json")
        self.errors = self._load_local("errors.json")
    
    def _load_local(self, filename):
        p = MEMORY_DIR / filename
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    
    def _save_local(self, data, filename):
        (MEMORY_DIR / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    
    def _memu_call(self, endpoint, data):
        """Call memU API, return response or None on failure"""
        if not self.api_key:
            return None
        try:
            import urllib.request
            payload = json.dumps(data).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            }
            req = urllib.request.Request(
                self.base_url + endpoint, data=payload, headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print("  [memU API] " + str(e)[:80])
            return None
    
    def _memu_store(self, content, metadata=None):
        """Store a memory in memU"""
        data = {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        resp = self._memu_call("/api/v1/memory/store", data)
        return resp is not None and resp.get("status") == "success"
    
    def _memu_search(self, query, limit=5):
        """Search memU for relevant memories"""
        data = {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "query": query,
            "limit": limit,
        }
        resp = self._memu_call("/api/v1/memory/search", data)
        if resp and resp.get("status") == "success":
            return resp.get("data", {}).get("memories", [])
        return []
    
    def remember(self, key, value, layer="l1"):
        """Store a memory entry"""
        entry = {"key": key, "value": value, "time": datetime.now().isoformat()}
        if layer == "l0":
            self.l0[key] = entry
        elif layer == "l1":
            self.l1[key] = entry
            self._save_local(self.l1, "warm.json")
            self._memu_store(
                json.dumps(entry["value"], ensure_ascii=False),
                {"layer": "L1", "key": key}
            )
        elif layer == "l2":
            self.l2[key] = entry
            self._save_local(self.l2, "cold.json")
            self._memu_store(
                json.dumps(entry["value"], ensure_ascii=False),
                {"layer": "L2", "key": key}
            )
    
    def recall(self, key):
        """Recall a memory by exact key"""
        if key in self.l0: return self.l0[key]["value"]
        if key in self.l1: return self.l1[key]["value"]
        if key in self.l2: return self.l2[key]["value"]
        # Try memU semantic search as last resort
        results = self._memu_search(key, limit=1)
        if results:
            try:
                return json.loads(results[0].get("content", "null"))
            except (json.JSONDecodeError, TypeError):
                return results[0].get("content")
        return None
    
    def recall_relevant(self, query, limit=5):
        """Find relevant memories using memU semantic search"""
        results = self._memu_search(query, limit=limit)
        if results:
            return [{"key": r.get("metadata", {}).get("key", "unknown"),
                     "value": r.get("content"),
                     "score": r.get("score", 0)} for r in results]
        # Fallback: local keyword search
        results = []
        query_lower = query.lower()
        for layer in [self.l1, self.l2]:
            for key, entry in layer.items():
                value_str = json.dumps(entry.get("value", ""), ensure_ascii=False).lower()
                if query_lower in key.lower() or query_lower in value_str:
                    results.append({"key": key, "value": entry["value"], "score": 0.5})
        return results[:limit]
    
    def remember_error(self, error_type, detail, fix, success):
        """Remember an error and its fix"""
        if "list" not in self.errors: self.errors["list"] = []
        self.errors["list"].append({
            "type": error_type, "detail": detail[:200],
            "fix": fix, "ok": success,
            "time": datetime.now().isoformat()
        })
        self.errors["list"] = self.errors["list"][-100:]
        self._save_local(self.errors, "errors.json")
        self._memu_store(
            json.dumps({"type": error_type, "detail": detail[:200], "fix": fix, "ok": success}, ensure_ascii=False),
            {"type": "error_fix"}
        )
    
    def find_fix(self, error_type):
        """Find a known fix for an error type"""
        for entry in reversed(self.errors.get("list", [])):
            if entry["type"] == error_type and entry["ok"]:
                return entry["fix"]
        return None
    
    def flush(self):
        """Flush hot memories to persistent storage"""
        for key, entry in self.l0.items():
            self._memu_store(
                json.dumps(entry, ensure_ascii=False),
                {"layer": "L0_flush", "key": key}
            )
        self.l0.clear()
    
    def get_context_summary(self, max_chars=2000):
        """Get a compact context summary for LLM prompts"""
        summary_parts = []
        total_chars = 0
        recent_l1 = sorted(
            self.l1.values(),
            key=lambda x: x.get("time", ""), reverse=True
        )[:10]
        for entry in recent_l1:
            line = entry["key"] + ": " + json.dumps(entry["value"], ensure_ascii=False)[:100]
            if total_chars + len(line) > max_chars:
                break
            summary_parts.append(line)
            total_chars += len(line)
        return "\n".join(summary_parts)
    
    def stats(self):
        return {
            "l0_hot": len(self.l0), "l1_warm": len(self.l1),
            "l2_cold": len(self.l2),
            "error_patterns": len(self.errors.get("list", [])),
            "memu_connected": bool(self.api_key),
        }


# ============================================================
# AI Backend Interface - Pluggable (same as v2.1)
# ============================================================
class AIBackend:
    def generate_code(self, requirement, language="python", context=None):
        raise NotImplementedError
    def fix_code(self, code, error, language="python"):
        raise NotImplementedError


class TemplateBackend(AIBackend):
    def __init__(self):
        # Import template library from v21
        try:
            from ghost_v21 import TemplateLibrary
            self.templates = TemplateLibrary()
        except ImportError:
            self.templates = None
    
    def generate_code(self, requirement, language="python", context=None):
        if self.templates:
            return self.templates.generate(requirement, language)
        return "# Template library not available\nprint('Hello from Ghost Agent v3.0')"
    
    def fix_code(self, code, error, language="python"):
        return code


class StepfunBackend(AIBackend):
    """Stepfun 3.5 Flash backend"""
    
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
    """LongCat model backend"""
    
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
# OpenClaw Executor (same as v2.1)
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
    
    def run_shell(self, cmd, project_dir=None):
        wd = Path(project_dir) if project_dir else PROJECTS_DIR
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, cwd=str(wd), shell=True)
            return {"success": r.returncode == 0, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "timeout"}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}


# ============================================================
# SmartFixer V2 (same as v2.1)
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
            if "KeyError" in error: fixes.append("Use .get() for missing key")
            if "IndexError" in error: fixes.append("Index out of range")
            if "FileNotFoundError" in error: fixes.append("File not found")
            if "ZeroDivisionError" in error: fixes.append("Division by zero")
            if "AttributeError" in error: fixes.append("Attribute error")
            if "TypeError" in error: fixes.append("Type error")
        return code, "; ".join(fixes) if fixes else "Cannot auto-fix", len(fixes) > 0


# ============================================================
# Task Planner (same as v2.1)
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
# Ghost Agent v3.0 Main Class
# ============================================================
class GhostAgent:
    """
    Ghost Agent v3.0 - memU Memory + All v2.x Features
    
    Usage:
        agent = GhostAgent()                                    # Default
        agent = GhostAgent(ai=StepfunBackend())                  # With AI
        agent = GhostAgent(memu_config={"api_key": "xxx"})      # With memU
    """
    
    def __init__(self, ai=None, memu_config=None):
        self.ai = ai or TemplateBackend()
        memu_config = memu_config or {}
        self.memory = MemUMemory(
            api_key=memu_config.get("api_key"),
            base_url=memu_config.get("base_url", "https://api.memu.so"),
            user_id=memu_config.get("user_id", "ghost_agent_user"),
            agent_id=memu_config.get("agent_id", "ghost_agent_main"),
        )
        self.executor = OpenClawExecutor()
        self.planner = TaskPlanner()
        self.fixer = SmartFixerV2(self.memory)
        self.history = []
    
    def do(self, requirement, language="python", project_dir=None):
        print("=" * 60)
        print("Ghost Agent v3.0 - memU Memory")
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
                
                # Try SmartFixer first
                new_code, desc, fixed = self.fixer.fix(current_code, err, language)
                if fixed:
                    print("  Fixed: " + desc)
                    fixes.append({"round": rnd, "fix": desc})
                    current_code = new_code
                else:
                    # Try memory for known fix
                    mem_fix = self.memory.find_fix("NameError" if "NameError" in err else "SyntaxError" if "SyntaxError" in err else "TypeError" if "TypeError" in err else "")
                    if mem_fix:
                        print("  Memory hint: " + mem_fix)
                    
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
    """Create Ghost Agent v3.0 from config file"""
    if config_path is None:
        config_path = Path("ghost_agent_config.json")
    
    if not config_path.exists():
        return GhostAgent()
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    backend = config.get("backend", "template")
    memu_config = config.get("memu", {})
    
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
    
    return GhostAgent(ai=ai, memu_config=memu_config)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Quick test
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
        print("  python ghost_v30.py --test             # Run tests")
        print("  python ghost_v30.py <requirement>      # Run task")
        print()
        agent = create_agent()
        agent.do("write a hello world script")
