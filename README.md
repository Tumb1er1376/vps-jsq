# VPS Residual Value Calculator

A maintained fork of [hahabye/vps_jsq](https://github.com/hahabye/vps_jsq) for estimating the remaining value of VPS subscriptions.

This fork keeps the original GPL-3.0 license and adds a redesigned frontend, a validated Python API, generated SVG share cards, containerized deployment, tests, and GitHub Actions.

## Features

- Monthly, quarterly, semiannual, annual, two-year, three-year, and five-year billing cycles
- Reference exchange rates with optional custom-rate comparison
- Calendar-aware remaining-value calculation
- Compact SVG share cards with Markdown copy support
- Responsive light UI with accessible focus states
- Bounded request payloads and generated-share storage
- Separate non-root web/API containers with health checks
- Unit tests and CI container builds

## Quick Start

```bash
cp .env.example .env
# Edit PUBLIC_BASE_URL in .env
docker compose up -d --build
```

Default local endpoints:

- Web (including `/api/` and `/share/` proxying): `http://127.0.0.1:18088`
- Direct API/debug port: `http://127.0.0.1:18089`

Use `deploy/Caddyfile.example` as a reverse-proxy template. Replace `vps.example.com` with your domain.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `PUBLIC_BASE_URL` | `http://localhost:18088` in Compose | Base URL embedded in generated share links |
| `WEB_PORT` | `18088` | Host loopback port for the frontend |
| `API_PORT` | `18089` | Host loopback port for the API |
| `WEB_IMAGE` | local build | Optional prebuilt frontend image |
| `API_IMAGE` | local build | Optional prebuilt API image |

The API stores generated SVG cards in the `share-data` volume. It keeps at most 2,000 files. A separate retention job can remove cards older than your desired sharing window.

### Calculation convention

The selected billing price is treated as the price of one billing cycle. Remaining value is calculated over all days between the trade date and expiry date. It is intentionally not capped to one billing cycle, so a monthly subscription with more than one month remaining can have a remaining value greater than its displayed monthly cycle price.

## Development

Run backend tests:

```bash
python3 -m unittest discover -s tests -v
```

Validate frontend asset references:

```bash
python3 scripts/check_web_assets.py
```

Build both containers:

```bash
docker compose build
```

## API

### `GET /api/vps/rates`

Returns the supported CNY exchange rates. When the upstream provider is unavailable, the API currently falls back to bundled estimates.

### `POST /api/vps/jsq`

```json
{
  "exchange_rate": "6.780",
  "custom_exchange_rate": "7.000",
  "renew_money": "10",
  "currency_code": "USD",
  "cycle": "monthly",
  "expiry_date": "2026-12-31",
  "trade_date": "2026-07-18"
}
```

Request bodies are limited to 16 KiB and must use `application/json`.

## Deployment Notes

- Bind the web and API ports to loopback and expose them through Caddy, Nginx, or another TLS reverse proxy.
- Put public rate limiting in front of `/api/vps/jsq` when deploying to a high-traffic domain.
- Do not commit `.env`, generated SVG files, backups, or runtime caches.
- The provided images run as non-root users and drop Linux capabilities.

## Attribution and License

Based on [hahabye/vps_jsq](https://github.com/hahabye/vps_jsq). Original project discussions and attribution remain available in the upstream repository history.

Licensed under the GNU General Public License v3.0. See [LICENSE.txt](LICENSE.txt). Modified versions must remain GPL-compatible and preserve license notices.

Bundled third-party software notices are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
