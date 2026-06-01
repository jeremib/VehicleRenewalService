# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FastAPI service that automates Tennessee vehicle registration renewals on `secure.tncountyclerk.com` via Selenium + headless Chromium. Deployed as a Cloudflare Worker fronting a Cloudflare Container that runs the Python app.

## Commands

Local Docker run (per README):
```
export DOCKER_DEFAULT_PLATFORM=linux/amd64 && docker build -t vehicle_registration . && docker run -p 8080:80 -v "$(pwd)/app:/app" vehicle_registration
```

Cloudflare:
- `npm run dev` — `wrangler dev` (runs Worker + container locally)
- `npm run deploy` — `wrangler deploy` (builds Dockerfile, pushes container, deploys Worker)

There are no automated tests, linters, or typecheck scripts wired up. The container build itself is the only CI signal.

## Architecture

Two-layer deployment:

1. **Cloudflare Worker** (`src/index.ts`) — thin entrypoint. Defines `VehicleRenewalContainer` (extends `@cloudflare/containers` `Container`, `defaultPort = 80`, `sleepAfter = "5m"`) and forwards every request via `env.VEHICLE_RENEWAL.getByName("default").fetch(request)`. The Worker itself does no business logic — it exists to bind the container Durable Object and route `vrs.renewmytags.com/*` to it.
2. **Container** (`Dockerfile` → `app/`) — `python:3.12-alpine` with `chromium` + `chromium-chromedriver`. Runs `uvicorn Main:app --host 0.0.0.0 --port 80 --workers 4`. `RENEWAL_SERVICE_URL` is baked into the image (currently `https://secure.tncountyclerk.com//`).

`wrangler.jsonc` binds the container as a Durable Object (`VEHICLE_RENEWAL`), `instance_type: standard-1`, `max_instances: 5`. The account id and zone id for `renewmytags.com` are committed.

### Python app flow

`app/Main.py` exposes two endpoints, both POST:
- `/query/price/tennessee` → `process_renewal_query` — navigates the renewal flow up to the fee summary and returns it without paying.
- `/complete/tennessee` → `process_renewal_completion` — same flow plus `handle_payment_processing`, verifies landing on the confirmation page.

Selenium is synchronous, FastAPI is async — every request is dispatched through a module-level `ThreadPoolExecutor(max_workers=10)` via `run_in_thread`. This cap (10) is the effective concurrency limit per container instance; combined with `max_instances: 5` that's 50 concurrent renewals before requests queue.

Each request constructs a fresh `RenewalService` (new headless Chrome process), and the `finally` block calls `driver.quit()`. There is no driver reuse / pooling — driver startup cost is paid per request.

### RenewalService state machine

`app/Services/RenewalService.py` walks a multi-page government site by CSS/ID selectors. The site does not have stable page URLs, so `check_current_page()` sniffs DOM elements to decide where it is: `street_number_page`, `form_page`, `price_page`, `fee_page`, `successful_payment`. The query path can short-circuit to `price_page` early (Main.py:40-42).

Method order matters and mirrors the user's clicks: `beginning_county_selection` → `fill_street_number_page` → `fill_form_page` → `county_selection_element` → `collect_form_data` → (optionally) `handle_payment_processing`. Most methods swallow exceptions with bare `except Exception: pass` — failures cascade into a wrong-page state detected later. If you add new steps, follow that pattern only when the step is genuinely optional; otherwise propagate.

Form fee fields use CSS selectors with escaped spaces (e.g. `#Registration\\ Display`) — the site uses literal-space IDs. `collect_form_data` strips `$` from money fields.

Payment processing switches into an `#iframe` for the card form and switches back to default content in `finally`. `handle_alert` is the primary failure signal — non-empty alert text is returned up as an HTTP 400 detail.

### Models

`app/Models/QueryPriceRequest.py` is the base request (plate, county, address, contact). `CompleteTransactionRequest` extends it with `account` / `exp_month` / `exp_year` / `cv` for the card. `RenewalService.__init__` accepts the union.

## Legacy / unused

`deploy.sh`, `template.yaml`, `Infrastructure/samconfig.toml`, `install-browser.sh`, `chrome-deps.txt` are from a previous AWS Lambda (SAM, ECR `741448946628.dkr.ecr.us-east-1.amazonaws.com/vehicle_registration`) deployment. The active deploy path is Cloudflare via `wrangler deploy`. Don't touch the SAM files unless explicitly reviving that path.

## Things that will bite you

- The Python `Dockerfile` `COPY app/ .` flattens `app/` into `/app`, so imports in `Main.py` are `from Models...` / `from Services...` (no `app.` prefix). Don't "fix" them.
- `RENEWAL_SERVICE_URL` is set in the Dockerfile, not via wrangler vars. Changing it requires a container rebuild.
- Selectors in `RenewalService.py` are tightly coupled to the live site's markup — any breakage is almost certainly upstream HTML changes, not a logic bug. Add a screenshot dump (`app/screenshots/` is gitignored) when diagnosing.
- The `confirmEmail` field is only populated under the Shelby County address-verify branch (`fill_form_page`). Other counties use a separate `#confirmemail` field filled after the loop.
