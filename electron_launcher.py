# -*- coding: utf-8 -*-
"""
Ghost Agent v3.1 - Electron Desktop App Launcher
启动 Python 后端 + Electron 前端
"""
import subprocess
import sys
import time
import os
from pathlib import Path

WORKSPACE = Path(__file__).parent

def start_backend():
    """启动 Ghost Agent Python 后端"""
    print("[Launcher] 启动 Ghost Agent 后端...")
    
    # 使用 PyInstaller 打包后的路径
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        backend_path = Path(sys._MEIPASS) / "ghost_v31.py"
    else:
        # 开发环境
        backend_path = WORKSPACE / "ghost_v31.py"
    
    # 启动 web_ui.py 作为后端
    backend = subprocess.Popen(
        [sys.executable, str(WORKSPACE / "web_ui.py")],
        cwd=str(WORKSPACE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    print(f"[Launcher] 后端 PID: {backend.pid}")
    time.sleep(2)  # 等待后端启动
    
    return backend

def start_electron():
    """启动 Electron 前端"""
    print("[Launcher] 启动 Electron 前端...")
    
    electron_dir = WORKSPACE / "electron"
    
    if getattr(sys, 'frozen', False):
        # 打包后：electron 可执行文件
        electron_path = Path(sys._MEIPASS) / "electron" / "Ghost Agent.exe"
        subprocess.Popen([str(electron_path)], cwd=str(electron_dir))
    else:
        # 开发环境：使用 npx 启动
        subprocess.Popen(
            ["npx", "electron", "."],
            cwd=str(electron_dir),
            shell=True,
        )

def main():
    print("=" * 60)
    print("Ghost Agent v3.1 - Desktop App")
    print("=" * 60)
    
    backend = start_backend()
    start_electron()
    
    print("[Launcher] Ghost Agent 已启动!")
    print("[Launcher] 按 Ctrl+C 退出")
    
    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\n[Launcher] 正在关闭...")
        backend.kill()
        print("[Launcher] 已退出")

if __name__ == "__main__":
    main()
