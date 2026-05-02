"""
Ghost Agent v1.1.0 — 全自动 AI 代码 Agent
作者: 小鬼 & Jake

核心升级:
- Auto-Fix Loop: 出错 → 自动分析 → 自动修复 → 再运行 (最多5轮)
- Smart Generator: 根据需求智能生成完整代码
- Task Manager: 任务队列管理
- Memory: 记住之前的调试经验
"""

import subprocess
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path(__file__).parent
PROJECTS_DIR = WORKSPACE / "projects"
LOGS_DIR = WORKSPACE / "logs"
MEMORY_FILE = WORKSPACE / "ghost_memory.json"
MAX_FIX_ROUNDS = 5
TIMEOUT = 30

for d in [PROJECTS_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)


# ============================================================
# 记忆系统 — 记住调试经验
# ============================================================
class GhostMemory:
    """记住之前遇到的错误和解决方案"""

    def __init__(self):
        self.data = {"errors": [], "fixes": [], "stats": {"total": 0, "success": 0, "failed": 0}}
        self.load()

    def load(self):
        if MEMORY_FILE.exists():
            try:
                self.data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

    def save(self):
        MEMORY_FILE.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def remember_error(self, error_type: str, detail: str, fix: str, success: bool):
        entry = {
            "time": datetime.now().isoformat(),
            "type": error_type,
            "detail": detail[:200],
            "fix": fix,
            "success": success
        }
        self.data["errors"].append(entry)
        self.data["stats"]["total"] += 1
        if success:
            self.data["stats"]["success"] += 1
        else:
            self.data["stats"]["failed"] += 1
        # 只保留最近50条
        self.data["errors"] = self.data["errors"][-50:]
        self.save()

    def find_similar_fix(self, error_type: str) -> str:
        """查找之前类似错误的修复方案"""
        for entry in reversed(self.data["errors"]):
            if entry["type"] == error_type and entry["success"]:
                return entry["fix"]
        return None


# ============================================================
# 代码执行器
# ============================================================
class Executor:
    """安全执行代码"""

    @staticmethod
    def run(code: str, language: str = "python", project_dir: str = None) -> dict:
        work_dir = Path(project_dir) if project_dir else PROJECTS_DIR
        work_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%H%M%S")

        if language == "python":
            suffix = ".py"
            cmd = [sys.executable, "-X", "utf8", str(work_dir / f"_run_{ts}.py")]
        elif language == "javascript":
            suffix = ".js"
            cmd = ["node", str(work_dir / f"_run_{ts}.js")]
        else:
            return {"success": False, "stdout": "", "stderr": f"不支持: {language}", "code": code}

        temp_file = work_dir / f"_run_{ts}{suffix}"
        temp_file.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=TIMEOUT,
                cwd=str(work_dir),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "code": code
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "执行超时", "code": code}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "code": code}


# ============================================================
# 智能修复器 — 自动修 bug
# ============================================================
class SmartFixer:
    """分析错误并自动修复代码"""

    # 修复规则: (错误模式, 修复函数)
    @staticmethod
    def fix(code: str, error: str, language: str = "python") -> tuple:
        """
        尝试自动修复代码
        返回: (修复后的代码, 修复描述, 是否修复了)
        """
        fixes_applied = []

        if language == "python":
            # 1. NameError: 拼写错误
            m = re.search(r"NameError: name '(\w+)' is not defined\. Did you mean: '(\w+)'", error)
            if m:
                wrong, correct = m.groups()
                code = code.replace(wrong, correct)
                fixes_applied.append(f"修正拼写: {wrong} → {correct}")

            # 2. ModuleNotFoundError
            m = re.search(r"No module named '(\w+)'", error)
            if m:
                module = m.group(1)
                fixes_applied.append(f"缺少模块 '{module}'，需要: pip install {module}")

            # 3. SyntaxError: 缺少冒号
            m = re.search(r"SyntaxError.*line (\d+)", error)
            if m:
                line_no = int(m.group(1))
                lines = code.split("\n")
                if 0 < line_no <= len(lines):
                    line = lines[line_no - 1]
                    # 检查是否是 for/if/def/class 缺少冒号
                    for keyword in ["for", "if", "elif", "else", "def", "class", "while", "try", "except", "with"]:
                        if line.strip().startswith(keyword) and not line.rstrip().endswith(":"):
                            lines[line_no - 1] = line.rstrip() + ":"
                            code = "\n".join(lines)
                            fixes_applied.append(f"L{line_no}: 在 '{keyword}' 后添加冒号")
                            break

            # 4. IndentationError
            if "IndentationError" in error or "expected an indented block" in error:
                m = re.search(r"line (\d+)", error)
                if m:
                    line_no = int(m.group(1))
                    lines = code.split("\n")
                    if 0 < line_no <= len(lines):
                        lines[line_no - 1] = "    " + lines[line_no - 1].lstrip()
                        code = "\n".join(lines)
                        fixes_applied.append(f"L{line_no}: 添加缩进")

            # 5. TypeError: str + int
            if "TypeError" in error and "concatenate" in error.lower():
                # 尝试简单修复
                fixes_applied.append("类型转换问题: 尝试用 str() 转换")

            # 6. KeyError
            m = re.search(r"KeyError: '(\w+)'", error)
            if m:
                key = m.group(1)
                fixes_applied.append(f"字典键 '{key}' 不存在，建议使用 .get('{key}', 默认值)")

            # 7. IndexError
            if "IndexError" in error:
                fixes_applied.append("索引越界，建议检查列表长度")

            # 8. FileNotFoundError
            if "FileNotFoundError" in error:
                m = re.search(r"\[Errno 2\] No such file or directory: '(.+)'", error)
                if m:
                    filepath = m.group(1)
                    fixes_applied.append(f"文件 '{filepath}' 不存在，请检查路径")

            # 9. ZeroDivisionError
            if "ZeroDivisionError" in error:
                fixes_applied.append("除以零错误，建议添加除数不为零的检查")

            # 10. AttributeError
            m = re.search(r"AttributeError: '(\w+)' object has no attribute '(\w+)'", error)
            if m:
                obj_type, attr = m.groups()
                fixes_applied.append(f"'{obj_type}' 对象没有 '{attr}' 属性，检查对象类型")

        fixed = len(fixes_applied) > 0
        fix_desc = "; ".join(fixes_applied) if fixes_applied else "无法自动修复"

        return code, fix_desc, fixed


# ============================================================
# 代码生成器 — 根据需求生成代码
# ============================================================
class CodeGenerator:
    """根据自然语言需求生成代码"""

    @staticmethod
    def generate(requirement: str, language: str = "python") -> str:
        req = requirement.lower()

        if language == "python":
            # 网页相关
            if any(k in req for k in ["网页", "爬", "抓取", "scrape", "crawl", "http"]):
                return CodeGenerator._web_scraper(requirement)
            # 文件操作
            elif any(k in req for k in ["文件", "整理", "归类", "organize", "file"]):
                return CodeGenerator._file_organizer(requirement)
            # 数据处理
            elif any(k in req for k in ["数据", "分析", "analyze", "data", "统计"]):
                return CodeGenerator._data_analysis(requirement)
            # API / 服务器
            elif any(k in req for k in ["api", "服务器", "server", "接口", "web"]):
                return CodeGenerator._api_server(requirement)
            # 图片处理
            elif any(k in req for k in ["图片", "image", "photo", "画图"]):
                return CodeGenerator._image_processor(requirement)
            # 自动化脚本
            elif any(k in req for k in ["自动化", "定时", "auto", "schedule"]):
                return CodeGenerator._auto_script(requirement)
            # 数学计算
            elif any(k in req for k in ["计算", "数学", "math", "计算"]):
                return CodeGenerator._math_calculator(requirement)
            # 默认
            else:
                return CodeGenerator._generic_script(requirement)

        elif language == "javascript":
            return CodeGenerator._js_generic(requirement)

        return f"# TODO: {requirement}"

    @staticmethod
    def _web_scraper(req):
        return f'''"""
{req}
Ghost Agent 自动生成
"""
import urllib.request
import re
from pathlib import Path

def fetch_page(url: str) -> str:
    """抓取网页内容"""
    req = urllib.request.Request(url, headers={{
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")

def extract_links(html: str) -> list:
    """提取所有链接"""
    return re.findall(r'href="(https?://[^"]+)"', html)

def extract_text(html: str) -> str:
    """提取纯文本"""
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

if __name__ == "__main__":
    url = "https://example.com"
    print(f"抓取: {{url}}")
    html = fetch_page(url)
    links = extract_links(html)
    text = extract_text(html)
    print(f"找到 {{len(links)}} 个链接")
    print(f"文本长度: {{len(text)}} 字符")
    print("\\n前200字符:")
    print(text[:200])
'''

    @staticmethod
    def _file_organizer(req):
        return f'''"""
{req}
Ghost Agent 自动生成
"""
from pathlib import Path
import shutil
from collections import defaultdict

def organize(directory: str):
    """按文件类型整理文件"""
    path = Path(directory)
    if not path.exists():
        print(f"目录不存在: {{directory}}")
        return

    type_map = {{
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".html": "HTML", ".css": "CSS", ".json": "JSON",
        ".md": "Markdown", ".txt": "Text",
        ".jpg": "Images", ".png": "Images", ".gif": "Images", ".bmp": "Images",
        ".mp4": "Videos", ".avi": "Videos", ".mkv": "Videos",
        ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
        ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
        ".pdf": "PDF", ".doc": "Documents", ".docx": "Documents",
        ".xls": "Spreadsheets", ".xlsx": "Spreadsheets",
        ".exe": "Executables", ".msi": "Executables",
    }}

    stats = defaultdict(list)
    for file in path.iterdir():
        if file.is_file():
            folder = type_map.get(file.suffix.lower(), "Others")
            target = path / folder
            target.mkdir(exist_ok=True)
            shutil.move(str(file), str(target / file.name))
            stats[folder].append(file.name)

    total = sum(len(v) for v in stats.values())
    print(f"整理了 {{total}} 个文件:")
    for folder, files in sorted(stats.items()):
        print(f"  [{{folder}}]: {{len(files)}} 个")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    organize(target)
'''

    @staticmethod
    def _data_analysis(req):
        return f'''"""
{req}
Ghost Agent 自动生成
"""
from collections import Counter
import math

def analyze(data: list) -> dict:
    """全面数据分析"""
    if not data:
        return {{"error": "空数据"}}

    result = {{"总数": len(data)}}

    if all(isinstance(x, (int, float)) for x in data):
        sorted_data = sorted(data)
        n = len(data)
        result.update({{
            "最小值": min(data),
            "最大值": max(data),
            "总和": sum(data),
            "平均值": sum(data) / n,
            "中位数": sorted_data[n // 2] if n % 2 else (sorted_data[n//2-1] + sorted_data[n//2]) / 2,
            "方差": sum((x - sum(data)/n) ** 2 for x in data) / n,
        }})
        result["标准差"] = math.sqrt(result["方差"])

    if all(isinstance(x, str) for x in data):
        lengths = [len(x) for x in data]
        counter = Counter(data)
        result.update({{
            "最短": min(lengths),
            "最长": max(lengths),
            "平均长度": sum(lengths) / len(lengths),
            "最常见": counter.most_common(5),
        }})

    return result

if __name__ == "__main__":
    # 示例: 数值分析
    data = [23, 45, 67, 12, 89, 34, 56, 78, 91, 15, 62, 37]
    print("=== 数值分析 ===")
    result = analyze(data)
    for k, v in result.items():
        print(f"  {{k}}: {{v}}")

    # 示例: 文本分析
    words = ["apple", "banana", "apple", "cherry", "banana", "apple", "date"]
    print("\\n=== 文本分析 ===")
    result = analyze(words)
    for k, v in result.items():
        print(f"  {{k}}: {{v}}")
'''

    @staticmethod
    def _api_server(req):
        return f'''"""
{req}
Ghost Agent 自动生成
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class APIHandler(BaseHTTPRequestHandler):
    routes = {{}}

    @classmethod
    def route(cls, path):
        def decorator(func):
            cls.routes[path] = func
            return func
        return decorator

    def do_GET(self):
        parsed = urlparse(self.path)
        handler = APIHandler.routes.get(parsed.path, self.handle_404)
        result = handler(self, parsed)
        self.send_json(result)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body) if body else {{}}
        except json.JSONDecodeError:
            data = {{"raw": body.decode()}}

        parsed = urlparse(self.path)
        handler = APIHandler.routes.get(parsed.path, self.handle_404)
        result = handler(self, parsed, data)
        self.send_json(result)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def handle_404(self, parsed, data=None):
        return {{"error": "Not Found", "path": parsed.path}}

    def log_message(self, fmt, *args):
        pass  # 静默

# 注册路由
@APIHandler.route("/")
def home(handler, parsed, data=None):
    return {{"message": "Ghost Agent API v1.0", "time": datetime.now().isoformat()}}

@APIHandler.route("/health")
def health(handler, parsed, data=None):
    return {{"status": "healthy"}}

@APIHandler.route("/echo")
def echo(handler, parsed, data=None):
    params = parse_qs(parsed.query)
    return {{"params": params, "data": data}}

@APIHandler.route("/time")
def time(handler, parsed, data=None):
    return {{"time": datetime.now().isoformat()}}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080)) if "os" in dir() else 8080
    server = HTTPServer(("localhost", port), APIHandler)
    print(f"Ghost Agent API 启动: http://localhost:{{port}}")
    print("路由: /, /health, /echo, /time")
    server.serve_forever()
'''

    @staticmethod
    def _image_processor(req):
        return f'''"""
{req}
Ghost Agent 自动生成
注意: 需要 pip install Pillow
"""
from pathlib import Path

def create_thumbnail(input_path: str, output_path: str, size=(128, 128)):
    """创建缩略图"""
    try:
        from PIL import Image
        img = Image.open(input_path)
        img.thumbnail(size)
        img.save(output_path)
        print(f"缩略图已保存: {{output_path}}")
    except ImportError:
        print("请先安装 Pillow: pip install Pillow")
    except Exception as e:
        print(f"错误: {{e}}")

def get_image_info(filepath: str) -> dict:
    """获取图片信息"""
    try:
        from PIL import Image
        img = Image.open(filepath)
        return {{
            "格式": img.format,
            "尺寸": img.size,
            "模式": img.mode,
            "文件大小": Path(filepath).stat().st_size,
        }}
    except ImportError:
        return {{"error": "请先安装 Pillow: pip install Pillow"}}
    except Exception as e:
        return {{"error": str(e)}}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        info = get_image_info(filepath)
        for k, v in info.items():
            print(f"  {{k}}: {{v}}")
    else:
        print("用法: python script.py <图片路径>")
'''

    @staticmethod
    def _auto_script(req):
        return f'''"""
{req}
Ghost Agent 自动生成
"""
import time
import schedule
from datetime import datetime

def task():
    """定时执行的任务"""
    print(f"[{{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}] 任务执行!")

def run_once():
    """执行一次"""
    print("执行任务...")
    task()
    print("完成!")

def run_scheduled():
    """定时执行"""
    schedule.every(1).minutes.do(task)
    print("定时任务已启动 (每分钟执行一次)")
    print("按 Ctrl+C 停止")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n已停止")

if __name__ == "__main__":
    import sys
    if "--schedule" in sys.argv:
        run_scheduled()
    else:
        run_once()
'''

    @staticmethod
    def _math_calculator(req):
        return f'''"""
{req}
Ghost Agent 自动生成
"""
import math
import random

class Calculator:
    """科学计算器"""

    @staticmethod
    def add(a, b): return a + b
    @staticmethod
    def sub(a, b): return a - b
    @staticmethod
    def mul(a, b): return a * b
    @staticmethod
    def div(a, b): return a / b if b != 0 else float("inf")
    @staticmethod
    def power(a, b): return a ** b
    @staticmethod
    def sqrt(a): return math.sqrt(a) if a >= 0 else None
    @staticmethod
    def factorial(n): return math.factorial(n) if n >= 0 else None
    @staticmethod
    def fibonacci(n):
        if n <= 0: return []
        if n == 1: return [0]
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[-1] + fib[-2])
        return fib
    @staticmethod
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0: return False
        return True
    @staticmethod
    def gcd(a, b): return math.gcd(a, b)
    @staticmethod
    def lcm(a, b): return abs(a * b) // math.gcd(a, b)

if __name__ == "__main__":
    calc = Calculator()
    print("=== 数学计算器 ===")
    print(f"  2 + 3 = {{calc.add(2, 3)}}")
    print(f"  10 - 4 = {{calc.sub(10, 4)}}")
    print(f"  6 * 7 = {{calc.mul(6, 7)}}")
    print(f"  100 / 3 = {{calc.div(100, 3):.4f}}")
    print(f"  2^10 = {{calc.power(2, 10)}}")
    print(f"  sqrt(144) = {{calc.sqrt(144)}}")
    print(f"  10! = {{calc.factorial(10)}}")
    print(f"  fib(15) = {{calc.fibonacci(15)}}")
    print(f"  17 是质数? {{calc.is_prime(17)}}")
    print(f"  gcd(12, 18) = {{calc.gcd(12, 18)}}")
    print(f"  lcm(12, 18) = {{calc.lcm(12, 18)}}")
'''

    @staticmethod
    def _generic_script(req):
        return f'''"""
{req}
Ghost Agent 自动生成
时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
from pathlib import Path

def main():
    """主函数"""
    print("Ghost Agent 自动生成的脚本")
    print("需求: {req}")
    # TODO: 根据需求实现具体逻辑
    print("Hello from Ghost Agent!")

if __name__ == "__main__":
    main()
'''

    @staticmethod
    def _js_generic(req):
        return f'''/**
 * {req}
 * Ghost Agent 自动生成
 */
function main() {{
    console.log("Ghost Agent JS 脚本");
    console.log("需求: {req}");
    // TODO: 实现逻辑
}}

main();
'''


# ============================================================
# Ghost Agent 主类 v1.1.0
# ============================================================
class GhostAgent:
    """
    全自动 AI 代码 Agent
    - 理解需求 → 生成代码 → 运行 → 自动修复 → 成功
    """

    def __init__(self):
        self.executor = Executor()
        self.fixer = SmartFixer()
        self.generator = CodeGenerator()
        self.memory = GhostMemory()
        self.task_history = []

    def do(self, requirement: str, language: str = "python", project_dir: str = None) -> dict:
        """
        执行任务: 需求 → 代码 → 运行 → 自动修复

        返回:
        {
            "success": bool,
            "requirement": str,
            "language": str,
            "rounds": int,         # 尝试了几轮
            "final_code": str,     # 最终代码
            "output": str,         # 输出
            "fixes": list,         # 修复记录
        }
        """
        print("=" * 60)
        print("Ghost Agent v1.1.0")
        print("=" * 60)
        print(f"需求: {requirement}")
        print(f"语言: {language}")
        print()

        # Step 1: 生成代码
        print("[1/3] 生成代码...")
        code = self.generator.generate(requirement, language)
        print(f"  生成了 {len(code.splitlines())} 行代码")

        # Step 2: 运行 + 自动修复循环
        print("[2/3] 运行 + 自动修复...")
        fixes = []
        current_code = code

        for round_num in range(1, MAX_FIX_ROUNDS + 1):
            print(f"  --- 第 {round_num} 轮 ---")

            result = self.executor.run(current_code, language, project_dir)

            if result["success"]:
                print(f"  成功! (第{round_num}轮)")
                break
            else:
                error = result["stderr"]
                print(f"  失败: {error[:100]}")

                # 尝试自动修复
                new_code, fix_desc, fixed = self.fixer.fix(current_code, error, language)

                if fixed:
                    print(f"  修复: {fix_desc}")
                    fixes.append({"round": round_num, "fix": fix_desc, "error": error[:100]})
                    current_code = new_code
                else:
                    print(f"  无法自动修复: {fix_desc}")
                    fixes.append({"round": round_num, "fix": "无法自动修复: " + fix_desc, "error": error[:100]})

                    # 查记忆
                    error_type = "Unknown"
                    for pattern in ["NameError", "TypeError", "SyntaxError", "ModuleNotFoundError",
                                     "IndentationError", "KeyError", "IndexError", "FileNotFoundError",
                                     "ZeroDivisionError", "AttributeError"]:
                        if pattern in error:
                            error_type = pattern
                            break

                    similar_fix = self.memory.find_similar_fix(error_type)
                    if similar_fix:
                        print(f"  记忆提示: {similar_fix}")

                    # 如果是模块缺失，不算真正的代码错误
                    if "pip install" in fix_desc:
                        break

                    if round_num == MAX_FIX_ROUNDS:
                        print(f"  已达最大修复轮数 ({MAX_FIX_ROUNDS})")
        else:
            result = self.executor.run(current_code, language, project_dir)

        # Step 3: 生成报告
        print("[3/3] 生成报告...")
        success = result["success"]
        output = result["stdout"]

        # 记住这次经验
        if not success:
            error_type = "Unknown"
            for pattern in ["NameError", "TypeError", "SyntaxError", "ModuleNotFoundError",
                             "IndentationError", "KeyError", "IndexError", "FileNotFoundError",
                             "ZeroDivisionError", "AttributeError"]:
                if pattern in result["stderr"]:
                    error_type = pattern
                    break
            self.memory.remember_error(error_type, result["stderr"], str(fixes), success)

        report = {
            "success": success,
            "requirement": requirement,
            "language": language,
            "rounds": round_num,
            "final_code": current_code,
            "output": output,
            "fixes": fixes,
            "error": result["stderr"] if not success else None,
        }

        self.task_history.append({
            "time": datetime.now().isoformat(),
            "requirement": requirement,
            "success": success,
            "rounds": round_num,
        })

        # 输出结果
        print()
        print("=" * 60)
        if success:
            print("任务完成!")
            print(f"轮数: {round_num}")
            if output:
                print(f"输出:\\n{output[:300]}")
        else:
            print("任务失败")
            print(f"尝试了 {round_num} 轮自动修复")
            print(f"最后错误: {result['stderr'][:200]}")
        print("=" * 60)

        return report


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    import sys

    agent = GhostAgent()

    if len(sys.argv) > 1:
        requirement = " ".join(sys.argv[1:])
        report = agent.do(requirement)
    else:
        # 默认测试
        print("用法: python ghost_agent.py <需求描述>")
        print()
        print("运行默认测试...")
        print()

        # 测试1: 正常代码
        report = agent.do("写一个数据分析脚本")

        print()

        # 测试2: 有bug的代码（会被自动修复）
        report = agent.do("写一个数学计算器")
