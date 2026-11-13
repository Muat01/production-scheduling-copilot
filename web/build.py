"""Assemble the single-file web control room -> docs/index.html (GitHub Pages).

Run from the repo root:  python export_web.py && python web/build.py
"""
import os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")
os.makedirs(OUT, exist_ok=True)
rd = lambda f: open(os.path.join(SRC, f), encoding="utf-8").read()
css = rd("fonts.css") + "\n" + rd("style.css") + "\n" + rd("extra.css")
boot = """(function(){try{var q=new URLSearchParams(location.hash.slice(1)),th=q.get('th')||localStorage.getItem('psc_theme')||'system',
l=q.get('l')||localStorage.getItem('psc_lang')||'en';var dk=th=='dark'||(th=='system'&&matchMedia('(prefers-color-scheme: dark)').matches);
document.documentElement.dataset.theme=dk?'dark':'light';document.documentElement.lang=l;document.documentElement.dir=l=='ar'?'rtl':'ltr'}catch(e){document.documentElement.dataset.theme='dark'}})();"""
html = f"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Production Scheduling Copilot control room: plain-language re-planning, OR-Tools CP-SAT vs dispatching rules, disruption repair and benchmarks (simulated order books). Designed and built by Muatasem Hadi.">
<meta name="author" content="Muatasem Hadi">
<meta name="theme-color" content="#0B100E">
<title>Production Scheduling Copilot · Control Room</title>
<script>{boot}</script>
<style>{css}</style>
</head>
<body>
<div class="shell"><aside class="side" id="side"></aside><div class="main"><header class="top" id="top"></header><main class="content" id="app"></main></div></div>
<nav class="bnav" id="bnav" aria-label="Pages"></nav>
<div id="cmdk" class="cmdk" role="dialog" aria-modal="true"><div class="box"><input id="cmdq" autocomplete="off" spellcheck="false"><ul id="cmdl"></ul><div class="foot" id="cmdf"></div></div></div>
<div id="toast" role="status" aria-live="polite"></div>
<script>
{open(os.path.join(ROOT, "web", "data.js"), encoding="utf-8").read()}
{rd("strings.js")}
{rd("head.js")}
{rd("engine.js")}
{rd("charts.js")}
{rd("app.js")}
</script>
</body>
</html>"""
out = os.path.join(OUT, "index.html")
open(out, "w", encoding="utf-8").write(html)
print(out, round(len(html.encode()) / 1024), "KB")
