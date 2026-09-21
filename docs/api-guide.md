# CalculationTime API guide

Reliable time, date, geospatial, astronomy, finance, health and math calculations, plus public reference-data tables, over a plain JSON API.

This guide describes the API **as it is today (contract v0.1.0, beta)**. The contract is published in the API's public repository and matched the live service on 2026-09-21. Details the contract does not carry (keyed rate limits, header forms) come from the API's own user guide, <https://github.com/ByeBilly/calculationtime-api/blob/main/docs/api-user-guide.md>, and are marked as such; this portal has no key, so it has not run the protected endpoints itself. Where something is not documented or not yet available, the guide says so instead of guessing. The authoritative machine-readable contract is always <https://api.calculationtime.com/openapi.json>, and the service itself serves Markdown documentation at <https://api.calculationtime.com/>.

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
| API key header | `X-API-Key: YOUR_KEY` | Declared as `ApiKeyAuth` in the contract. Used in every example on this site. Keys look like `ct_live_...`. |
| Bearer token | `Authorization: Bearer YOUR_KEY` | Declared as `BearerAuth`. The API's own guide accepts either form and uses Bearer in its examples. Send one, not both. |

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

- **Public routes:** 60 requests per minute per client IP (observed).
- **Keyed routes:** the API's own guide states a default of 120 requests per minute per customer, with per-customer overrides. We could not confirm this with a key. `GET /v1/account/limits` (free) shows your actual plan and batch limits.
- **When you hit the limit** the API returns `429` with a `Retry-After` header (seconds, per the API guide). Wait that long, add jitter if several workers share a key, and do not retry in a tight loop.

## 6. Credits

Protected endpoints are credit-metered, and the contract publishes the cost of each one as `x-credit-cost`. Across the documented protected calculation endpoints:

| Cost | Endpoints |
|---|---|
| 1 credit | 71 (most lightweight maths, date, geo, finance and health calls) |
| 2 credits | 6 (including `crux-midnight` and `crux-current`) |
| 3 credits | 4 |
| 5 credits | 2 (including `crux-hourly`, which returns all 24 hours) |
| free | the account endpoints (`/v1/account/credits`, `/usage`, `/limits`) |

The exact cost of every endpoint is shown on its reference entry, for example on [Finance](reference/finance.html) and [Astronomy](reference/astronomy.html). Check your balance with `GET /v1/account/credits` and your usage with `GET /v1/account/usage`. When credits run out the API answers `402`. Credit prices in money terms are not published yet.

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

Status codes documented in the contract for protected endpoints: `200`, `400` (bad request), `401` (missing or invalid key), `402` (credits exhausted), `403` (suspended account or expired trial), `429` (rate limited). Unknown routes return `404`. The API guide also lists `500` and `503` (an optional store or provider is unavailable). A malformed JSON body returns `400` with code `invalid_json`. Handle unknown codes generically.

Route check (2026-09-21): every one of the 89 documented protected routes answered `401` with the standard error envelope when called without a key, so each route exists and is protected as documented. Nothing was called with a key.

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

Every dataset is also served under `/api/v1/data/...` with identical behaviour (for example `/api/v1/data/http-status?q=429`). Both the `/v1/data/...` routes and the `/api/v1/data/...` compatibility aliases are present in the live OpenAPI contract, which lists 122 unique paths in all.

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

Generated from the OpenAPI contract (v0.1.0) by `build-portal.py`. "public" means no key; "key" means an API key is required. Each area has its own reference page with a copy-paste request per endpoint. Administrative and private-sharing routes are omitted, and the `/api/v1/data/...` aliases are covered in section 9.

### [Service and status](reference/service.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| GET | [`/`](reference/service.html#get) | Markdown API documentation | public | - |
| GET | [`/health`](reference/service.html#get--health) | Low-level service health | public | - |
| GET | [`/openapi.json`](reference/service.html#get--openapi.json) | OpenAPI contract for live routes | public | - |
| GET | [`/v1/status`](reference/service.html#get--v1-status) | Public measured service status and endpoint inventory | public | - |
| GET | [`/v1/time/utc`](reference/service.html#get--v1-time-utc) | Current UTC timestamp and clock-model metadata | public | - |
| GET | [`/api/v1/utility/tagline`](reference/service.html#get--api-v1-utility-tagline) | Deterministic daily CalculationTime tagline | public | - |
| GET | [`/v1/canary`](reference/service.html#get--v1-canary) | Protected monitoring canary for API-key path checks | key | free |

### [Reference data](reference/reference-data.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| GET | [`/v1/data/countries`](reference/reference-data.html#get--v1-data-countries) | Country reference table with capitals, ISO codes, dialing codes, and currencies | public | - |
| GET | [`/v1/data/timezones`](reference/reference-data.html#get--v1-data-timezones) | IANA timezone reference with current UTC offsets and DST status | public | - |
| GET | [`/v1/data/elements`](reference/reference-data.html#get--v1-data-elements) | Periodic table reference values | public | - |
| GET | [`/v1/data/constants`](reference/reference-data.html#get--v1-data-constants) | Physical and mathematical constants reference table | public | - |
| GET | [`/v1/data/materials/density`](reference/reference-data.html#get--v1-data-materials-density) | Common material density reference table | public | - |
| GET | [`/v1/data/http-status`](reference/reference-data.html#get--v1-data-http-status) | HTTP status code directory | public | - |
| GET | [`/v1/data/mime-types`](reference/reference-data.html#get--v1-data-mime-types) | MIME type and extension reference table | public | - |
| GET | [`/v1/data/unicode-blocks`](reference/reference-data.html#get--v1-data-unicode-blocks) | Unicode block range reference table | public | - |
| GET | [`/v1/data/constellations`](reference/reference-data.html#get--v1-data-constellations) | IAU constellation names, genitives, abbreviations, and quadrants | public | - |
| GET | [`/v1/data/stars/bright`](reference/reference-data.html#get--v1-data-stars-bright) | Bright star reference table | public | - |
| GET | [`/v1/data/meteor-showers`](reference/reference-data.html#get--v1-data-meteor-showers) | Major annual meteor shower reference table | public | - |

### [Time and dates](reference/time-and-dates.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| GET | [`/v1/time`](reference/time-and-dates.html#get--v1-time) | Get local time for one coordinate | key | 1 credit |
| POST | [`/v1/time/batch`](reference/time-and-dates.html#post--v1-time-batch) | Get local time for up to 100 coordinates | key | 1 credit |
| GET | [`/v1/date/difference`](reference/time-and-dates.html#get--v1-date-difference) | Calendar day difference | key | 1 credit |
| POST | [`/v1/date/difference/batch`](reference/time-and-dates.html#post--v1-date-difference-batch) | Batch calendar day differences | key | 1 credit |
| GET | [`/v1/date/add`](reference/time-and-dates.html#get--v1-date-add) | Add calendar units to a date | key | 1 credit |
| POST | [`/v1/date/business-days`](reference/time-and-dates.html#post--v1-date-business-days) | Business-day count with supplied holidays | key | 1 credit |
| POST | [`/v1/date/business-days/jurisdiction`](reference/time-and-dates.html#post--v1-date-business-days-jurisdiction) | Business-day count for a supported jurisdiction | key | 1 credit |
| POST | [`/v1/date/business-days-add`](reference/time-and-dates.html#post--v1-date-business-days-add) | Add or subtract configurable business days | key | 1 credit |
| POST | [`/v1/date/iso-week`](reference/time-and-dates.html#post--v1-date-iso-week) | ISO week number, week-year, and weekday | key | 1 credit |
| POST | [`/v1/date/age-breakdown`](reference/time-and-dates.html#post--v1-date-age-breakdown) | Exact age duration breakdown from birth date to timestamp | key | 1 credit |
| POST | [`/v1/date/countdown-precise`](reference/time-and-dates.html#post--v1-date-countdown-precise) | Precise calendar delta between timestamps | key | 1 credit |
| POST | [`/v1/date/epoch-converter`](reference/time-and-dates.html#post--v1-date-epoch-converter) | Unix epoch seconds or milliseconds to ISO/RFC strings | key | 1 credit |
| POST | [`/v1/date/quarter-calculator`](reference/time-and-dates.html#post--v1-date-quarter-calculator) | Calendar and fiscal quarter with progress percentage | key | 1 credit |
| POST | [`/v1/date/leap-year-check`](reference/time-and-dates.html#post--v1-date-leap-year-check) | Gregorian and Julian leap-year proof check | key | 1 credit |
| POST | [`/v1/date/days-in-month`](reference/time-and-dates.html#post--v1-date-days-in-month) | Days in a Gregorian month | key | 1 credit |
| POST | [`/v1/date/timezone-offset`](reference/time-and-dates.html#post--v1-date-timezone-offset) | Fixed UTC offset conversion without DST lookup | key | 1 credit |
| POST | [`/v1/date/calendar-range`](reference/time-and-dates.html#post--v1-date-calendar-range) | Generate a deterministic date range with weekday and ISO week facts | key | 1 credit |
| GET | [`/v1/holidays`](reference/time-and-dates.html#get--v1-holidays) | Holidays for a jurisdiction and year | key | 1 credit |
| GET | [`/v1/holidays/next`](reference/time-and-dates.html#get--v1-holidays-next) | Next holiday for a jurisdiction | key | 1 credit |
| GET | [`/v1/holidays/is-business-day`](reference/time-and-dates.html#get--v1-holidays-is-business-day) | Business-day check for one date | key | 1 credit |

### [Geo](reference/geo.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| GET | [`/v1/geo/distance`](reference/geo.html#get--v1-geo-distance) | Distance between two coordinates | key | 1 credit |
| POST | [`/v1/geo/distance/batch`](reference/geo.html#post--v1-geo-distance-batch) | Batch distance calculations | key | 1 credit |
| GET | [`/v1/geo/midpoint`](reference/geo.html#get--v1-geo-midpoint) | Midpoint between two coordinates | key | 1 credit |
| GET | [`/v1/geo/bounding-box`](reference/geo.html#get--v1-geo-bounding-box) | Bounding box around a coordinate | key | 1 credit |
| GET | [`/v1/geo/elevation`](reference/geo.html#get--v1-geo-elevation) | Elevation for one coordinate | key | 1 credit |
| GET | [`/v1/geo/nearby`](reference/geo.html#get--v1-geo-nearby) | Nearby stored geo points | key | 1 credit |

### [Astronomy and Crux clock](reference/astronomy.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| GET | [`/v1/solar/position`](reference/astronomy.html#get--v1-solar-position) | Solar position for date and coordinate | key | 1 credit |
| GET | [`/v1/astronomy/ephemeris`](reference/astronomy.html#get--v1-astronomy-ephemeris) | Astronomy ephemeris for a date | key | 1 credit |
| POST | [`/v1/astronomy/crux-midnight`](reference/astronomy.html#post--v1-astronomy-crux-midnight) | Crux clock hand midnight sidereal positions from Parkes Observatory calibration | key | 2 credits |
| POST | [`/v1/astronomy/crux-hourly`](reference/astronomy.html#post--v1-astronomy-crux-hourly) | Crux clock hand hourly sidereal breakdown for one local date | key | 5 credits |
| POST | [`/v1/astronomy/crux-current`](reference/astronomy.html#post--v1-astronomy-crux-current) | Current Crux clock hand position and Parkes alignment delta | key | 2 credits |
| POST | [`/v1/astronomy/solar-noon`](reference/astronomy.html#post--v1-astronomy-solar-noon) | Solar transit/noon timestamp for a coordinate and date | key | 1 credit |
| POST | [`/v1/astronomy/equinox-solstice`](reference/astronomy.html#post--v1-astronomy-equinox-solstice) | Equinox and solstice timestamps for a year | key | 1 credit |
| POST | [`/v1/astronomy/moon-phase`](reference/astronomy.html#post--v1-astronomy-moon-phase) | Moon illumination, age, and phase name for a timestamp | key | 1 credit |
| POST | [`/v1/astronomy/julian-date`](reference/astronomy.html#post--v1-astronomy-julian-date) | Gregorian timestamp to Julian Day and Modified Julian Date | key | 1 credit |
| POST | [`/v1/astronomy/sidereal-time`](reference/astronomy.html#post--v1-astronomy-sidereal-time) | Greenwich and local sidereal time for a timestamp and longitude | key | 1 credit |
| POST | [`/v1/astronomy/twilight-calculator`](reference/astronomy.html#post--v1-astronomy-twilight-calculator) | Civil, nautical, and astronomical twilight crossings | key | 1 credit |
| POST | [`/v1/astronomy/sun-position`](reference/astronomy.html#post--v1-astronomy-sun-position) | Sun right ascension, declination, azimuth, and elevation | key | 1 credit |
| POST | [`/v1/astronomy/moon-position`](reference/astronomy.html#post--v1-astronomy-moon-position) | Moon right ascension, declination, azimuth, and elevation | key | 1 credit |
| POST | [`/v1/astronomy/day-length`](reference/astronomy.html#post--v1-astronomy-day-length) | Daylight duration between sunrise and sunset | key | 1 credit |
| POST | [`/v1/astronomy/polar-night-check`](reference/astronomy.html#post--v1-astronomy-polar-night-check) | Check midnight sun or polar night state for a latitude/date | key | 1 credit |

### [Finance](reference/finance.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| POST | [`/v1/finance/margin-markup`](reference/finance.html#post--v1-finance-margin-markup) | Gross margin, markup, selling price, and cost variance | key | 1 credit |
| POST | [`/v1/finance/loan-amortization`](reference/finance.html#post--v1-finance-loan-amortization) | Fixed-rate loan amortization schedule | key | 5 credits |
| POST | [`/v1/finance/tax-extraction`](reference/finance.html#post--v1-finance-tax-extraction) | Tax add-on and inclusive reverse extraction | key | 2 credits |
| POST | [`/v1/finance/freelancer-rate`](reference/finance.html#post--v1-finance-freelancer-rate) | Freelancer hourly and daily rate target | key | 2 credits |
| POST | [`/v1/finance/simple-interest`](reference/finance.html#post--v1-finance-simple-interest) | Simple interest from principal, rate, and time | key | 1 credit |
| POST | [`/v1/finance/compound-interest`](reference/finance.html#post--v1-finance-compound-interest) | Future value with compound interest frequency options | key | 1 credit |
| POST | [`/v1/finance/loan-amortization-summary`](reference/finance.html#post--v1-finance-loan-amortization-summary) | Loan payment, total interest, and total cost summary | key | 1 credit |
| POST | [`/v1/finance/rule-of-72`](reference/finance.html#post--v1-finance-rule-of-72) | Estimated investment doubling time using the rule of 72 | key | 1 credit |
| POST | [`/v1/finance/roi`](reference/finance.html#post--v1-finance-roi) | Return on investment percentage from cost and net gain | key | 1 credit |
| POST | [`/v1/finance/discount-calculator`](reference/finance.html#post--v1-finance-discount-calculator) | Final price and savings from original price and discount rate | key | 1 credit |
| POST | [`/v1/finance/markup-margin`](reference/finance.html#post--v1-finance-markup-margin) | Convert between gross margin and markup percentages | key | 1 credit |
| POST | [`/v1/finance/break-even`](reference/finance.html#post--v1-finance-break-even) | Break-even units from fixed costs, variable cost, and price | key | 1 credit |
| POST | [`/v1/finance/salestax`](reference/finance.html#post--v1-finance-salestax) | Add or extract sales tax/GST from an amount and tax rate | key | 1 credit |
| POST | [`/v1/finance/cagr`](reference/finance.html#post--v1-finance-cagr) | Compound annual growth rate from beginning value, ending value, and years | key | 1 credit |

### [Math and statistics](reference/math-and-statistics.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| POST | [`/v1/math/quadratic-solver`](reference/math-and-statistics.html#post--v1-math-quadratic-solver) | Solve a quadratic equation with real or complex roots and vertex coordinates | key | 1 credit |
| POST | [`/v1/math/pythagorean-solve`](reference/math-and-statistics.html#post--v1-math-pythagorean-solve) | Solve the missing side of a right triangle from any two sides | key | 1 credit |
| POST | [`/v1/math/triangle-heron`](reference/math-and-statistics.html#post--v1-math-triangle-heron) | Triangle area, perimeter, and angles from three side lengths | key | 1 credit |
| POST | [`/v1/math/circle-geometry`](reference/math-and-statistics.html#post--v1-math-circle-geometry) | Circle area, circumference, diameter, arc length, and sector area | key | 1 credit |
| POST | [`/v1/math/sphere-geometry`](reference/math-and-statistics.html#post--v1-math-sphere-geometry) | Sphere diameter, surface area, and volume from radius | key | 1 credit |
| POST | [`/v1/math/cylinder-geometry`](reference/math-and-statistics.html#post--v1-math-cylinder-geometry) | Cylinder base area, surface area, and volume from radius and height | key | 1 credit |
| POST | [`/v1/math/statistics-summary`](reference/math-and-statistics.html#post--v1-math-statistics-summary) | Mean, median, mode, variance, standard deviation, and IQR for numbers | key | 1 credit |
| POST | [`/v1/math/percentage-change`](reference/math-and-statistics.html#post--v1-math-percentage-change) | Absolute and percentage change from baseline to current value | key | 1 credit |
| POST | [`/v1/math/percent-error`](reference/math-and-statistics.html#post--v1-math-percent-error) | Absolute, relative, and percent error against an accepted true value | key | 1 credit |
| POST | [`/v1/math/gcd-lcm`](reference/math-and-statistics.html#post--v1-math-gcd-lcm) | Greatest common divisor and least common multiple for integer sets | key | 1 credit |
| POST | [`/v1/math/matrix-determinant`](reference/math-and-statistics.html#post--v1-math-matrix-determinant) | Determinants for 2x2 and 3x3 matrices | key | 1 credit |
| POST | [`/v1/math/proportion-solver`](reference/math-and-statistics.html#post--v1-math-proportion-solver) | Solve x in equivalent ratios a/b = c/x | key | 1 credit |
| POST | [`/v1/math/logarithm-eval`](reference/math-and-statistics.html#post--v1-math-logarithm-eval) | Evaluate logarithms with custom bases using change of base | key | 1 credit |
| POST | [`/v1/math/exponent-eval`](reference/math-and-statistics.html#post--v1-math-exponent-eval) | Evaluate exponentiation and optional real root extraction | key | 1 credit |
| POST | [`/v1/math/combinatorics`](reference/math-and-statistics.html#post--v1-math-combinatorics) | Permutations and combinations for n and r | key | 1 credit |
| POST | [`/v1/stats/summary`](reference/math-and-statistics.html#post--v1-stats-summary) | Descriptive statistics for a numeric dataset | key | 3 credits |

### [Health](reference/health.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| POST | [`/v1/health/bmi`](reference/health.html#post--v1-health-bmi) | Body Mass Index and category classification | key | 1 credit |
| POST | [`/v1/health/bmr`](reference/health.html#post--v1-health-bmr) | Basal Metabolic Rate using Mifflin-St Jeor | key | 1 credit |
| POST | [`/v1/health/tdee`](reference/health.html#post--v1-health-tdee) | Total Daily Energy Expenditure from BMR and activity multiplier | key | 1 credit |
| POST | [`/v1/health/macro-split`](reference/health.html#post--v1-health-macro-split) | Protein, carbs, and fat grams from calories and macro percentages | key | 1 credit |
| POST | [`/v1/health/pace-calculator`](reference/health.html#post--v1-health-pace-calculator) | Running or walking pace and speed from distance and duration | key | 1 credit |

### [Payroll and trades](reference/payroll-and-trades.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| POST | [`/v1/payroll/decimal-hours`](reference/payroll-and-trades.html#post--v1-payroll-decimal-hours) | Clock time to decimal hours and overtime conversion | key | 1 credit |
| POST | [`/v1/tradie/job-margin`](reference/payroll-and-trades.html#post--v1-tradie-job-margin) | Tradie job margin from labour, materials, subcontractors, overhead, and quote | key | 2 credits |
| POST | [`/v1/tradie/vat-return-summary`](reference/payroll-and-trades.html#post--v1-tradie-vat-return-summary) | Tradie VAT return summary from sales and purchases | key | 3 credits |
| POST | [`/v1/tradie/cis-deduction`](reference/payroll-and-trades.html#post--v1-tradie-cis-deduction) | UK CIS-style deduction model for labour and materials | key | 2 credits |
| POST | [`/v1/tradie/mileage-claim`](reference/payroll-and-trades.html#post--v1-tradie-mileage-claim) | Mileage claim and unreimbursed/reimbursed excess calculation | key | 1 credit |
| POST | [`/v1/tradie/tool-depreciation`](reference/payroll-and-trades.html#post--v1-tradie-tool-depreciation) | Straight-line tool and equipment depreciation schedule | key | 3 credits |
| POST | [`/v1/tradie/invoice-aging`](reference/payroll-and-trades.html#post--v1-tradie-invoice-aging) | Receivables aging buckets for unpaid invoices | key | 3 credits |

### [Account](reference/account.html)

| Method | Path | What it does | Access | Cost |
|---|---|---|---|---|
| GET | [`/v1/account/profile`](reference/account.html#get--v1-account-profile) | Authenticated customer profile | key | free |
| GET | [`/v1/account/usage`](reference/account.html#get--v1-account-usage) | Authenticated customer usage summary | key | free |
| GET | [`/v1/account/limits`](reference/account.html#get--v1-account-limits) | Authenticated customer plan and batch limits | key | free |
| GET | [`/v1/account/credits`](reference/account.html#get--v1-account-credits) | Authenticated customer credit balance | key | free |

## 11. Examples

### Contract checks for status, canary and ephemeris

These three routes were checked against the live Munich API and OpenAPI contract on 2026-09-21 (checks contributed by Jack):

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

- **Request schemas.** The contract publishes a known-good example body for each of the 74 POST operations (see the reference pages), but declares the body only as free-form JSON (`additionalProperties: true`): it does not list required versus optional fields, types or limits. Response schemas are not published either. Copy an example, change the values, and inspect the response.
- **Query parameter values.** A few GET endpoints (holidays, `geo/nearby`) list parameter names without sample values; the reference shows the names in capitals as placeholders. Which jurisdictions the holiday endpoints accept is not documented.
- **Keyed rate limits.** Stated in the API guide (default 120 per minute) but not returned by the contract; `GET /v1/account/limits` is authoritative.
- **Uptime.** No public SLA is claimed. `GET /v1/status` reports this deliberately.
- **Pricing and self-service.** Not live; beta access is by request. Credit costs are published, money prices are not.
- **Data caveats.** `observes_dst_now` in the timezone table means the zone uses daylight saving at all, not that it is in effect now; compare `offset_minutes` at the `at` timestamp you care about. Several reference tables are curated subsets (for example, 23 Unicode blocks and 20 bright stars).

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
