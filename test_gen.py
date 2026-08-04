"""
Generate a test HTML from an algorithm file using dsvis.
"""
import sys
sys.path.insert(0, r'e:\Study\DataStructure\DSVis')
import os
os.chdir(r'e:\Study\DataStructure\DSVis')

# We need steps and source_lines. Let's use the dsvis runtime to capture steps.
from dsvis.runtime.auto import capture_algorithm

# Try capturing gcd.py
algo_path = r'e:\Study\DataStructure\DSVis\gcd.py'
with open(algo_path, 'r', encoding='utf-8') as f:
    source = f.read()
source_lines = source.split('\n')

# Use the capture mechanism
try:
    result = capture_algorithm(algo_path)
    steps = result.get('steps', [])
    title = result.get('title', 'GCD Algorithm')
except Exception as e:
    print(f"Capture failed: {e}")
    # Fallback: generate minimal test
    steps = []
    title = 'Test'

from dsvis.card_renderer import render_debugger
html = render_debugger(steps, source_lines, title=title)

out_path = r'e:\Study\DataStructure\DSVis\test_output.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated: {out_path} ({len(html)} chars)")
print(f"Has PageAgent CDN: {'page-agent.demo.js' in html}")
print(f"Has DSVIS_ALGO placeholder: {'__DSVIS_ALGO__' in html}")
print(f"Has buildZodSchema: {'buildZodSchema' in html}")
print(f"Has _zod.run: {'_zod.run' in html}")
print(f"Has $ZodType: {'$ZodType' in html}")
