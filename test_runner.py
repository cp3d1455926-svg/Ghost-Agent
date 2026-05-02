# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from code_agent import CodeAgent

agent = CodeAgent()

# Test 1
print("[T1] Basic:")
r = agent.write_and_run('print("hello world")', description="basic")
print("OK" if r['success'] else "FAIL")

# Test 2
print("")
print("[T2] Error:")
r = agent.write_and_run('prnt("typo")', description="error test")
print("OK" if r['success'] else "FAIL")
if not r['success']:
    print(agent.explain_error(r['stderr']))

# Test 3
print("")
print("[T3] Data:")
code3 = "data=[1,2,3,4,5]\nprint('avg=' + str(sum(data)/len(data)))"
r = agent.write_and_run(code3, description="data")
print("OK" if r['success'] else "FAIL")

# Test 4
print("")
print("[T4] Project scan:")
info = agent.get_project_info("C:\\Users\\shenz\\.openclaw\\workspace")
print("type=" + str(info.get('type')) + " files=" + str(info.get('total_files')))

print("")
print("Done: " + str(len(agent.history)) + " tasks")
