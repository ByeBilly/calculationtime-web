# CalculationTime API - developer portal

Documentation site for the **CalculationTime API**, the developer-facing companion to [calculationtime.com](https://www.calculationtime.com).

The API provides time, date, geospatial, astronomy (including the Crux Sky Clock engine), finance, health and math calculations, plus public reference-data tables, over plain JSON. Everything is built around visible assumptions and repeatable methods.

- Main site and calculators: <https://www.calculationtime.com>
- Developer page and beta access: <https://www.calculationtime.com/developers/api/>
- API base URL: `https://api.calculationtime.com`
- Machine-readable contract: <https://api.calculationtime.com/openapi.json>

## What is in this repository

| Path | What it is |
|---|---|
| `index.html` | The landing page: a single self-contained file (inline CSS and about 30 lines of JavaScript, no build step, no external dependencies). It shows a live API status pill and a working "try it" call against the public reference-data endpoints. |
| `docs/api-guide.md` | The developer guide (source): base URL, authentication, public vs protected endpoints, rate limits, credits, errors, CORS and caching, reference data, a generated endpoint index, examples, and an explicit list of what is not documented yet. |
| `docs/api-guide.html` | The same guide rendered as a web page - this is what the portal links to, because GitHub Pages does not render plain `.md` files. Regenerate it after editing the Markdown: `pip install markdown && python3 build-docs.py`. |
| `build-docs.py` | Renders the guide to HTML (see above). |
| `.nojekyll` | Tells GitHub Pages to serve the files exactly as they are. |
| `README.md` | This file. |

## Deploying

It is plain static files, so it works on any static host (GitHub Pages, Vercel, Netlify, Cloudflare Pages, or any web server). Serve the repository root; there is nothing to build (the rendered guide is committed).

Preview locally:

```bash
python3 -m http.server 8080
# then open http://localhost:8080/
```

`index.html` links to the rendered `docs/api-guide.html`. The Markdown source stays alongside it, and GitHub itself renders `docs/api-guide.md` when browsing the repository.

## Accuracy policy

The portal only states what has been verified against the live service and its OpenAPI contract. When the contract does not say something (for example, request field names for most calculation endpoints, per-endpoint credit costs, or keyed rate limits), the guide says so rather than guessing. Please keep it that way:

- Do not add claims about pricing, uptime guarantees, "free" access or authentication schemes that the contract or the developer page does not support.
- Endpoint counts on the landing page and the endpoint index in the guide come from the OpenAPI contract at v0.1.0. When the contract changes, regenerate them.
- Reference-data row counts are as at dataset version 2026-09-21.

### Refreshing the endpoint index

```bash
curl -s https://api.calculationtime.com/openapi.json -o openapi.json
```

Then rebuild the "Endpoint index" section of `docs/api-guide.md` from the `paths` object (method, path, `summary`, and whether the operation lists `security`).

## Beta access

Beta API keys are issued privately by request: <https://www.calculationtime.com/developers/api/beta/>. Never commit a key to this repository.

## Roadmap items (not live)

Published request and response schemas for every calculation endpoint, self-service key requests with a usage dashboard and public pricing, and larger reference tables.
