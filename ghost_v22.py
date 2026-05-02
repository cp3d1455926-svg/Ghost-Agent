# -*- coding: utf-8 -*-
"""
Ghost Agent v2.2 - Multi-Agent Collaboration
Author: Ghost & Jake

New in v2.2:
- SubAgent: 子 Agent，可以独立执行任务
- AgentPool: Agent 池，管理多个子 Agent
- TaskSplitter: 把大任务拆分成小任务
- ResultMerger: 合并子 Agent 的结果

Architecture:
    Main Agent (Ghost)
        ├── SubAgent-1 (Coder)   — 写代码
        ├── SubAgent-2 (Tester)  — 测试验证
        └── SubAgent-3 (Reviewer)— 代码审查
"""
import subprocess, os, sys, json, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
PROJECTS_DIR = WORKSPACE / "projects"
MEMORY_DIR = WORKSPACE / "memory_v2"
MAX_FIX_ROUNDS = 5
TIMEOUT = 30

for d in [PROJECTS_DIR, MEMORY_DIR]:
    d.mkdir(exist_ok=True)


# ============================================================
# SubAgent — 子 Agent
# ============================================================
class SubAgent:
    """子 Agent，可以独立执行任务"""
    
    def __init__(self, name, role="coder"):
        self.name = name
        self.role = role  # coder, tester, reviewer
        self.history = []
    
    def execute(self, task, language="python", project_dir=None):
        """执行分配的任务"""
        print("  [" + self.name + "/" + self.role + "] " + task[:60])
        
        # 根据角色执行不同操作
        if self.role == "coder":
            result = self._do_code(task, language, project_dir)
        elif self.role == "tester":
            result = self._do_test(task, language, project_dir)
        elif self.role == "reviewer":
            result = self._do_review(task, project_dir)
        else:
            result = {"success": False, "error": "Unknown role"}
        
        self.history.append({"task": task, "result": result, "time": datetime.now().isoformat()})
        return result
    
    def _do_code(self, task, language, project_dir):
        """生成代码"""
        wd = project_dir or str(PROJECTS_DIR)
        Path(wd).mkdir(exist_ok=True)
        code = self._generate_simple(task, language)
        return {"success": True, "code": code, "action": "generated"}
    
    def _do_test(self, task, language, project_dir):
        """运行测试"""
        wd = project_dir or str(PROJECTS_DIR)
        # 找到最新的代码文件
        files = sorted(Path(wd).glob("_run_*.*"), reverse=True)
        if not files:
            return {"success": False, "error": "No code files found"}
        
        latest = files[0]
        try:
            if latest.suffix == ".py":
                r = subprocess.run(
                    [sys.executable, "-X", "utf8", str(latest)],
                    capture_output=True, text=True, timeout=TIMEOUT,
                    cwd=wd, env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
            else:
                r = subprocess.run(
                    ["node", str(latest)],
                    capture_output=True, text=True, timeout=TIMEOUT, cwd=wd
                )
            return {
                "success": r.returncode == 0,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "action": "tested"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _do_review(self, task, project_dir):
        """代码审查（简单版）"""
        wd = project_dir or str(PROJECTS_DIR)
        files = sorted(Path(wd).glob("_run_*.py"), reverse=True)
        if not files:
            return {"success": False, "error": "No code files found"}
        
        code = files[0].read_text(encoding="utf-8")
        issues = []
        
        # 简单检查
        if "import *" in code:
            issues.append("Avoid import *")
        if "except:" in code:
            issues.append("Avoid bare except")
        if "TODO" in code or "FIXME" in code:
            issues.append("Has TODO/FIXME")
        if len(code.splitlines()) > 100:
            issues.append("Code is long, consider splitting")
        
        return {
            "success": True,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 20),
            "action": "reviewed"
        }
    
    def _generate_simple(self, task, language):
        """简单代码生成（模板）"""
        if language != "python":
            return "// TODO: " + task
        return (
            '"""' + task + '"""\n'
            'def main():\n'
            '    print("Hello from ' + self.name + '!")\n'
            '    # TODO: ' + task + '\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        )


# ============================================================
# AgentPool — Agent 池
# ============================================================
class AgentPool:
    """管理多个子 Agent"""
    
    def __init__(self):
        self.agents = {}
    
    def create(self, name, role="coder"):
        agent = SubAgent(name, role)
        self.agents[name] = agent
        return agent
    
    def get(self, name):
        return self.agents.get(name)
    
    def list_all(self):
        return [(name, agent.role) for name, agent in self.agents.items()]
    
    def execute_parallel(self, tasks):
        """
        并行执行多个任务
        tasks: [(agent_name, task, language, project_dir), ...]
        返回: [(agent_name, result), ...]
        """
        results = []
        for agent_name, task, language, project_dir in tasks:
            agent = self.get(agent_name)
            if agent:
                result = agent.execute(task, language, project_dir)
                results.append((agent_name, result))
            else:
                results.append((agent_name, {"success": False, "error": "Agent not found"}))
        return results
    
    def execute_pipeline(self, task_name, steps):
        """
        流水线执行
        steps: [(agent_name, task, language, project_dir), ...]
        前一步的输出作为下一步的输入
        """
        print("[Pipeline] " + task_name)
        print("Steps: " + " -> ".join(s[0] for s in steps))
        print()
        
        context = {}
        for i, (agent_name, task, language, project_dir) in enumerate(steps, 1):
            print("[Step " + str(i) + "/" + str(len(steps)) + "] " + agent_name)
            agent = self.get(agent_name)
            if not agent:
                print("  ERROR: Agent not found")
                return {"success": False, "error": "Agent not found: " + agent_name}
            
            # 把上下文注入任务
            enriched_task = task
            if context:
                enriched_task = task + "\nContext: " + json.dumps(context, ensure_ascii=False)[:500]
            
            result = agent.execute(enriched_task, language, project_dir)
            context[agent_name] = result
            
            if not result.get("success"):
                print("  FAILED")
                return {"success": False, "step": i, "error": result.get("error", "Unknown")}
            print("  OK")
            print()
        
        return {"success": True, "context": context}


# ============================================================
# TaskSplitter — 任务拆分器
# ============================================================
class TaskSplitter:
    """把大任务拆分成可并行的小任务"""
    
    def split(self, requirement):
        """分析任务，返回子任务列表"""
        req = requirement.lower()
        sub_tasks = []
        
        if any(k in req for k in ["完整", "full", "项目", "project", "系统", "system"]):
            # 大项目 → 拆成多个模块
            sub_tasks = [
                ("coder-1", "Create main module", "python"),
                ("coder-2", "Create utility module", "python"),
                ("tester", "Run all tests", "python"),
                ("reviewer", "Review all code", "python"),
            ]
        elif any(k in req for k in ["web", "网站", "api", "server"]):
            sub_tasks = [
                ("coder-1", "Create server module", "python"),
                ("coder-2", "Create routes module", "python"),
                ("tester", "Test server", "python"),
            ]
        elif any(k in req for k in ["test", "测试"]):
            sub_tasks = [
                ("tester", "Run unit tests", "python"),
                ("reviewer", "Review test coverage", "python"),
            ]
        else:
            # 默认：单个任务
            sub_tasks = [
                ("coder-1", requirement, "python"),
                ("tester", "Test the code", "python"),
            ]
        
        return sub_tasks


# ============================================================
# Ghost Agent v2.2 Main Class
# ============================================================
class GhostAgentV22(GhostAgent if 'GhostAgent' in dir() else object):
    """Ghost Agent v2.2 — 多 Agent 协作版"""
    
    def __init__(self, ai=None):
        # Import from v21 if available
        try:
            from ghost_v21 import GhostAgent as G21, TemplateBackend
            self._base = G21(ai=ai)
            self.memory = self._base.memory
            self.executor = self._base.executor
            self.fixer = self._base.fixer
        except ImportError:
            self.memory = None
            self.executor = OpenClawExecutor()
            self.fixer = SmartFixerV2(None)
        
        self.pool = AgentPool()
        self.splitter = TaskSplitter()
        self._setup_default_agents()
    
    def _setup_default_agents(self):
        """创建默认的 Agent 团队"""
        self.pool.create("coder-1", "coder")
        self.pool.create("coder-2", "coder")
        self.pool.create("tester", "tester")
        self.pool.create("reviewer", "reviewer")
    
    def do_multi(self, requirement, language="python", project_dir=None):
        """多 Agent 协作执行"""
        print("=" * 60)
        print("Ghost Agent v2.2 — Multi-Agent Collaboration")
        print("=" * 60)
        print("Requirement: " + requirement)
        print("Team: " + str(self.pool.list_all()))
        print()
        
        # 1. 拆分任务
        print("[1/4] Task Splitting")
        sub_tasks = self.splitter.split(requirement)
        print("  Sub-tasks: " + str(len(sub_tasks)))
        for name, task, lang in sub_tasks:
            print("    " + name + ": " + task[:50])
        print()
        
        # 2. 并行执行
        print("[2/4] Parallel Execution")
        tasks = [(name, task, lang, project_dir) for name, task, lang in sub_tasks]
        results = self.pool.execute_parallel(tasks)
        
        # 3. 合并结果
        print()
        print("[3/4] Result Merging")
        merged = self._merge_results(results)
        
        # 4. 反思
        print("[4/4] Reflection")
        success = all(r.get("success", False) for _, r in results)
        print("  Overall: " + ("SUCCESS" if success else "PARTIAL FAILURE"))
        
        return {"success": success, "results": results, "merged": merged}
    
    def do_pipeline(self, requirement, language="python", project_dir=None):
        """流水线执行"""
        print("=" * 60)
        print("Ghost Agent v2.2 — Pipeline Mode")
        print("=" * 60)
        print("Requirement: " + requirement)
        print()
        
        steps = [
            ("coder-1", "Generate code for: " + requirement, language, project_dir),
            ("tester", "Test the generated code", language, project_dir),
            ("reviewer", "Review the code quality", language, project_dir),
        ]
        
        return self.pool.execute_pipeline(requirement, steps)
    
    def _merge_results(self, results):
        """合并子 Agent 的结果"""
        merged = {"success": True, "outputs": [], "errors": [], "issues": []}
        
        for name, result in results:
            if result.get("success"):
                if "stdout" in result:
                    merged["outputs"].append(result["stdout"][:200])
                if "code" in result:
                    merged["outputs"].append("Code generated: " + str(len(result["code"])) + " chars")
                if "issues" in result:
                    merged["issues"].extend(result["issues"])
            else:
                merged["success"] = False
                merged["errors"].append(name + ": " + result.get("error", "Unknown"))
        
        print("  Outputs: " + str(len(merged["outputs"])))
        print("  Errors: " + str(len(merged["errors"])))
        print("  Issues: " + str(len(merged["issues"])))
        
        return merged


# ============================================================
# OpenClaw Executor & SmartFixer (standalone)
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

class SmartFixerV2:
    def __init__(self, memory): self.memory = memory
    def fix(self, code, error, lang="python"):
        fixes = []
        if "NameError" in error:
            m = re.search(r"name '(\w+)' is not defined", error)
            if m: fixes.append("Undefined: " + m.group(1))
        if "SyntaxError" in error: fixes.append("Syntax error")
        if "ModuleNotFoundError" in error: fixes.append("Missing module")
        if "TypeError" in error: fixes.append("Type error")
        return code, "; ".join(fixes) if fixes else "Cannot fix", len(fixes) > 0


if __name__ == "__main__":
    import sys
    
    # Import v21 base classes
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ghost_v21 import GhostAgent, TemplateBackend, LongCatBackend
        print("Loaded v21 base classes")
    except ImportError:
        print("Warning: ghost_v21 not found, using standalone mode")
        GhostAgent = None
        TemplateBackend = None
        LongCatBackend = None
    
    agent = GhostAgentV22()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        agent.do_multi("write a complete web API project")
    elif len(sys.argv) > 1 and sys.argv[1] == "--pipeline":
        agent.do_pipeline("write a hello world script")
    elif len(sys.argv) > 1:
        agent.do_multi(" ".join(sys.argv[1:]))
    else:
        print("Usage:")
        print("  python ghost_v22.py --multi     # Multi-agent mode")
        print("  python ghost_v22.py --pipeline  # Pipeline mode")
        print("  python ghost_v22.py <task>      # Auto mode")
        print()
        agent.do_pipeline("write a hello world script")
