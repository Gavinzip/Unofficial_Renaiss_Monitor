# Zeabur Deployment (renassis market monitor)

## 1) Create Service
- Repo source: this `renassis` repo.
- Dockerfile: `Dockerfile.market-monitor`.

## 2) Environment Variables
- `DISCORD_WEBHOOK_URL`
- `PRICE_THRESHOLD` (example: `20`)
- `WINDOW_DAYS` (example: `30`)
- `SEEN_IDS_FILE` (recommended: `/data/seen_ids.txt`)

## 3) Persistent Volume
- Mount a volume to `/data`.
- This keeps `seen_ids.txt` across restarts.

## 4) Run Command
Built into Dockerfile:

```bash
python scripts/market_monitor.py
```
