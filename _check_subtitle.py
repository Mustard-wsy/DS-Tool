import json, re, pathlib, tempfile, os
files = sorted(pathlib.Path(tempfile.gettempdir()).glob("tmp*.html"), key=os.path.getmtime, reverse=True)
html = files[0].read_text(encoding="utf-8")
c = html.count("showSubtitle")
subs = re.findall(r'"subtitle":"([^"]+)"', html)
print(f"subtitle occurrences: {c}")
print(f"subtitles: {subs[:5]}... ({len(subs)} total)")
