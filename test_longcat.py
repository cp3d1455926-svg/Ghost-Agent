# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ghost_v21 import GhostAgent, LongCatBackend

print("Testing LongCat backend...")
print()

# Test 1: Direct backend call
backend = LongCatBackend()
print("[Test 1] Direct API call:")
code = backend.generate_code("write a Python function to calculate factorial", "python")
print(code[:300])
print()

# Test 2: Full Ghost Agent with LongCat
print("[Test 2] Full Ghost Agent:")
agent = GhostAgent(ai=LongCatBackend())
r = agent.do("write a hello world script")
print("Success:", r["success"])
