# CalculationTime API guide

Reliable time, date, geospatial, astronomy, finance, health and math calculations, plus public reference-data tables, over a plain JSON API.

This guide describes the API **as it is today (contract v0.1.0, beta)**. Everything here was checked against the live service and its OpenAPI contract on 2026-09-21. Where something is not documented or not yet available, the guide says so instead of guessing. The authoritative machine-readable contract is always <https://api.calculationtime.com/openapi.json>, and the service itself serves Markdown documentation at <https://api.calculationtime.com/>.

- Main site: <https://www.calculationtime.com>
- Developer page and beta access: <https://www.calculationtime.com/developers/api/>
- Live status: <https://www.calculationtime.com/developers/api/status/>

## 1. Base URL and versioning

```text
https://api.calculationtime.com
```

Endpoints are versioned in the path (`/v1/...`). The reference-data endpoints are also available under an `/api/v1/data/...` alias with identical behaviour. All requests use HTTPS. Requests and responses are JSON (`Content-Type: application/json`).

## 2. Quickstart

Public call, no key:

```bash
curl 'https://api.calculationtime.com/v1/data/http-status?q=teapot'
```

```json
{"dataset_version":"2026-09-21","source":"node_http_status_codes","count":1,"data":[{"code":418,"phrase":"I'm a Teapot","class":"4xx","category":"client_error"}]}
```

Authenticated call (requires a beta key, see section 3):

```bash
curl 'https://api.calculationtime.com/v1/account/credits' \
  -H 'X-API-Key: YOUR_KEY'
```

JavaScript:

```js
const res = await fetch('https://api.calculationtime.com/v1/data/stars/bright?q=crux');
const { dataset_version, count, data } = await res.json();
```

## 3. Authentication

Endpoints marked "public" below need no credentials. Every other endpoint needs an API key.

| Scheme | How to send it | Notes |
|---|---|---|
| API key | Header `X-API-Key: YOUR_KEY` | The scheme used in all of CalculationTime's own examples. Keys look like `ct_live_...`. |
| Bearer token | Header `Authorization: Bearer YOUR_KEY` | Declared as `BearerAuth` in the OpenAPI contract. Prefer `X-API-Key`, which the published examples use. |

A missing or invalid key returns:

```http
HTTP/1.1 401 Unauthorized
{"error":{"code":"unauthorized","message":"A valid API key is required"}}
```

**Getting a key.** Beta keys are issued privately, by request, at <https://www.calculationtime.com/developers/api/beta/>. There is no self-service signup yet.

**Keep keys secret.** Never put a key in public web pages, mobile app bundles or client-side code (all of which anyone can read). Call the API from a server you control, or use it only from tooling you own. CalculationTime's examples never include a real key.

## 4. Public and protected endpoints

| Public (no key) | Protected (key required) |
|---|---|
| `GET /` (Markdown docs), `GET /health`, `GET /openapi.json`, `GET /v1/status`, `GET /v1/time/utc`, `GET /api/v1/utility/tagline`, and all eleven `/v1/data/...` reference tables | Local time, date, holiday, geo, solar and astronomy calculations, finance, health, math, statistics, payroll and trades calculators, and the account endpoints |

The full list is in section 10.

## 5. Rate limits

Normal limited responses include rate-limit headers. Observed on the public tier on 2026-09-21:

| Header | Meaning | Observed |
|---|---|---|
| `x-ratelimit-limit` | Requests allowed in the current window | `60` |
| `x-ratelimit-remaining` | Requests left in the window | counts down from 59 |
| `x-ratelimit-reset` | When the window resets, as **Unix epoch seconds** | about 60 seconds after the first request of a window |

So the public tier behaves as roughly **60 requests per minute**. Keyed customers have plan-specific limits: call `GET /v1/account/limits` to see yours, including documented batch limits.

When you exceed a limit the contract lists `429 Too Many Requests`. Back off until `x-ratelimit-reset`, and add jitter if several workers share a key. Do not retry in a tight loop.

## 6. Credits

Protected calculation endpoints are credit-metered. The live OpenAPI contract exposes known per-route costs as `x-credit-cost`. Common astronomy costs:

| Endpoint | Credits per call |
|---|---|
| `POST /v1/astronomy/crux-midnight` | 2 (regardless of how many days are requested) |
| `POST /v1/astronomy/crux-hourly` | 5 (all 24 hours of the date) |
| `POST /v1/astronomy/crux-current` | 2 |
| `GET /v1/astronomy/ephemeris` | 1 |
| Other phase-one astronomy POST routes | 1 each |

Check the live OpenAPI contract for exact per-endpoint costs before building billing displays. Check your balance with `GET /v1/account/credits` and your usage with `GET /v1/account/usage`. The contract also lists `402` as a possible response, consistent with a credit or payment condition.

## 7. Responses, errors and status codes

**Reference data** responses share one envelope:

```json
{ "dataset_version": "2026-09-21", "source": "curated_bright_star_reference", "count": 20, "data": [ ... ] }
```

`count` is the number of rows returned (after any `q`/`limit` filtering). The timezone dataset also includes an `at` timestamp because offsets depend on the moment of the request.

**Errors** use one envelope:

```json
{ "error": { "code": "not_found", "message": "Endpoint not found" } }
```

Status codes documented in the contract for protected endpoints: `200`, `400` (bad request), `401` (missing/invalid key), `402`, `403` (forbidden), `429` (rate limited). Unknown routes return `404`. Handle unknown codes generically.

## 8. CORS and caching

The API allows any origin (`access-control-allow-origin: *`) for `GET`, `POST` and `OPTIONS`, and allows the request headers `Authorization`, `Content-Type`, `X-API-Key` and `X-Admin-Key`. Open CORS lets browsers read **public** endpoints directly; it is not a reason to expose a private key in browser code (see section 3).

Caching headers as observed: reference data is sent with `cache-control: private, max-age=2592000` (30 days, with stale-while-revalidate), timezones with `max-age=86400` (24 hours), and status/health with `no-store`. Reference data changes rarely, so cache it locally and key your cache on `dataset_version`.

## 9. Reference data (public)

All endpoints are `GET`, need no key and return the envelope from section 7. Query parameters are listed below the table. Row counts and versions below are as at 2026-09-21.

| Endpoint | Rows | Source named in the response | Notes |
|---|---|---|---|
| `/v1/data/countries` | 250 | `world_countries_package` | Names, ISO alpha-2/alpha-3/numeric codes, capitals, dialing codes |
| `/v1/data/timezones` | 418 | `node_icu_iana_tzdb` | IANA zones with `current_utc_offset`, `offset_minutes`, `observes_dst_now` (see the note below on what this flag means) |
| `/v1/data/elements` | 118 | `periodic_table_package` | Atomic number, symbol, name, atomic mass, electron configuration and more |
| `/v1/data/constants` | 10 | `curated_codified_constants` | Small curated set, each with unit and note |
| `/v1/data/materials/density` | 33 | `curated_engineering_density_reference` | Typical engineering densities in kg/m3 (no thermal or mechanical properties) |
| `/v1/data/http-status` | 63 | `node_http_status_codes` | Code, phrase, class, category (no descriptions) |
| `/v1/data/mime-types` | 2,522 | `mime_db_package` | Type, source, charset, compressible flag, extensions (about 290 KB; fetch once and cache) |
| `/v1/data/unicode-blocks` | 23 | `curated_unicode_block_reference` | A **subset** of Unicode blocks, not the full list |
| `/v1/data/constellations` | 88 | `iau_88_constellation_reference` | Names, genitives, abbreviations, quadrants |
| `/v1/data/stars/bright` | 20 | `curated_bright_star_reference` | Right ascension (hours), declination (degrees), apparent magnitude, spectral type, constellation |
| `/v1/data/meteor-showers` | 10 | `curated_major_meteor_shower_reference` | Peak dates, active window, zenithal hourly rate, radiant constellation |

### Query parameters

| Parameter | Applies to | Effect | Verified |
|---|---|---|---|
| `q` | most datasets | Case-insensitive text filter | `?q=teapot`, `?q=crux`, `?q=Australia/Sydney` |
| `limit` | most datasets | Cap the number of rows | `stars/bright?limit=3` returns 3 |
| `extension` | `/v1/data/mime-types` | Match one file extension | `?extension=json` returns `application/json` |
| `at` | `/v1/data/timezones` | ISO timestamp at which offsets are computed (default: now) | Sydney: `UTC+11:00` at 2026-01-15, `UTC+10:00` at 2026-07-15 |

Every dataset is also served under `/api/v1/data/...` with identical behaviour (for example `/api/v1/data/http-status?q=429`). Both the `/v1/data/...` routes and the `/api/v1/data/...` compatibility aliases are present in the live OpenAPI contract.

**Read `observes_dst_now` carefully.** In the timezone dataset this flag is `true` for any zone that uses daylight saving at all - it stayed `true` for `Europe/London` in January (offset `UTC+00:00`) and for `Australia/Sydney` in July (offset `UTC+10:00`) - so it does **not** tell you whether DST is in force at the requested time. To find out, compare `offset_minutes` at different `at` values, or use the standard offset for the zone.

Filtering example:

```bash
curl 'https://api.calculationtime.com/v1/data/stars/bright?q=crux'
```

```json
{"dataset_version":"2026-09-21","source":"curated_bright_star_reference","count":2,"data":[{"name":"Acrux","designation":"Alpha Crucis","right_ascension_hours":12.4433,"declination_degrees":-63.0991,"apparent_magnitude":0.76,"spectral_type":"B0.5IV","constellation":"Crux"}, ...]}
```

Several tables are curated subsets rather than complete catalogues. Each response names its `source`; treat the data as a reference aid and check a primary source (IANA, unicode.org, NIST, IAU) for anything critical.

## 10. Endpoint index

Generated from the live OpenAPI contract (v0.1.0). "public" means no key; "key" means an API key is required. This customer-facing index omits administrative routes, private-sharing routes, and duplicate `/api/v1/data/...` compatibility aliases; the live contract currently exposes 122 unique paths.

### Public service and utility

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/` | Markdown API documentation | public |
| GET | `/health` | Low-level service health | public |
| GET | `/openapi.json` | OpenAPI contract for live routes | public |
| GET | `/v1/status` | Public measured service status and endpoint inventory | public |
| GET | `/v1/time/utc` | Current UTC timestamp and clock-model metadata | public |
| GET | `/api/v1/utility/tagline` | Deterministic daily CalculationTime tagline | public |

### Reference data (public)

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/v1/data/countries` | Country reference table with capitals, ISO codes, dialing codes, and currencies | public |
| GET | `/v1/data/timezones` | IANA timezone reference with current UTC offsets and DST status | public |
| GET | `/v1/data/elements` | Periodic table reference values | public |
| GET | `/v1/data/constants` | Physical and mathematical constants reference table | public |
| GET | `/v1/data/materials/density` | Common material density reference table | public |
| GET | `/v1/data/http-status` | HTTP status code directory | public |
| GET | `/v1/data/mime-types` | MIME type and extension reference table | public |
| GET | `/v1/data/unicode-blocks` | Unicode block range reference table | public |
| GET | `/v1/data/constellations` | IAU constellation names, genitives, abbreviations, and quadrants | public |
| GET | `/v1/data/stars/bright` | Bright star reference table | public |
| GET | `/v1/data/meteor-showers` | Major annual meteor shower reference table | public |

### Time and dates

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/v1/time` | Get local time for one coordinate | key |
| POST | `/v1/time/batch` | Get local time for up to 100 coordinates | key |
| GET | `/v1/date/difference` | Calendar day difference | key |
| POST | `/v1/date/difference/batch` | Batch calendar day differences | key |
| GET | `/v1/date/add` | Add calendar units to a date | key |
| POST | `/v1/date/business-days` | Business-day count with supplied holidays | key |
| POST | `/v1/date/business-days/jurisdiction` | Business-day count for a supported jurisdiction | key |
| POST | `/v1/date/business-days-add` | Add or subtract configurable business days | key |
| POST | `/v1/date/iso-week` | ISO week number, week-year, and weekday | key |
| POST | `/v1/date/age-breakdown` | Exact age duration breakdown from birth date to timestamp | key |
| POST | `/v1/date/countdown-precise` | Precise calendar delta between timestamps | key |
| POST | `/v1/date/epoch-converter` | Unix epoch seconds or milliseconds to ISO/RFC strings | key |
| POST | `/v1/date/quarter-calculator` | Calendar and fiscal quarter with progress percentage | key |
| POST | `/v1/date/leap-year-check` | Gregorian and Julian leap-year proof check | key |
| POST | `/v1/date/days-in-month` | Days in a Gregorian month | key |
| POST | `/v1/date/timezone-offset` | Fixed UTC offset conversion without DST lookup | key |
| POST | `/v1/date/calendar-range` | Generate a deterministic date range with weekday and ISO week facts | key |

### Holidays and business days

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/v1/holidays` | Holidays for a jurisdiction and year | key |
| GET | `/v1/holidays/next` | Next holiday for a jurisdiction | key |
| GET | `/v1/holidays/is-business-day` | Business-day check for one date | key |

### Geospatial

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/v1/geo/distance` | Distance between two coordinates | key |
| POST | `/v1/geo/distance/batch` | Batch distance calculations | key |
| GET | `/v1/geo/midpoint` | Midpoint between two coordinates | key |
| GET | `/v1/geo/bounding-box` | Bounding box around a coordinate | key |
| GET | `/v1/geo/elevation` | Elevation for one coordinate | key |
| GET | `/v1/geo/nearby` | Nearby stored geo points | key |

### Solar and astronomy

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/v1/solar/position` | Solar position for date and coordinate | key |
| GET | `/v1/astronomy/ephemeris` | Astronomy ephemeris for a date | key |
| POST | `/v1/astronomy/crux-midnight` | Crux clock hand midnight sidereal positions from Parkes Observatory calibration | key |
| POST | `/v1/astronomy/crux-hourly` | Crux clock hand hourly sidereal breakdown for one local date | key |
| POST | `/v1/astronomy/crux-current` | Current Crux clock hand position and Parkes alignment delta | key |
| POST | `/v1/astronomy/solar-noon` | Solar transit/noon timestamp for a coordinate and date | key |
| POST | `/v1/astronomy/equinox-solstice` | Equinox and solstice timestamps for a year | key |
| POST | `/v1/astronomy/moon-phase` | Moon illumination, age, and phase name for a timestamp | key |
| POST | `/v1/astronomy/julian-date` | Gregorian timestamp to Julian Day and Modified Julian Date | key |
| POST | `/v1/astronomy/sidereal-time` | Greenwich and local sidereal time for a timestamp and longitude | key |
| POST | `/v1/astronomy/twilight-calculator` | Civil, nautical, and astronomical twilight crossings | key |
| POST | `/v1/astronomy/sun-position` | Sun right ascension, declination, azimuth, and elevation | key |
| POST | `/v1/astronomy/moon-position` | Moon right ascension, declination, azimuth, and elevation | key |
| POST | `/v1/astronomy/day-length` | Daylight duration between sunrise and sunset | key |
| POST | `/v1/astronomy/polar-night-check` | Check midnight sun or polar night state for a latitude/date | key |

### Finance

| Method | Path | What it does | Access |
|---|---|---|---|
| POST | `/v1/finance/margin-markup` | Gross margin, markup, selling price, and cost variance | key |
| POST | `/v1/finance/loan-amortization` | Fixed-rate loan amortization schedule | key |
| POST | `/v1/finance/tax-extraction` | Tax add-on and inclusive reverse extraction | key |
| POST | `/v1/finance/freelancer-rate` | Freelancer hourly and daily rate target | key |
| POST | `/v1/finance/simple-interest` | Simple interest from principal, rate, and time | key |
| POST | `/v1/finance/compound-interest` | Future value with compound interest frequency options | key |
| POST | `/v1/finance/loan-amortization-summary` | Loan payment, total interest, and total cost summary | key |
| POST | `/v1/finance/rule-of-72` | Estimated investment doubling time using the rule of 72 | key |
| POST | `/v1/finance/roi` | Return on investment percentage from cost and net gain | key |
| POST | `/v1/finance/discount-calculator` | Final price and savings from original price and discount rate | key |
| POST | `/v1/finance/markup-margin` | Convert between gross margin and markup percentages | key |
| POST | `/v1/finance/break-even` | Break-even units from fixed costs, variable cost, and price | key |
| POST | `/v1/finance/salestax` | Add or extract sales tax/GST from an amount and tax rate | key |
| POST | `/v1/finance/cagr` | Compound annual growth rate from beginning value, ending value, and years | key |

### Math and statistics

| Method | Path | What it does | Access |
|---|---|---|---|
| POST | `/v1/math/quadratic-solver` | Solve a quadratic equation with real or complex roots and vertex coordinates | key |
| POST | `/v1/math/pythagorean-solve` | Solve the missing side of a right triangle from any two sides | key |
| POST | `/v1/math/triangle-heron` | Triangle area, perimeter, and angles from three side lengths | key |
| POST | `/v1/math/circle-geometry` | Circle area, circumference, diameter, arc length, and sector area | key |
| POST | `/v1/math/sphere-geometry` | Sphere diameter, surface area, and volume from radius | key |
| POST | `/v1/math/cylinder-geometry` | Cylinder base area, surface area, and volume from radius and height | key |
| POST | `/v1/math/statistics-summary` | Mean, median, mode, variance, standard deviation, and IQR for numbers | key |
| POST | `/v1/math/percentage-change` | Absolute and percentage change from baseline to current value | key |
| POST | `/v1/math/percent-error` | Absolute, relative, and percent error against an accepted true value | key |
| POST | `/v1/math/gcd-lcm` | Greatest common divisor and least common multiple for integer sets | key |
| POST | `/v1/math/matrix-determinant` | Determinants for 2x2 and 3x3 matrices | key |
| POST | `/v1/math/proportion-solver` | Solve x in equivalent ratios a/b = c/x | key |
| POST | `/v1/math/logarithm-eval` | Evaluate logarithms with custom bases using change of base | key |
| POST | `/v1/math/exponent-eval` | Evaluate exponentiation and optional real root extraction | key |
| POST | `/v1/math/combinatorics` | Permutations and combinations for n and r | key |
| POST | `/v1/stats/summary` | Descriptive statistics for a numeric dataset | key |

### Health

| Method | Path | What it does | Access |
|---|---|---|---|
| POST | `/v1/health/bmi` | Body Mass Index and category classification | key |
| POST | `/v1/health/bmr` | Basal Metabolic Rate using Mifflin-St Jeor | key |
| POST | `/v1/health/tdee` | Total Daily Energy Expenditure from BMR and activity multiplier | key |
| POST | `/v1/health/macro-split` | Protein, carbs, and fat grams from calories and macro percentages | key |
| POST | `/v1/health/pace-calculator` | Running or walking pace and speed from distance and duration | key |

### Payroll and trades

| Method | Path | What it does | Access |
|---|---|---|---|
| POST | `/v1/payroll/decimal-hours` | Clock time to decimal hours and overtime conversion | key |
| POST | `/v1/tradie/job-margin` | Tradie job margin from labour, materials, subcontractors, overhead, and quote | key |
| POST | `/v1/tradie/vat-return-summary` | Tradie VAT return summary from sales and purchases | key |
| POST | `/v1/tradie/cis-deduction` | UK CIS-style deduction model for labour and materials | key |
| POST | `/v1/tradie/mileage-claim` | Mileage claim and unreimbursed/reimbursed excess calculation | key |
| POST | `/v1/tradie/tool-depreciation` | Straight-line tool and equipment depreciation schedule | key |
| POST | `/v1/tradie/invoice-aging` | Receivables aging buckets for unpaid invoices | key |

### Account

| Method | Path | What it does | Access |
|---|---|---|---|
| GET | `/v1/canary` | Protected monitoring canary for API-key path checks | key |
| GET | `/v1/account/profile` | Authenticated customer profile | key |
| GET | `/v1/account/usage` | Authenticated customer usage summary | key |
| GET | `/v1/account/limits` | Authenticated customer plan and batch limits | key |
| GET | `/v1/account/credits` | Authenticated customer credit balance | key |

## 11. Examples

### Contract checks for status, canary and ephemeris

These three routes were checked against the live Munich API and OpenAPI contract on 2026-09-21:

| Route | Live method/access | Contract details | Unauthenticated live behaviour |
|---|---|---|---|
| `/v1/status` | `GET`, public | No security requirement; returns service, version, uptime, cache mode and endpoint-family inventory | `200 OK` |
| `/v1/canary` | `GET`, key required | Accepts `X-API-Key` or `Authorization: Bearer`; protected monitoring route | `401` with `{"error":{"code":"unauthorized","message":"A valid API key is required"}}` |
| `/v1/astronomy/ephemeris` | `GET`, key required | Optional `date` query parameter; `x-credit-cost: 1`; accepts `X-API-Key` or `Authorization: Bearer` | `401` with the same unauthorized error envelope |

### Local time for a coordinate (key required)

`GET /v1/time` takes the optional query parameters `lat`, `lon` and `at` (a timestamp).

```bash
curl 'https://api.calculationtime.com/v1/time?lat=-32.99&lon=148.26' \
  -H 'X-API-Key: YOUR_KEY'
```

### Crux clock: midnight positions (key required, 2 credits)

```bash
curl 'https://api.calculationtime.com/v1/astronomy/crux-midnight' \
  -X POST \
  -H 'X-API-Key: YOUR_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"start_date":"2026-03-31","days":3,"timezone":"+10:00"}'
```

Abridged response, as published on the CalculationTime developer page:

```json
{
  "input": { "start_date": "2026-03-31", "days": 3, "timezone": "+10:00" },
  "count": 3,
  "positions": [
    { "date": "2026-03-31", "day_index": 0, "crux_hand_degrees": 0 },
    { "date": "2026-04-01", "day_index": 1, "crux_hand_degrees": 0.985647366 },
    { "date": "2026-04-02", "day_index": 2, "crux_hand_degrees": 1.971294733 }
  ],
  "method": "parkes_crux_hand_sidereal_clock_zeroed_2026_03_31_local_midnight"
}
```

### Crux clock: hourly breakdown (key required, 5 credits)

```bash
curl 'https://api.calculationtime.com/v1/astronomy/crux-hourly' \
  -X POST -H 'X-API-Key: YOUR_KEY' -H 'Content-Type: application/json' \
  -d '{"date":"2026-03-31","timezone":"+10:00"}'
```

### Crux clock: current position (key required, 2 credits)

```bash
curl 'https://api.calculationtime.com/v1/astronomy/crux-current' \
  -X POST -H 'X-API-Key: YOUR_KEY' -H 'Content-Type: application/json' \
  -d '{"timestamp":"2026-04-01T00:00:00+10:00"}'
```

The Crux clock is calibrated to Parkes Observatory (latitude -32.99, longitude 148.26, elevation 415 m), with the clock hand zeroed at local midnight on 2026-03-31.

## 12. What is not documented yet

Being direct about the gaps so you can plan around them:

- **Request bodies.** In the OpenAPI contract, the POST request bodies for the finance, math, statistics, date, payroll, health and most astronomy endpoints are declared only as free-form JSON objects (`additionalProperties: true`), and response schemas are not published. Field names are therefore not specified here for those endpoints. Ask for the field list when you request a beta key; the Crux endpoints above are fully documented.
- **Per-endpoint credit costs** beyond the three Crux endpoints.
- **Keyed rate limits and batch limits** are returned per customer by `GET /v1/account/limits` rather than published.
- **Uptime.** No public SLA is claimed. `GET /v1/status` reports this deliberately.
- **Pricing and self-service.** Not live; beta access is by request.

## 13. Good practice

1. Cache reference data; key the cache on `dataset_version`. It changes rarely.
2. Read `x-ratelimit-remaining` and `x-ratelimit-reset` and slow down before you hit `429`.
3. Never expose your key in client-side code; proxy through your own server.
4. Treat curated reference tables as aids, not authorities, and cite the primary source for critical use.
5. Check `GET /v1/status` and the status page before assuming an outage on your side.

## 14. Help

- Request beta access or ask a question: <https://www.calculationtime.com/developers/api/beta/>
- Contract: <https://api.calculationtime.com/openapi.json>
- Main site and the calculators these endpoints power: <https://www.calculationtime.com>
