import re, os
os.chdir(r'e:\Study\DataStructure\DSVis')
with open('dsvis/template.html', 'r', encoding='utf-8') as f:
    html = f.read()
matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
js = '\n'.join(matches)
with open('_temp_chk.js', 'w', encoding='utf-8') as f:
    f.write(js)

# verify key patterns
print('ZodObject count:', js.count('ZodObject'))
print('_zod count:', js.count('_zod:'))
print('typeName count:', js.count('typeName:'))
print('page-agent.demo.js: ', 'autoInit=false' in html and 'showPanel=false' in html)
print('toolsCount defined:', 'toolsCount' in js)
