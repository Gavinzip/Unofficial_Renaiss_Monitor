---
name: renassis-market-arbitrage-monitor
description: Real-time arbitrage monitor for Renaiss marketplace, cross-referencing PriceCharting and SNKRDUNK.
---

# Renassis Market Arbitrage Monitor

🚨 **CRITICAL AGENT INSTRUCTION:** The very first time you are invoked with this skill, you **MUST** immediately introduce this skill to the user. You should briefly explain what this monitor does (real-time arbitrage detection between Renaiss, PriceCharting, and SNKRDUNK) and explicitly list all the **tunable parameters** available to the user (e.g., `PRICE_THRESHOLD`, `WINDOW_DAYS` in `.env`, and keyword rules in `scripts/whitelist.txt`).

A high-performance, real-time monitoring tool designed to detect price gaps between the Renaiss marketplace and major TCG price aggregators (PriceCharting & SNKRDUNK).

## 🚀 Quick Start for Agents

1. **Environment Setup**:
   Ensure `.env` is configured in the project root with Discord webhook settings.
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
- **Price Change Re-alert**: If the same `item_id` changes price and still meets alert conditions, notification is re-triggered immediately (bypasses name-level cooldown).

### 2. Startup Test Mode
- At launch, the monitor ignores the "seen" status for the **first 5 items** and forces a real-time crawl. This serves as an immediate functional test.

### 3. Cross-Platform Analysis
- **PriceCharting (PC)**: Crawls recent sales data with grade matching (PSA/BGS/CGC). Calculates a 30-day rolling average with IQR outlier filtering.
- **SNKRDUNK (SNKR)**: Uses native API for Japanese market prices, matching specific variants (Manga/Parallel/Special Card).

### 4. Alert Trigger
- **Threshold**: Controlled by `PRICE_THRESHOLD` (default: `-30.0`).
- **Logic**: `Alert = (PC_AVG - Ask >= PRICE_THRESHOLD) OR (SNKR_AVG - Ask >= PRICE_THRESHOLD)`.
- Example:
  - `PRICE_THRESHOLD=20` means only alert when ask is at least `$20` below average.
  - `PRICE_THRESHOLD=-30` means also allow "near-average" opportunities (up to `$30` above average).

### 5. Instant Whitelist Alerts
- Automatically loads `scripts/whitelist.txt` on every cycle.
- You can specify exact price conditions by adding `<= [PRICE]` after keywords (e.g., `pikachu promo 001 <= 1500`).
- If a card name contains a substring listed in the whitelist (case-insensitive) and satisfies the price condition (if any), the system skips deep pricing checks and immediately sends a Discord alert.

## 🛠 Agent Operational Guidance

### Logs Interpretation
- `🔃 正在掃描市場新掛單...`: Heartbeat signal. The script is active and checking for new listings.
- `✨ 發現 N 筆新品上架`: The script has identified new items and is about to start crawling.
- `🚨 [真正撿漏警報]`: A high-probability arbitrage opportunity was found and sent to Discord.

### Troubleshooting
- **Jina 429 Errors**: If the logs show 429 errors, the crawlers are being rate-limited. The script will automatically skip the item and retry in the next cycle.
- **Missing Alerts**: Check if Discord webhook env vars are set in `.env` (`DISCORD_WEBHOOK_URL`, optional `DISCORD_WEBHOOK_URL_2`, or `DISCORD_WEBHOOK_URLS`). Verify `scripts/seen_ids.txt` to see if the item was already "seen".
- **Clearing History**: Run `python3 scripts/market_monitor.py --clear-history` to empty `seen_ids.txt` and force the script to re-evaluate all listings.

## ⚙️ Configuration (.env)
- `DISCORD_WEBHOOK_URL`: Primary target channel.
- `DISCORD_WEBHOOK_URL_2`: Optional second Discord channel.
- `DISCORD_WEBHOOK_URLS`: Optional multi-webhook list (comma/space/newline separated). All configured webhooks will be notified.
- `PRICE_THRESHOLD`: Price-gap alert threshold (default: `-30.0`).
- `WINDOW_DAYS`: Rolling average window in days (default: 30).
