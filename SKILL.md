---
name: renassis-market-arbitrage-monitor
description: Real-time arbitrage monitor for Renaiss marketplace, cross-referencing PriceCharting and SNKRDUNK.
---

# Renassis Market Arbitrage Monitor

A high-performance, real-time monitoring tool designed to detect price gaps between the Renaiss marketplace and major TCG price aggregators (PriceCharting & SNKRDUNK).

## 🚀 Quick Start for Agents

1. **Environment Setup**:
   Ensure `.env` is configured in the project root with `DISCORD_WEBHOOK_URL`.
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Monitor**:
   Execute the script from the root directory. It is designed to run persistently in the background.
   ```bash
   python3 scripts/market_monitor.py
   ```

## 🧠 Core Logic & Capabilities

### 1. Incremental Scanning (Efficiency)
- The monitor fetches all listings from Renaiss but only performs expensive price crawls for **newly discovered IDs**.
- **Persistence**: It maintains a `seen_ids.txt` file in the `scripts/` directory. Even after a restart, it will skip previously analyzed items to prevent alert spam.

### 2. Startup Test Mode
- At launch, the monitor ignores the "seen" status for the **first 5 items** and forces a real-time crawl. This serves as an immediate functional test.

### 3. Cross-Platform Analysis
- **PriceCharting (PC)**: Crawls recent sales data with grade matching (PSA/BGS/CGC). Calculates a 30-day rolling average with IQR outlier filtering.
- **SNKRDUNK (SNKR)**: Uses native API for Japanese market prices, matching specific variants (Manga/Parallel/Special Card).

### 4. Alert Trigger
- **Threshold**: Default is **$20 USD** profit potential.
- **Logic**: `Alert = (PC_AVG - Ask >= $20) OR (SNKR_AVG - Ask >= $20)`.

## 🛠 Agent Operational Guidance

### Logs Interpretation
- `🔃 正在掃描市場新掛單...`: Heartbeat signal. The script is active and checking for new listings.
- `✨ 發現 N 筆新品上架`: The script has identified new items and is about to start crawling.
- `🚨 [真正撿漏警報]`: A high-probability arbitrage opportunity was found and sent to Discord.

### Troubleshooting
- **Jina 429 Errors**: If the logs show 429 errors, the crawlers are being rate-limited. The script will automatically skip the item and retry in the next cycle.
- **Missing Alerts**: Check if `DISCORD_WEBHOOK_URL` is set in the `.env` file. Verify `scripts/seen_ids.txt` to see if the item was already "seen".

## ⚙️ Configuration (.env)
- `DISCORD_WEBHOOK_URL`: Target channel for alerts.
- `PRICE_THRESHOLD`: Minimum profit to trigger an alert (default: 20.0).
- `WINDOW_DAYS`: Rolling average window in days (default: 30).
