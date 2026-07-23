import re, os, subprocess, sys
os.chdir(r'e:\Study\DataStructure\DSVis')
with open('dsvis/template.html', 'r', encoding='utf-8') as f:
    html = f.read()
matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
js = '\n'.join(matches)
with open('_temp_chk.js', 'w', encoding='utf-8') as f:
    f.write(js)

result = subprocess.run(['node', '--check', '_temp_chk.js'], capture_output=True, text=True)
if result.returncode == 0:
    print("SYNTAX OK")
else:
    print("SYNTAX ERROR:", result.stderr[:500])

# Verify key markers
print('Object.defineProperty _zod:', js.count("Object.defineProperty(inner, '_zod'") + js.count("Object.defineProperty(schema, '_zod'"))
print('processJSONSchema:', js.count('processJSONSchema'))
print('target.type:', js.count('target.type'))
