# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ghost_agent import GhostAgent

agent = GhostAgent()

print("=" * 60)
print("Ghost Agent v1.1.0 Test")
print("=" * 60)

# Test 1: data analysis
print("\n--- Test 1: Data Analysis ---")
r1 = agent.do("写一个数据分析脚本")
print("Success:", r1["success"])
print("Rounds:", r1["rounds"])
if r1["output"]:
    print("Output:", r1["output"][:200])

# Test 2: math calculator
print("\n--- Test 2: Math Calculator ---")
r2 = agent.do("写一个数学计算器")
print("Success:", r2["success"])
print("Rounds:", r2["rounds"])
if r2["output"]:
    print("Output:", r2["output"][:200])

# Test 3: auto-fix (code with typo)
print("\n--- Test 3: Auto Fix ---")
from ghost_agent import CodeGenerator, Executor, SmartFixer
code = CodeGenerator.generate("hello world script")
# Inject a bug
code = code.replace("print", "prnt")
print("Injected bug: prnt instead of print")
result = Executor.run(code)
print("First run success:", result["success"])
if not result["success"]:
    new_code, desc, fixed = SmartFixer.fix(code, result["stderr"])
    print("Fixed:", fixed, "-", desc)
    if fixed:
        result2 = Executor.run(new_code)
        print("After fix success:", result2["success"])

print("\n" + "=" * 60)
print("All tests done!")
print("Stats:", agent.memory.data["stats"])
