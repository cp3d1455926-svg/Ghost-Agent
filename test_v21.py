# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ghost_v21 import GhostAgent

agent = GhostAgent()

tasks = [
    "write a data analysis script",
    "write a file organizer",
    "write a web scraper",
    "write an API server",
    "write a number guessing game",
]

for t in tasks:
    print("\n" + "=" * 60)
    r = agent.do(t)
    status = "OK" if r["success"] else "FAIL"
    print("Result: " + status + " | Rounds: " + str(r["rounds"]) + " | Fixes: " + str(len(r["fixes"])))

print("\n" + "=" * 60)
print("All tests done!")
print("Memory stats - L0:", len(agent.memory.l0), "L1:", len(agent.memory.l1))
print("Error patterns:", len(agent.memory.errors.get("list", [])))
