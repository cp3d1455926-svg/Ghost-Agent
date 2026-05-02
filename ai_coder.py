"""
Ghost Agent — 自然语言 → 代码生成 → 运行 → 调试
作者: 小鬼 & Jake
版本: v1.0.0

这个模块让我（小鬼）能够：
1. 理解你的需求（自然语言）
2. 生成代码
3. 运行代码
4. 自动调试直到成功
"""

import json
import os
from pathlib import Path
from datetime import datetime
from code_agent import CodeAgent, logger

# ============================================================
# 代码模板库
# ============================================================
CODE_TEMPLATES = {
    "python": {
        "web_scraper": '''"""
网页抓取器
需求: {requirement}
"""
import urllib.request
import re
from pathlib import Path

def fetch_page(url: str) -> str:
    """抓取网页内容"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")

def extract_links(html: str) -> list:
    """提取所有链接"""
    return re.findall(r'href="(https?://[^"]+)"', html)

if __name__ == "__main__":
    url = "https://example.com"
    print(f"抓取: {url}")
    html = fetch_page(url)
    links = extract_links(html)
    print(f"找到 {len(links)} 个链接")
    for link in links[:10]:
        print(f"  → {link}")
''',

        "file_organizer": '''"""
文件整理器
需求: {requirement}
"""
from pathlib import Path
import shutil
from collections import defaultdict

def organize_files(directory: str):
    """按文件类型整理文件"""
    path = Path(directory)
    if not path.exists():
        print(f"目录不存在: {directory}")
        return

    # 文件类型映射
    type_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".html": "HTML", ".css": "CSS", ".json": "JSON",
        ".md": "Markdown", ".txt": "Text",
        ".jpg": "Images", ".png": "Images", ".gif": "Images",
        ".mp4": "Videos", ".mp3": "Audio",
        ".zip": "Archives", ".pdf": "PDF",
    }

    stats = defaultdict(list)

    for file in path.iterdir():
        if file.is_file():
            folder_name = type_map.get(file.suffix.lower(), "Others")
            target_dir = path / folder_name
            target_dir.mkdir(exist_ok=True)
            shutil.move(str(file), str(target_dir / file.name))
            stats[folder_name].append(file.name)

    print(f"整理了 {sum(len(v) for v in stats.values())} 个文件:")
    for folder, files in sorted(stats.items()):
        print(f"  📁 {folder}: {len(files)} 个文件")

if __name__ == "__main__":
    organize_files(".")
''',

        "data_analysis": '''"""
数据分析器
需求: {requirement}
"""
import json
from collections import Counter
from pathlib import Path

def analyze_data(data: list) -> dict:
    """分析数据"""
    if not data:
        return {"error": "空数据"}

    result = {
        "总数": len(data),
        "类型": type(data[0]).__name__ if data else "unknown",
    }

    # 数值分析
    if all(isinstance(x, (int, float)) for x in data):
        result.update({
            "最小值": min(data),
            "最大值": max(data),
            "平均值": sum(data) / len(data),
            "总和": sum(data),
        })

    # 文本分析
    if all(isinstance(x, str) for x in data):
        lengths = [len(x) for x in data]
        counter = Counter(data)
        result.update({
            "最短": min(lengths),
            "最长": max(lengths),
            "平均长度": sum(lengths) / len(lengths),
            "最常见": counter.most_common(3),
        })

    return result

if __name__ == "__main__":
    # 示例数据
    sample = [12, 45, 23, 89, 34, 56, 78, 90, 11, 67]
    result = analyze_data(sample)
    print("数据分析结果:")
    for k, v in result.items():
        print(f"  {k}: {v}")
''',

        "api_server": '''"""
简单 API 服务器
需求: {requirement}
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class APIHandler(BaseHTTPRequestHandler):
    """简单的 REST API 处理器"""

    def do_GET(self):
        parsed = urlparse(self.path)
        routes = {
            "/": self.handle_root,
            "/health": self.handle_health,
            "/time": self.handle_time,
        }

        handler = routes.get(parsed.path, self.handle_404)
        handler()

    def handle_root(self):
        self.send_json({"message": "API 服务运行中", "version": "1.0"})

    def handle_health(self):
        self.send_json({"status": "healthy", "uptime": "running"})

    def handle_time(self):
        from datetime import datetime
        self.send_json({"time": datetime.now().isoformat()})

    def handle_404(self):
        self.send_json({"error": "Not Found"}, status=404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass  # 静默日志

if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("localhost", port), APIHandler)
    print(f"🚀 API 服务器启动: http://localhost:{port}")
    print("按 Ctrl+C 停止")
    server.serve_forever()
''',
    },

    "javascript": {
        "fetch_data": '''/**
 * 数据获取工具
 * 需求: {requirement}
 */
const https = require('https');
const http = require('http');

function fetchURL(url) {
    return new Promise((resolve, reject) => {
        const mod = url.startsWith('https') ? https : http;
        mod.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        }).on('error', reject);
    });
}

async function main() {
    console.log('📡 数据获取工具启动');
    // 示例
    try {
        const data = await fetchURL('https://httpbin.org/get');
        console.log('响应数据:', data.substring(0, 200));
    } catch (e) {
        console.error('获取失败:', e.message);
    }
}

main();
''',

        "file_watcher": '''/**
 * 文件监控器
 * 需求: {requirement}
 */
const fs = require('fs');
const path = require('path');

function watchDir(dirPath) {
    console.log(`👀 监控目录: ${dirPath}`);

    fs.watch(dirPath, (eventType, filename) => {
        if (filename) {
            console.log(`  [${eventType}] ${filename}`);
        }
    });

    console.log('按 Ctrl+C 停止监控');
}

const targetDir = process.argv[2] || '.';
watchDir(path.resolve(targetDir));
''',
    }
}


# ============================================================
# AI Coder 主类
# ============================================================
class AICoder:
    """
    自然语言 → 代码生成 → 运行 → 自动调试
    """

    def __init__(self):
        self.agent = CodeAgent()
        self.project_dir = str(Path(__file__).parent / "projects")

    def generate_code(self, description: str, language: str = "python") -> str:
        """
        根据自然语言描述生成代码
        这里使用模板 + 简单替换，后续可以接入真正的 AI 生成
        """
        desc_lower = description.lower()

        if language == "python":
            if any(kw in desc_lower for kw in ["爬", "抓取", "网页", "scrape", "crawl"]):
                return CODE_TEMPLATES["python"]["web_scraper"].format(requirement=description)
            elif any(kw in desc_lower for kw in ["整理", "归类", "文件", "organize"]):
                return CODE_TEMPLATES["python"]["file_organizer"].format(requirement=description)
            elif any(kw in desc_lower for kw in ["分析", "数据", "analyze", "data"]):
                return CODE_TEMPLATES["python"]["data_analysis"].format(requirement=description)
            elif any(kw in desc_lower for kw in ["api", "服务器", "server", "接口"]):
                return CODE_TEMPLATES["python"]["api_server"].format(requirement=description)
            else:
                # 默认：生成一个基础脚本框架
                return f'''"""
{description}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
from pathlib import Path

def main():
    """主函数"""
    print("🚀 程序启动")
    # TODO: 实现你的逻辑
    print("✅ 完成!")

if __name__ == "__main__":
    main()
'''
        elif language == "javascript":
            if any(kw in desc_lower for kw in ["监控", "watch", "文件变化"]):
                return CODE_TEMPLATES["javascript"]["file_watcher"].format(requirement=description)
            else:
                return CODE_TEMPLATES["javascript"]["fetch_data"].format(requirement=description)

        return f"# TODO: {description}"

    def run_task(self, description: str, language: str = "python",
                 auto_debug: bool = True) -> dict:
        """
        完整的任务流程:
        1. 理解需求 → 生成代码
        2. 运行代码
        3. 如果有错误 → 自动诊断
        """

        logger.info(f"{'='*60}")
        logger.info(f"🎯 收到任务: {description}")
        logger.info(f"{'='*60}")

        # Step 1: 生成代码
        logger.info("📝 Step 1: 生成代码...")
        code = self.generate_code(description, language)
        logger.info(f"   生成了 {len(code.splitlines())} 行代码")

        # Step 2: 运行代码
        logger.info("▶️ Step 2: 运行代码...")
        result = self.agent.write_and_run(
            code=code,
            language=language,
            project_dir=self.project_dir,
            description=description
        )

        # Step 3: 自动诊断
        if not result["success"] and auto_debug:
            logger.info("🔧 Step 3: 自动诊断...")
            diagnosis = self.agent.explain_error(result["stderr"])
            logger.info(f"诊断结果:\n{diagnosis}")
            result["diagnosis"] = diagnosis

        # 生成报告
        report = {
            "task": description,
            "language": language,
            "success": result["success"],
            "code_lines": len(code.splitlines()),
            "output": result.get("stdout", "")[:500],
            "error": result.get("stderr", "")[:300] if not result["success"] else None,
            "generated_code": code,
        }

        if not result["success"] and "diagnosis" in result:
            report["diagnosis"] = result["diagnosis"]

        return report

    def batch_run(self, tasks: list) -> list:
        """批量执行任务"""
        results = []
        for task in tasks:
            if isinstance(task, str):
                result = self.run_task(task)
            else:
                result = self.run_task(
                    task.get("description", ""),
                    task.get("language", "python")
                )
            results.append(result)
        return results


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    coder = AICoder()

    print("=" * 60)
    print("🤖 AI Coder v1.0.0 — 自然语言 → 代码 → 运行 → 调试")
    print("=" * 60)

    # 测试任务
    tasks = [
        ("写一个数据分析脚本", "python"),
        ("写一个API服务器", "python"),
    ]

    for desc, lang in tasks:
        print(f"\n{'─'*50}")
        report = coder.run_task(desc, lang, auto_debug=False)
        print(f"\n结果: {'✅ 成功' if report['success'] else '❌ 失败'}")
        if report["output"]:
            print(f"输出: {report['output'][:200]}")

    print(f"\n{'='*60}")
    print("✅ 所有任务执行完毕!")
