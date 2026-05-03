# -*- coding: utf-8 -*-
"""
Ghost Agent Web UI - Desktop Launcher
用 PyInstaller 打包为独立 exe
"""
import subprocess
import sys
import os
import time
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


def start_electron():
    """启动 Electron 前端"""
    print("[Launcher] 启动 Electron 前端...")
    electron_dir = WORKSPACE / "electron"

    # 检查 electron 是否可用
    electron_exe = electron_dir / "node_modules" / ".bin" / "electron.cmd"
    if not electron_exe.exists():
        print("[Launcher] Electron 未安装，请先运行: cd electron && npm install")
        return None

    frontend = subprocess.Popen(
        [str(electron_exe), "."],
        cwd=str(electron_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"[Launcher] 前端 PID: {frontend.pid}")
    return frontend


def main():
    print("=" * 60)
    print("Ghost Agent v3.1 - Desktop Launcher")
    print("=" * 60)

    backend = start_backend()
    time.sleep(2)  # 等待后端启动

    frontend = start_electron()
    if frontend is None:
        print("[Launcher] 启动失败")
        backend.kill()
        return

    print("[Launcher] Ghost Agent 已启动!")
    print("[Launcher] 按 Ctrl+C 退出")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\n[Launcher] 正在关闭...")
        frontend.kill()
        backend.kill()
        print("[Launcher] 已退出")


if __name__ == "__main__":
    main()
