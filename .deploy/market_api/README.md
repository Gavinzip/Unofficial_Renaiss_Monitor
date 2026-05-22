# Renassis Market API (for Agent Wallet)

## Endpoints

- `GET /health`
- `GET /v1/listings/latest?limit=20`
- `POST /v1/analyze/item-id`
- `POST /v1/opportunities/scan`

By default, analysis endpoints return full source records:
- `sources.pricecharting.records_raw`
- `sources.pricecharting.records_normalized`
- `sources.snkrdunk.records_raw`
- `sources.snkrdunk.records_normalized`

You can disable this with `include_full_records=false` in request body.

## Quick local run

```bash
pip install -r requirements.api.txt
python3 scripts/market_api_server.py
```

## Wallet integration

- Optional env: `AGENT_WALLET_WEBHOOK_URL`
- If `notify_wallet=true` in `/v1/opportunities/scan`, API will POST result payload to that webhook.

## Zeabur deploy

1. Service type: HTTP service
2. Dockerfile: `Dockerfile.api`
3. Env vars:
   - `PORT=8080`
   - `PRICE_DIFF_PERCENT_THRESHOLD=10`
   - `WINDOW_DAYS=30`
   - `AGENT_WALLET_WEBHOOK_URL` (optional)
