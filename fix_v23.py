path = r'C:\Users\shenz\.openclaw\workspace\code-agent\ghost_v23.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = []
for line in lines:
    # Fix the comparison in _write_full_article
    if 'if template = self.TEMPLATES[' in line and 'list' in line:
        line = line.replace('if template = ', 'if template == ')
    if 'if template = self.TEMPLATES[' in line and 'tutorial' in line:
        line = line.replace('if template = ', 'if template == ')
    fixed.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(fixed)
print('Fixed ' + str(len(fixed)) + ' lines')
