# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ghost_v2 import GhostAgent

agent = GhostAgent()

tasks = [
    "写一个数学计算器",
    "写一个API服务器",
    "写一个文件整理脚本",
    "写一个网页爬虫",
    "写一个猜数字游戏",
]

for t in tasks:
    print("\n" + "=" * 60)
    r = agent.do(t)
    print(f"\n结果: {'OK' if r['success'] else 'FAIL'} | 轮数: {r['rounds']} | 修复: {len(r['fixes'])}")

print("\n" + "=" * 60)
print("记忆统计:", agent.memory.l1.keys())
print("错误记录:", len(agent.memory.errors.get("list", [])))
