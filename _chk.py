import re, os
os.chdir(r'e:\Study\DataStructure\DSVis')
with open('dsvis/template.html', 'r', encoding='utf-8') as f:
    html = f.read()
matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
js = '\n'.join(matches)
with open('_temp_chk.js', 'w', encoding='utf-8') as f:
    f.write(js)

# verify key patterns
print('_zod present:', '_zod' in js)  # should be False (only in comment)
print('_def.type:', js.count("type:") )
print('typeName count:', js.count('typeName'))
print('coerce count:', js.count('coerce'))
