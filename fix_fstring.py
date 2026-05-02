# Fix ghost_v21.py f-string issues
import re

path = r'C:\Users\shenz\.openclaw\workspace\code-agent\ghost_v21.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The math calc template has f-strings with {c.xxx} that break Python string formatting
# Replace all f-string print statements in the _math_calc template

# Find and replace the math calc template section
old_math = 'print(f"2+3={c.add(2,3)} 10-4={c.sub(10,4)} 6*7={c.mul(6,7)}")'
new_math = 'print("2+3=" + str(c.add(2,3)) + " 10-4=" + str(c.sub(10,4)) + " 6*7=" + str(c.mul(6,7)))'

old_math2 = 'print(f"2^10={c.power(2,10)} sqrt(144)={c.sqrt(144)} 10!={c.fact(10)}")'
new_math2 = 'print("2^10=" + str(c.power(2,10)) + " sqrt(144)=" + str(c.sqrt(144)) + " 10!=" + str(c.fact(10)))'

old_math3 = 'print(f"fib(15)={c.fib(15)} is_prime(17)={c.is_prime(17)}")'
new_math3 = 'print("fib(15)=" + str(c.fib(15)) + " is_prime(17)=" + str(c.is_prime(17)))'

old_math4 = 'print(f"gcd(12,18)={c.gcd(12,18)} lcm(12,18)={c.lcm(12,18)}")'
new_math4 = 'print("gcd(12,18)=" + str(c.gcd(12,18)) + " lcm(12,18)=" + str(c.lcm(12,18)))'

content = content.replace(old_math, new_math)
content = content.replace(old_math2, new_math2)
content = content.replace(old_math3, new_math3)
content = content.replace(old_math4, new_math4)

# Also fix the data analysis template
old_data = 'print(f"  {k}: {v}")'
new_data = 'print("  " + str(k) + ": " + str(v))'
content = content.replace(old_data, new_data)

# Fix auto script template
old_auto = "print(f\"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行!\")"
new_auto = "print(\"[\" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + \"] 执行!\")"
content = content.replace(old_auto, new_auto)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! Fixed f-string issues.")
