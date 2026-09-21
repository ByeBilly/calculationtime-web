#!/usr/bin/env python3
"""Render docs/api-guide.md to docs/api-guide.html (needs: pip install markdown)."""
import re, markdown, pathlib

root = pathlib.Path(__file__).parent
src = (root / "docs" / "api-guide.md").read_text(encoding="utf-8")
md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"], extension_configs={"toc": {"toc_depth": "2-3"}})
body = md.convert(src)
body = re.sub(r"<table>", '<div class="scroll"><table>', body)
body = body.replace("</table>", "</table></div>")
toc = md.toc

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CalculationTime API guide</title>
<meta name="description" content="Developer guide for the CalculationTime API: authentication, limits, credits, reference data, examples and the full endpoint index.">
<style>
  :root {{ --bg:#f7f1e4; --panel:#fff; --ink:#14110c; --muted:#5a5245; --line:#d9ccb0; --brand:#0b0d14; --gold:#c98b2c; --gold-soft:#e5b65f; --code-bg:#0d1018; --code-ink:#f3ead6; --radius:12px; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg:#0b0d14; --panel:#12151f; --ink:#f4ecd9; --muted:#b9ae98; --line:#2b2f3d; --code-bg:#07080d; }} }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }}
  header {{ background:var(--brand); color:#f4ecd9; }}
  header .wrap {{ display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center; justify-content:space-between; padding:14px 0; }}
  .wrap {{ width:min(880px, 100% - 32px); margin-inline:auto; }}
  header a {{ color:inherit; text-decoration:none; font-size:14px; margin-left:16px; }}
  header a.logo {{ margin:0; font:700 20px Georgia,"Times New Roman",serif; }}
  header a.logo span {{ color:var(--gold-soft); }}
  header a:hover {{ text-decoration:underline; }}
  main {{ padding:36px 0 64px; }}
  h1,h2,h3 {{ font-family:Georgia,"Times New Roman",serif; line-height:1.15; }}
  h1 {{ font-size:clamp(32px,5vw,46px); margin:0 0 12px; }}
  h2 {{ font-size:28px; margin:44px 0 10px; padding-top:20px; border-top:1px solid var(--line); }}
  h3 {{ font-size:21px; margin:28px 0 8px; }}
  a {{ color:var(--gold); }}
  code {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.9em; background:rgba(201,139,44,.12); padding:1px 5px; border-radius:5px; }}
  pre {{ margin:14px 0; padding:16px 18px; overflow-x:auto; background:var(--code-bg); color:var(--code-ink); border-radius:var(--radius); font-size:13.5px; line-height:1.55; }}
  pre code {{ background:none; padding:0; color:inherit; }}
  .scroll {{ overflow-x:auto; margin:14px 0; }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); font-size:14.5px; }}
  th,td {{ padding:9px 12px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }}
  details.toc {{ margin:18px 0 8px; padding:12px 18px; background:var(--panel); border:1px solid var(--line); border-radius:var(--radius); }}
  details.toc summary {{ cursor:pointer; font-weight:800; }}
  .toc ul {{ margin:8px 0 0; padding-left:20px; }}
  blockquote {{ margin:14px 0; padding:10px 16px; border-left:4px solid var(--gold); background:rgba(201,139,44,.09); }}
  footer {{ background:var(--brand); color:#d8cdbd; padding:24px 0; font-size:14px; }}
  footer a {{ color:var(--gold-soft); }}
</style>
</head>
<body>
<header><div class="wrap">
  <a class="logo" href="../index.html">Calculation<span>Time</span> API</a>
  <nav aria-label="Primary"><a href="../index.html">Portal home</a><a href="https://api.calculationtime.com/openapi.json">OpenAPI</a><a href="https://www.calculationtime.com/developers/api/beta/">Request beta access</a><a href="https://www.calculationtime.com">Main site</a></nav>
</div></header>
<main><div class="wrap">
<details class="toc"><summary>On this page</summary>{toc}</details>
{body}
</div></main>
<footer><div class="wrap">Source: <a href="api-guide.md">api-guide.md</a> &middot; <a href="../index.html">Portal home</a> &middot; <a href="https://www.calculationtime.com">calculationtime.com</a></div></footer>
</body>
</html>
"""
(root / "docs" / "api-guide.html").write_text(page, encoding="utf-8")
print("wrote docs/api-guide.html", len(page), "bytes")
