# CalculationTime API: free time, date and reference data

A free JSON API for local time, daylight saving, date maths, holidays, astronomy, unit conversion and
reference tables. No key, no sign-up: send a request and read the answer. Up to 60 requests a minute
from each address, and it can be called straight from a web page.

**Docs, a live console and every endpoint with a request you can copy:
[calculationtime.com/developers/api](https://www.calculationtime.com/developers/api/)**

## Try it

Local time for a place (London), with its offset and whether daylight saving is on:

```sh
curl 'https://api.calculationtime.com/v1/time?lat=51.5074&lon=-0.1278'
```

Days between two dates:

```sh
curl 'https://api.calculationtime.com/v1/date/difference?start=2026-01-01&end=2026-12-25'
# {"days":358,"inclusive_days":359,"weeks":51.14...}
```

A reference table, filtered:

```sh
curl 'https://api.calculationtime.com/v1/data/countries?q=japan&limit=1'
```

The full OpenAPI 3.1 contract: <https://api.calculationtime.com/openapi.json>

This repository used to host the docs on GitHub Pages; those pages now forward to calculationtime.com.
