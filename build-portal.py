#!/usr/bin/env python3
"""Build the portal's generated pages from data/openapi.json.

Needs: pip install markdown
Run:   python3 build-portal.py

Writes docs/api-guide.html, docs/reference/*.html, sitemap.xml and robots.txt, and
regenerates the endpoint index (section 10) inside docs/api-guide.md.

Refresh the contract first:  curl -s https://api.calculationtime.com/openapi.json -o data/openapi.json
"""
import html, json, pathlib, re, datetime, collections
import markdown

ROOT = pathlib.Path(__file__).parent
SITE = "https://byebilly.github.io/calculationtime-web"
API = "https://api.calculationtime.com"
TODAY = datetime.date.today().isoformat()
oa = json.loads((ROOT / "data" / "openapi.json").read_text(encoding="utf-8"))
EXAMPLES = json.loads((ROOT / "data" / "get-examples.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- contract model
AREAS = [
    ("service", "Service and status", "Public probes: health, status, the OpenAPI contract and a UTC clock.",
     "The service endpoints need no key. They tell you whether the API is up, what it exposes and what time the server believes it is. Use them for health checks and for discovering the contract.",
     lambda p: p in ("/", "/health", "/openapi.json", "/v1/status", "/v1/time/utc", "/v1/canary") or "/utility/" in p),
    ("reference-data", "Reference data", "Public JSON tables: countries, time zones, elements, constants, materials, HTTP status, MIME types, Unicode blocks, constellations, bright stars, meteor showers.",
     "Every reference table is a public GET that needs no key and sends open CORS headers, so a browser can read it directly. Each response carries dataset_version, source and count. Most tables accept q (text filter) and limit. The same tables also answer under /api/v1/data/... as a frontend alias.",
     lambda p: p.startswith("/v1/data/")),
    ("time-and-dates", "Time and dates", "Local time for a coordinate, date differences, date arithmetic, business days, ISO weeks, ages, epoch conversion and more.",
     "Date and time calculations over plain JSON. Local time takes a latitude and longitude; date routines take ISO dates and return explicit, inspectable results rather than a bare number.",
     lambda p: p.startswith("/v1/time") or p.startswith("/v1/date") or p.startswith("/v1/holidays")),
    ("geo", "Geo", "Great-circle distance, midpoint, bounding box and elevation for latitude and longitude points.",
     "Geospatial helpers that work from coordinates you supply. Distances are great-circle distances on a sphere; treat them as estimates, not survey-grade values.",
     lambda p: p.startswith("/v1/geo")),
    ("astronomy", "Astronomy and Crux clock", "Sun and moon position, twilight, sidereal time, Julian date, ephemeris, and the Crux Sky Clock engine.",
     "The astronomy endpoints power the Crux Sky Clock and the site's sky calculators. The Crux endpoints report the Southern Cross clock position for Parkes Observatory, calibrated with the hand zeroed at local midnight on 2026-03-31.",
     lambda p: p.startswith("/v1/astronomy") or p.startswith("/v1/solar")),
    ("finance", "Finance", "Loan amortization, simple and compound interest, ROI, CAGR, margin, markup, break-even, discounts and sales tax.",
     "Finance calculators that return the working, not just the answer. Amounts are decimal numbers you supply; check each example body for the field names.",
     lambda p: p.startswith("/v1/finance")),
    ("math-and-statistics", "Math and statistics", "Quadratics, triangles, circles, proportions, logarithms, exponents, percentages, combinatorics and statistics summaries.",
     "Pure-maths endpoints. The request examples show the exact field names; results are computed with standard double-precision arithmetic, so display rounding is your decision.",
     lambda p: p.startswith("/v1/math") or p.startswith("/v1/stats")),
    ("health", "Health", "BMI, BMR, TDEE, macro splits and pace, with the formula named in the result.",
     "Health calculators use published formulas and state which one they used. They are aids for planning, not medical advice.",
     lambda p: p.startswith("/v1/health")),
    ("payroll-and-trades", "Payroll and trades", "Decimal hours, job margin, mileage claims, tool depreciation, invoice aging and VAT summaries.",
     "Small-business helpers for hours, margins, mileage, depreciation and invoices. Tax rules differ by jurisdiction; check the assumptions in each response before you rely on a figure.",
     lambda p: p.startswith("/v1/payroll") or p.startswith("/v1/tradie")),
    ("account", "Account", "Credit balance, usage and plan limits for the key you call with.",
     "Account endpoints report on the key you send. They are the way to check your balance and limits before you run a large job.",
     lambda p: p.startswith("/v1/account")),
]

def area_of(path):
    path = path[4:] if path.startswith("/api/v1/") else path  # /api/v1/x is grouped like /v1/x
    for slug, *_rest, pred in AREAS:
        if pred(path):
            return slug
    return None

def ops():
    out = []
    for path, item in oa["paths"].items():
        twin = path[4:] if path.startswith("/api/v1/") else None
        if (twin and twin in oa["paths"]) or path.startswith("/v1/admin") or path.startswith("/v1/observatory"):
            continue  # aliases of an existing /v1 route, admin and private-sharing routes are not part of the public reference
        for method, op in item.items():
            if not isinstance(op, dict):
                continue
            out.append(dict(method=method.upper(), path=path, op=op, area=area_of(path)))
    return out

OPS = ops()
by_area = collections.defaultdict(list)
for o in OPS:
    by_area[o["area"]].append(o)
assert None not in by_area, "Unmapped paths need an AREAS rule: " + ", ".join(x["path"] for x in by_area[None])

def access(op):
    return "key" if op.get("security") else "public"

def cost(op):
    c = op.get("x-credit-cost")
    return f"{c} credit{'s' if c != 1 else ''}" if c is not None else ("free" if op.get("security") else "-")

def curl_for(o):
    path, method, op = o["path"], o["method"], o["op"]
    key = " \\\n  -H 'X-API-Key: YOUR_KEY'" if op.get("security") else ""
    if method == "GET":
        ex = EXAMPLES.get(path)
        if ex:
            return f"curl '{API}{ex}'{key}"
        params = [p["name"] for p in op.get("parameters", []) if p.get("in") == "query"]
        q = ("?" + "&".join(f"{n}={n.upper()}" for n in params)) if params else ""
        return f"curl '{API}{path}{q}'{key}"
    body = op["requestBody"]["content"]["application/json"].get("example")
    data = json.dumps(body, separators=(",", ":")) if body is not None else "{}"
    return f"curl -X POST '{API}{path}'{key} \\\n  -H 'Content-Type: application/json' \\\n  -d '{data}'"

def slug_of(o):
    return (o["method"] + "-" + o["path"]).lower().replace("/", "-").replace("{", "").replace("}", "").strip("-")

# ---------------------------------------------------------------- page shell
CSS = """
  :root { --bg:#f7f1e4; --panel:#fff; --ink:#14110c; --muted:#5a5245; --line:#d9ccb0; --brand:#0b0d14; --gold:#c98b2c; --gold-soft:#e5b65f; --code-bg:#0d1018; --code-ink:#f3ead6; --radius:12px; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0b0d14; --panel:#12151f; --ink:#f4ecd9; --muted:#b9ae98; --line:#2b2f3d; --code-bg:#07080d; } }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }
  header { background:var(--brand); color:#f4ecd9; }
  header .wrap { display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center; justify-content:space-between; padding:14px 0; }
  .wrap { width:min(880px, 100% - 32px); margin-inline:auto; }
  header a { color:inherit; text-decoration:none; font-size:14px; margin-left:16px; }
  header a.logo { margin:0; font:700 20px Georgia,"Times New Roman",serif; }
  header a.logo span { color:var(--gold-soft); }
  header a:hover { text-decoration:underline; }
  main { padding:36px 0 64px; }
  h1,h2,h3 { font-family:Georgia,"Times New Roman",serif; line-height:1.15; }
  h1 { font-size:clamp(30px,5vw,44px); margin:0 0 12px; }
  h2 { font-size:28px; margin:44px 0 10px; padding-top:20px; border-top:1px solid var(--line); }
  h3 { font-size:20px; margin:28px 0 6px; }
  h3 code { font-size:.85em; }
  a { color:var(--gold); }
  code { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.9em; background:rgba(201,139,44,.12); padding:1px 5px; border-radius:5px; }
  pre { margin:12px 0; padding:16px 18px; overflow-x:auto; background:var(--code-bg); color:var(--code-ink); border-radius:var(--radius); font-size:13.5px; line-height:1.55; }
  pre code { background:none; padding:0; color:inherit; }
  .scroll { overflow-x:auto; margin:14px 0; }
  table { width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); font-size:14.5px; }
  th,td { padding:9px 12px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }
  th { font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }
  details.toc { margin:18px 0 8px; padding:12px 18px; background:var(--panel); border:1px solid var(--line); border-radius:var(--radius); }
  details.toc summary { cursor:pointer; font-weight:800; }
  .toc ul { margin:8px 0 0; padding-left:20px; }
  blockquote { margin:14px 0; padding:10px 16px; border-left:4px solid var(--gold); background:rgba(201,139,44,.09); }
  .meta { color:var(--muted); font-size:14px; margin:0 0 6px; }
  .pill { display:inline-block; padding:1px 9px; border-radius:99px; font-size:12px; font-weight:700; border:1px solid var(--line); background:var(--panel); margin-right:6px; }
  .crumbs { font-size:14px; color:var(--muted); margin:0 0 10px; }
  .areas { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:14px; margin:18px 0; padding:0; list-style:none; }
  .areas a { display:block; height:100%; padding:16px; background:var(--panel); border:1px solid var(--line); border-radius:var(--radius); text-decoration:none; color:inherit; }
  .areas a:hover { border-color:var(--gold); }
  .areas strong { display:block; font:700 18px Georgia,serif; }
  .areas span { font-size:14px; color:var(--muted); }
  li, p, td { overflow-wrap:anywhere; }
  footer { background:var(--brand); color:#d8cdbd; padding:24px 0; font-size:14px; }
  footer a { color:var(--gold-soft); }
"""

def shell(title, desc, body, depth, path, extra_head=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="{SITE}/{path}">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:type" content="website">
<style>{CSS}</style>
{extra_head}</head>
<body>
<header><div class="wrap">
  <a class="logo" href="{up}index.html">Calculation<span>Time</span> API</a>
  <nav aria-label="Primary"><a href="{up}docs/api-guide.html">Guide</a><a href="{up}docs/reference/">Endpoint reference</a><a href="{API}/openapi.json">OpenAPI</a><a href="https://www.calculationtime.com/developers/api/beta/">Request beta access</a><a href="https://www.calculationtime.com">Main site</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">Contract v{oa['info']['version']} &middot; built {TODAY} &middot; <a href="{up}index.html">Portal home</a> &middot; <a href="https://www.calculationtime.com">calculationtime.com</a> &middot; <a href="https://github.com/ByeBilly/calculationtime-web">Source on GitHub</a></div></footer>
</body>
</html>
"""

def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>\n"

# ---------------------------------------------------------------- reference pages
ref_dir = ROOT / "docs" / "reference"
ref_dir.mkdir(parents=True, exist_ok=True)
for old in ref_dir.glob("*.html"):
    old.unlink()

STATUS_TEXT = {"400": "invalid input", "401": "missing or invalid key", "402": "credits exhausted", "403": "account suspended or trial expired", "429": "rate limited"}

for slug, title, short, intro, _pred in AREAS:
    items = by_area[slug]
    rows = "".join(
        f"<tr><td>{o['method']}</td><td><a href=\"#{slug_of(o)}\"><code>{html.escape(o['path'])}</code></a></td><td>{html.escape(o['op'].get('summary',''))}</td><td>{access(o['op'])}</td><td>{cost(o['op'])}</td></tr>"
        for o in items)
    blocks = []
    for o in items:
        op = o["op"]
        codes = [c for c in op.get("responses", {}) if c != "200"]
        errs = ", ".join(f"<code>{c}</code> {STATUS_TEXT.get(c, op['responses'][c].get('description',''))}" for c in codes)
        params = [p for p in op.get("parameters", [])]
        ptxt = ""
        if params:
            ptxt = "<p><strong>Parameters:</strong> " + ", ".join(
                f"<code>{p['name']}</code> ({p['in']}{', required' if p.get('required') else ''})" for p in params) + "</p>"
        blocks.append(f"""<h3 id="{slug_of(o)}"><code>{o['method']} {html.escape(o['path'])}</code></h3>
<p>{html.escape(op.get('summary',''))}.</p>
<p class="meta"><span class="pill">{'API key required' if op.get('security') else 'Public, no key'}</span><span class="pill">{cost(op)}</span></p>
{ptxt}<pre><code>{html.escape(curl_for(o))}</code></pre>
{('<p class="meta">Other responses in the contract: ' + errs + '.</p>') if errs and op.get('security') else ''}""")
    body = f"""<p class="crumbs"><a href="../../index.html">Portal</a> / <a href="./">Endpoint reference</a> / {html.escape(title)}</p>
<h1>{html.escape(title)} endpoints</h1>
<p>{html.escape(intro)}</p>
<p class="meta">{len(items)} operations &middot; contract v{oa['info']['version']} &middot; base URL <code>{API}</code></p>
<div class="scroll"><table><thead><tr><th>Method</th><th>Path</th><th>What it does</th><th>Access</th><th>Cost</th></tr></thead><tbody>{rows}</tbody></table></div>
<blockquote>Request bodies below are the examples published in the API's OpenAPI contract. The contract declares body fields only as free-form JSON, so it does not say which fields are required or optional; treat each example as a known-good shape and read the result's fields. Replace <code>YOUR_KEY</code> with a beta key; never put a key in public code. Endpoints marked public work as shown with no key.</blockquote>
{''.join(blocks)}
<p><a href="../api-guide.html">Read the full guide</a> for authentication, limits, credits and errors, or <a href="./">browse every area</a>.</p>"""
    ld = jsonld({"@context": "https://schema.org", "@type": "TechArticle", "headline": f"{title} endpoints - CalculationTime API reference",
                 "description": short, "dateModified": TODAY, "inLanguage": "en",
                 "publisher": {"@type": "Organization", "name": "CalculationTime", "url": "https://www.calculationtime.com"}})
    (ref_dir / f"{slug}.html").write_text(
        shell(f"{title} API endpoints - CalculationTime API reference", short, body, 2, f"docs/reference/{slug}.html", ld),
        encoding="utf-8")

cards = "".join(
    f'<li><a href="{slug}.html"><strong>{html.escape(t)}</strong><span>{len(by_area[slug])} operations. {html.escape(s)}</span></a></li>'
    for slug, t, s, _i, _p in AREAS)
idx_body = f"""<p class="crumbs"><a href="../../index.html">Portal</a> / Endpoint reference</p>
<h1>CalculationTime API endpoint reference</h1>
<p>Every documented operation in the CalculationTime API contract (v{oa['info']['version']}), grouped by area, with a copy-paste request for each. {len(OPS)} operations across {len(AREAS)} areas. Reference data and service probes are public; everything else needs a beta key.</p>
<ul class="areas">{cards}</ul>
<p>New to the API? Start with the <a href="../api-guide.html">developer guide</a>. Administrative and private-sharing routes are deliberately left out of this reference.</p>"""
(ref_dir / "index.html").write_text(
    shell("CalculationTime API endpoint reference", f"All {len(OPS)} documented operations of the CalculationTime API by area, with copy-paste requests: time, dates, astronomy, finance, maths, health and reference data.", idx_body, 2, "docs/reference/"),
    encoding="utf-8")

# ---------------------------------------------------------------- guide (markdown) with generated index
guide_path = ROOT / "docs" / "api-guide.md"
md = guide_path.read_text(encoding="utf-8")
parts = re.split(r"(?m)^(?=## \d+\. )", md)
head, secs = parts[0], parts[1:]
def sec(n):
    for i, s in enumerate(secs):
        if s.startswith(f"## {n}. "):
            return i
    raise KeyError(n)

lines = ["## 10. Endpoint index", "",
         f"Generated from the OpenAPI contract (v{oa['info']['version']}) by `build-portal.py`. \"public\" means no key; \"key\" means an API key is required. Each area has its own reference page with a copy-paste request per endpoint. Administrative and private-sharing routes are omitted, and the `/api/v1/data/...` aliases are covered in section 9.", ""]
for slug, title, short, _i, _p in AREAS:
    lines += [f"### [{title}](reference/{slug}.html)", "", "| Method | Path | What it does | Access | Cost |", "|---|---|---|---|---|"]
    for o in by_area[slug]:
        lines.append(f"| {o['method']} | [`{o['path']}`](reference/{slug}.html#{slug_of(o)}) | {o['op'].get('summary','')} | {access(o['op'])} | {cost(o['op'])} |")
    lines.append("")
secs[sec(10)] = "\n".join(lines) + "\n"
guide_path.write_text(head + "".join(secs), encoding="utf-8")

# ---------------------------------------------------------------- render guide
gmd = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"], extension_configs={"toc": {"toc_depth": "2-3"}})
body = gmd.convert(guide_path.read_text(encoding="utf-8"))
body = body.replace("<table>", '<div class="scroll"><table>').replace("</table>", "</table></div>")
gbody = f'<details class="toc"><summary>On this page</summary>{gmd.toc}</details>\n{body}'
(ROOT / "docs" / "api-guide.html").write_text(
    shell("CalculationTime API guide: authentication, limits, credits and examples",
          "Developer guide for the CalculationTime API: authentication, rate limits, credits, errors, reference data, worked examples and the full endpoint index.",
          gbody, 1, "docs/api-guide.html",
          jsonld({"@context": "https://schema.org", "@type": "TechArticle", "headline": "CalculationTime API guide", "dateModified": TODAY, "inLanguage": "en",
                  "publisher": {"@type": "Organization", "name": "CalculationTime", "url": "https://www.calculationtime.com"}})),
    encoding="utf-8")

# ---------------------------------------------------------------- sitemap and robots
urls = ["", "docs/api-guide.html", "docs/reference/"] + [f"docs/reference/{s}.html" for s, *_ in AREAS]
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{SITE}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

print("operations:", len(OPS), {s: len(v) for s, v in by_area.items()})
print("pages:", len(urls))
