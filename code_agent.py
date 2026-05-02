"""
Ghost Agent — 自动写代码 + 调试系统
作者: 小鬼 & Jake
版本: v1.0.0
"""

import subprocess
import os
import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path(__file__).parent
PROJECTS_DIR = WORKSPACE / "projects"
LOGS_DIR = WORKSPACE / "logs"
MAX_DEBUG_ROUNDS = 5  # 最大自动调试轮数
TIMEOUT = 30  # 代码执行超时(秒)

for d in [PROJECTS_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)


# ============================================================
# 日志系统
# ============================================================
class Logger:
    def __init__(self, name="code_agent"):
        self.log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    def log(self, level, message):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] {message}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def info(self, msg): self.log("INFO", msg)
    def error(self, msg): self.log("ERROR", msg)
    def success(self, msg): self.log("OK", msg)
    def debug(self, msg): self.log("DEBUG", msg)


logger = Logger()


# ============================================================
# 代码执行器 — 安全运行代码
# ============================================================
class CodeExecutor:
    """安全地执行代码，捕获输出和错误"""

    @staticmethod
    def run_python(code: str, project_dir: str = None) -> dict:
        """运行 Python 代码，返回结果"""
        work_dir = Path(project_dir) if project_dir else PROJECTS_DIR
        work_dir.mkdir(exist_ok=True)

        # 写入临时文件
        timestamp = datetime.now().strftime("%H%M%S")
        temp_file = work_dir / f"_run_{timestamp}.py"

        try:
            temp_file.write_text(code, encoding="utf-8")
            logger.debug(f"代码已写入: {temp_file}")

            result = subprocess.run(
                [sys.executable, str(temp_file)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                cwd=str(work_dir),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "file": str(temp_file)
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（>{TIMEOUT}秒）",
                "returncode": -1,
                "file": str(temp_file)
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "file": str(temp_file)
            }

    @staticmethod
    def run_node(code: str, project_dir: str = None) -> dict:
        """运行 Node.js 代码"""
        work_dir = Path(project_dir) if project_dir else PROJECTS_DIR
        work_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%H%M%S")
        temp_file = work_dir / f"_run_{timestamp}.js"

        try:
            temp_file.write_text(code, encoding="utf-8")

            result = subprocess.run(
                ["node", str(temp_file)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                cwd=str(work_dir)
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "file": str(temp_file)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（>{TIMEOUT}秒）",
                "returncode": -1,
                "file": str(temp_file)
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "file": str(temp_file)
            }

    @staticmethod
    def run_shell(command: str, project_dir: str = None) -> dict:
        """运行 Shell 命令"""
        work_dir = Path(project_dir) if project_dir else PROJECTS_DIR

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                cwd=str(work_dir),
                shell=True
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（>{TIMEOUT}秒）",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }


# ============================================================
# 代码分析器 — 静态检查
# ============================================================
class CodeAnalyzer:
    """分析代码质量"""

    @staticmethod
    def analyze_python(code: str) -> dict:
        """基础 Python 代码分析"""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 检查常见问题
            if "import *" in stripped:
                issues.append(f"L{i}: 避免使用 import *")
            except_count = 0
            if stripped == "except:" or stripped.startswith("except :"):
                issues.append(f"L{i}: 避免裸 except，应指定异常类型")
            if "print(" in stripped and not stripped.startswith("#"):
                pass  # print 在调试中可以接受
            if "TODO" in stripped or "FIXME" in stripped:
                issues.append(f"L{i}: 有未完成的 TODO/FIXME")

        # 检查语法
        try:
            compile(code, "<string>", "exec")
            syntax_ok = True
        except SyntaxError as e:
            syntax_ok = False
            issues.append(f"语法错误 L{e.lineno}: {e.msg}")

        return {
            "syntax_ok": syntax_ok,
            "lines": len(lines),
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)
        }


# ============================================================
# 自动调试器 — 分析错误并给出修复建议
# ============================================================
class AutoDebugger:
    """分析错误输出，给出修复建议"""

    # 常见错误模式
    ERROR_PATTERNS = {
        "ModuleNotFoundError": {
            "pattern": "ModuleNotFoundError: No module named",
            "fix": "pip install <module>"
        },
        "ImportError": {
            "pattern": "ImportError",
            "fix": "检查模块是否安装，或修正 import 路径"
        },
        "SyntaxError": {
            "pattern": "SyntaxError",
            "fix": "检查语法：括号匹配、缩进、冒号等"
        },
        "IndentationError": {
            "pattern": "IndentationError",
            "fix": "检查缩进，Python 需要一致的缩进（建议4空格）"
        },
        "NameError": {
            "pattern": "NameError",
            "fix": "变量未定义，检查变量名拼写和作用域"
        },
        "TypeError": {
            "pattern": "TypeError",
            "fix": "类型错误，检查函数参数类型是否正确"
        },
        "IndexError": {
            "pattern": "IndexError",
            "fix": "索引越界，检查列表/字符串长度"
        },
        "KeyError": {
            "pattern": "KeyError",
            "fix": "字典键不存在，使用 .get() 或检查键名"
        },
        "FileNotFoundError": {
            "pattern": "FileNotFoundError",
            "fix": "文件不存在，检查文件路径是否正确"
        },
        "ZeroDivisionError": {
            "pattern": "ZeroDivisionError",
            "fix": "除以零，添加除数不为零的检查"
        },
        "AttributeError": {
            "pattern": "AttributeError",
            "fix": "对象没有该属性/方法，检查对象类型"
        },
        "TimeoutError": {
            "pattern": "超时",
            "fix": "代码执行超时，检查是否有死循环"
        },
    }

    @classmethod
    def diagnose(cls, error_output: str) -> dict:
        """诊断错误，返回可能的原因和修复建议"""
        results = []

        for error_type, info in cls.ERROR_PATTERNS.items():
            if info["pattern"] in error_output:
                # 提取具体信息
                detail = ""
                lines = error_output.split("\n")
                for line in lines:
                    if info["pattern"] in line:
                        detail = line.strip()
                        break

                results.append({
                    "type": error_type,
                    "detail": detail,
                    "suggestion": info["fix"]
                })

        if not results:
            results.append({
                "type": "Unknown",
                "detail": error_output[:200],
                "suggestion": "查看完整错误输出，搜索相关文档"
            })

        return {
            "identified_errors": results,
            "total": len(results)
        }


# ============================================================
# 项目上下文 — 理解项目结构
# ============================================================
class ProjectContext:
    """理解和管理项目上下文"""

    @staticmethod
    def scan(project_dir: str) -> dict:
        """扫描项目目录结构"""
        path = Path(project_dir)
        if not path.exists():
            return {"error": f"目录不存在: {project_dir}"}

        files = []
        dirs = []

        for item in path.rglob("*"):
            if item.is_file():
                rel = item.relative_to(path)
                files.append({
                    "path": str(rel),
                    "size": item.stat().st_size,
                    "ext": item.suffix
                })
            else:
                rel = item.relative_to(path)
                dirs.append(str(rel))

        # 检测项目类型
        project_type = "unknown"
        if (path / "package.json").exists():
            project_type = "nodejs"
        elif (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
            project_type = "python"
        elif (path / "Cargo.toml").exists():
            project_type = "rust"
        elif (path / "pom.xml").exists():
            project_type = "java"
        elif any(f["ext"] == ".py" for f in files):
            project_type = "python"
        elif any(f["ext"] == ".js" for f in files):
            project_type = "javascript"

        return {
            "type": project_type,
            "total_files": len(files),
            "total_dirs": len(dirs),
            "files": files[:50],  # 最多返回50个文件
            "dirs": dirs[:20],
        }

    @staticmethod
    def read_file(filepath: str) -> str:
        """读取文件内容"""
        path = Path(filepath)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    @staticmethod
    def write_file(filepath: str, content: str):
        """写入文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.success(f"文件已写入: {filepath}")

    @staticmethod
    def list_files(project_dir: str, pattern: str = "*") -> list:
        """列出匹配的文件"""
        path = Path(project_dir)
        if not path.exists():
            return []
        return [str(f.relative_to(path)) for f in path.rglob(pattern) if f.is_file()]


# ============================================================
# Code Agent 主类
# ============================================================
class CodeAgent:
    """
    全能代码 Agent
    - 根据需求编写代码
    - 自动运行和调试
    - 理解项目上下文
    """

    def __init__(self):
        self.executor = CodeExecutor()
        self.analyzer = CodeAnalyzer()
        self.debugger = AutoDebugger()
        self.context = ProjectContext()
        self.history = []

    def write_and_run(self, code: str, language: str = "python",
                      project_dir: str = None, description: str = "") -> dict:
        """编写并运行代码，自动诊断错误"""

        logger.info(f"{'='*50}")
        logger.info(f"任务: {description or '代码执行'}")
        logger.info(f"语言: {language}")

        # 1. 静态分析
        if language == "python":
            analysis = self.analyzer.analyze_python(code)
            logger.debug(f"代码分析: {analysis['lines']}行, 得分 {analysis['score']}")
            if not analysis["syntax_ok"]:
                logger.error(f"语法错误: {analysis['issues']}")
                return {"success": False, "phase": "analysis", "issues": analysis["issues"]}

        # 2. 执行代码
        if language == "python":
            result = self.executor.run_python(code, project_dir)
        elif language == "javascript":
            result = self.executor.run_node(code, project_dir)
        else:
            result = {"success": False, "stderr": f"不支持的语言: {language}"}

        # 3. 记录历史
        self.history.append({
            "time": datetime.now().isoformat(),
            "description": description,
            "language": language,
            "success": result["success"]
        })

        # 4. 输出结果
        if result["success"]:
            logger.success("代码执行成功!")
            if result["stdout"]:
                logger.info(f"输出:\n{result['stdout'][:500]}")
        else:
            logger.error(f"执行失败: {result['stderr'][:300]}")
            diagnosis = self.debugger.diagnose(result["stderr"])
            logger.info(f"诊断结果: {json.dumps(diagnosis, ensure_ascii=False, indent=2)}")

        return result

    def explain_error(self, error_output: str) -> str:
        """解释错误并给出修复建议"""
        diagnosis = self.debugger.diagnose(error_output)
        lines = []
        for err in diagnosis["identified_errors"]:
            lines.append(f"🔴 {err['type']}: {err['detail']}")
            lines.append(f"   💡 建议: {err['suggestion']}")
        return "\n".join(lines)

    def get_project_info(self, project_dir: str) -> dict:
        """获取项目信息"""
        return self.context.scan(project_dir)


# ============================================================
# 如果直接运行，执行测试
# ============================================================
if __name__ == "__main__":
    agent = CodeAgent()

    print("=" * 60)
    print("👻 Ghost Agent v1.0.0 — 自动写代码 + 调试系统")
    print("=" * 60)

    # 测试1: 正常运行
    print("\n📝 测试1: 正常代码")
    result = agent.write_and_run(
        code='print("Hello from Code Agent! 🤖")\nfor i in range(5):\n    print(f"  计数: {i}")',
        language="python",
        description="基础测试"
    )

    # 测试2: 有错误的代码
    print("\n📝 测试2: 有错误的代码")
    result = agent.write_and_run(
        code='prnt("这里有错误")',
        language="python",
        description="错误测试"
    )
    if not result["success"]:
        print(agent.explain_error(result["stderr"]))

    # 测试3: 缺少模块
    print("\n📝 测试3: 缺少模块")
    result = agent.write_and_run(
        code='import nonexistent_module_12345',
        language="python",
        description="模块缺失测试"
    )
    if not result["success"]:
        print(agent.explain_error(result["stderr"]))

    print("\n✅ Code Agent 测试完成!")
    print(f"📊 执行了 {len(agent.history)} 个任务")
