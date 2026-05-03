# -*- coding: utf-8 -*-
"""
Ghost Agent v3.1 - Desktop Launcher (No Electron)
使用系统默认浏览器打开 Web UI
"""
import subprocess
import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

WORKSPACE = Path(__file__).parent


def start_backend():
    """启动 Ghost Agent Python 后端"""
    print("[Launcher] 启动 Ghost Agent 后端...")
    backend = subprocess.Popen(
        [sys.executable, str(WORKSPACE / "web_ui.py")],
        cwd=str(WORKSPACE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"[Launcher] 后端 PID: {backend.pid}")
    return backend


def main():
    print("=" * 60)
    print("Ghost Agent v3.1 - Desktop")
    print("=" * 60)

    backend = start_backend()
    time.sleep(2)  # 等待后端启动

    # 用系统浏览器打开 Web UI
    url = "http://localhost:26602"
    print(f"[Launcher] 打开浏览器: {url}")
    webbrowser.open(url)

    print("[Ghost Agent 已启动!]")
    print("[Launcher] 按 Ctrl+C 退出")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\n[Launcher] 正在关闭...")
        backend.kill()
        print("[Launcher] 已退出")


if __name__ == "__main__":
    main()
