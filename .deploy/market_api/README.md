# Renassis Market API (for Agent Wallet)

## Endpoints

- `GET /health`
- `GET /v1/listings/latest?limit=20`
- `POST /v1/analyze/item-id`
- `POST /v1/opportunities/scan`
- `GET /v1/opportunities/latest`

By default, analysis endpoints return full source records:
- `sources.pricecharting.records_raw`
- `sources.pricecharting.records_normalized`
- `sources.snkrdunk.records_raw`
- `sources.snkrdunk.records_normalized`

You can disable this with `include_full_records=false` in request body.

`/v1/opportunities/scan` behavior:
- `scan_limit`: how many latest listings to analyze (default `30`)
- `keep_limit`: how many final cards to keep in response (default `10`)
- `limit`: deprecated alias of `keep_limit` (kept for compatibility)
- `use_cache`: use cached result when available (default `true`)
- `force_refresh`: ignore cache and recalculate now (default `false`)
- `cache_ttl_seconds`: cache freshness window, overrides env default

`/v1/listings/latest` query params:
- `limit`: return item count (max `200`)
- `page`: start page (default `1`)
- `pages`: fetch how many pages from `page` (default `1`, max `10`)
- `step`: items per marketplace page (default `96`)
- `cardType`: marketplace card type (default `Card`)
- `orderBy`: marketplace ordering (default `listedDateDesc`)
- `dedupe`: if `true`, keep cheapest per `name+grade`
- `q`: optional name keyword filter
- `minAsk` / `maxAsk`: optional ask price range filter (USD)

## Quick local run

```bash
pip install -r requirements.api.txt
python3 scripts/market_api_server.py
```

## Wallet integration

- Optional env: `AGENT_WALLET_WEBHOOK_URL`
- If `notify_wallet=true` in `/v1/opportunities/scan`, API will POST result payload to that webhook.

## Cache

- Cache file path: `OPPORTUNITY_CACHE_FILE` (default `scripts/cache/opportunities_latest.json`)
- Default cache TTL: `OPPORTUNITY_CACHE_TTL_SECONDS` (default `300`)
- Startup warmup: `OPPORTUNITY_WARMUP_ON_STARTUP=true` (default enabled)
- Warmup size defaults:
  - `OPPORTUNITY_WARMUP_SCAN_LIMIT=30`
  - `OPPORTUNITY_WARMUP_KEEP_LIMIT=10`

## Zeabur deploy

1. Service type: HTTP service
2. Dockerfile: `Dockerfile.api`
3. Env vars:
   - `PORT=8080`
   - `PRICE_DIFF_PERCENT_THRESHOLD=10`
   - `WINDOW_DAYS=30`
   - `AGENT_WALLET_WEBHOOK_URL` (optional)
