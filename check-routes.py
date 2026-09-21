#!/usr/bin/env python3
"""Keyless route check: does every protected route in data/openapi.json exist on the live API?

A route that exists answers 401 without a key. A 404 means the contract lists a route the running service does not serve.
Run it before every contract refresh:  python3 check-routes.py
Polite by design: one request every 1.2 s, well inside the public 60-per-minute limit.
"""
import json, pathlib, sys, time, urllib.request, urllib.error
API = "https://api.calculationtime.com"
oa = json.loads((pathlib.Path(__file__).parent / "data" / "openapi.json").read_text(encoding="utf-8"))
bad, seen = [], 0
for path, item in oa["paths"].items():
    if "{" in path or path.startswith("/v1/admin"):
        continue
    for method, op in item.items():
        if not isinstance(op, dict) or not op.get("security"):
            continue
        req = urllib.request.Request(API + path, method=method.upper(), data=b"{}" if method != "get" else None, headers={"Content-Type": "application/json"})
        try:
            code = urllib.request.urlopen(req, timeout=15).status
        except urllib.error.HTTPError as e:
            code = e.code
        seen += 1
        if code != 401:
            bad.append((code, method.upper(), path))
        time.sleep(1.2)
print(f"checked {seen} protected routes; {len(bad)} did not answer 401")
for b in bad:
    print("  ", *b)
sys.exit(1 if bad else 0)
