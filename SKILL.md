---
name: renassis-market-arbitrage-monitor
description: Real-time arbitrage monitor for Renaiss marketplace + Twitter/X news aggregator. Cross-references PriceCharting and SNKRDUNK for market data, monitors Twitter accounts for Pokemon TCG news and sends AI-summarized alerts to Discord.
---

# Renassis Market Arbitrage Monitor

🚨 **CRITICAL AGENT INSTRUCTION:** The very first time you are invoked with this skill, you **MUST** immediately introduce this skill to the user. You should briefly explain what this monitor does:
1. **Real-time arbitrage detection** between Renaiss, PriceCharting, and SNKRDUNK
2. **Twitter/X news monitoring** - monitors Pokemon TCG Twitter accounts and sends AI-summarized Discord alerts

Also explicitly list all the **tunable parameters** available to the user (e.g., `PRICE_DIFF_PERCENT_THRESHOLD`, `WINDOW_DAYS`, `TWITTER_ACCOUNTS`, `TWITTER_CHECK_INTERVAL` in `.env`, and keyword rules in `scripts/whitelist.txt`).

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
   Canonical entrypoint is only `scripts/market_monitor.py` (do not use a root-level `market_monitor.py`).

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
- **Threshold**: Controlled by `PRICE_DIFF_PERCENT_THRESHOLD` (default: `-10.0`).
- **Logic**: `Alert = ((AVG - Ask) / AVG * 100 >= PRICE_DIFF_PERCENT_THRESHOLD)` on either source.
- Example:
  - `PRICE_DIFF_PERCENT_THRESHOLD=10` means only alert when ask is at least `10%` below average.
  - `PRICE_DIFF_PERCENT_THRESHOLD=-10` means also allow "near-average" opportunities (up to `10%` above average).

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
- **Clearing History**:
  - Run `python3 scripts/market_monitor.py --clear-history` to clear `seen_ids.txt` (ID/price seen-state) and then exit immediately.
  - On the next normal launch (`python3 scripts/market_monitor.py`), the monitor performs startup test mode and force-scans the first 5 marketplace listings again.
  - Note: `--clear-history` only clears `seen_ids.txt`; name-level cooldown history (`scripts/seen_names.json`) is kept.

## ⚙️ Configuration (.env)
- `DISCORD_WEBHOOK_URL`: Primary target channel.
- `DISCORD_WEBHOOK_URL_2`: Optional second Discord channel.
- `DISCORD_WEBHOOK_URLS`: Optional multi-webhook list (comma/space/newline separated). All configured webhooks will be notified.
- `DISCORD_WEBHOOK_URL_NOMARKET_ERROR`: Discord webhook for "no market data found" alerts (sent when both PriceCharting and SNKRDUNK return no data).
- `PRICE_DIFF_PERCENT_THRESHOLD`: Percentage price-gap alert threshold (default: `-10.0`).
- `WINDOW_DAYS`: Rolling average window in days (default: 30).

### 🔄 Card Suffix Fallback Search
When searching for cards with type suffixes (e.g., `-Holo`, `-Full Art`, `-Reverse Holo`, `-1st Edition`, `-PSA 10`), the system automatically:
1. First attempts search with the full name including suffix
2. If no exact name+number match found, strips the suffix and retries
3. Validates that results strictly match both name AND number
4. If validation fails, no result is included

This handles cases like "Shedinja-Holo #6" where PriceCharting lists the card as just "shedinja-6".

### 📊 No Market Data Notification
When both PriceCharting AND SNKRDUNK return no data for a card, a special notification is sent to `DISCORD_WEBHOOK_URL_NOMARKET_ERROR` containing:
- Card name, number, series, grade, language
- Renaiss listing link
- Image link (if available)

---

# 🐦 Twitter/X News Monitor

Separate monitoring module for tracking Pokemon TCG news from Twitter/X accounts. Uses Jina AI to bypass anti-scraping and MiniMax to generate Chinese summaries.

## 🚀 Quick Start for Twitter Monitor

```bash
# Single run
python3 scripts/twitter_monitor.py

# Background mode (runs every 30 minutes by default)
nohup python3 -u scripts/twitter_monitor.py > twitter_monitor.log 2>&1 &
```

## 🧠 Core Logic & Capabilities

### 1. Jina AI Content Fetching
- Uses `https://r.jina.ai/https://x.com/{username}` to fetch Twitter content
- Bypasses most anti-scraping protections
- Fetches latest 5-6 tweets per account per cycle

### 2. Tweet Deduplication
- Maintains `scripts/seen_tweets.json` to track processed tweet IDs
- Only alerts on NEW tweets since last check
- Stores last 100 tweet IDs per account

### 3. MiniMax AI Summarization
- Generates Chinese (Traditional) summaries of new tweets
- Extracts key Pokemon TCG news points
- Falls back to raw content if API key not set

### 4. Discord Notification
- Sends formatted Embed messages to `DISCORD_WEBHOOK_URL_TWITTER`
- Includes: summary, source link, timestamp, tweet count

## ⚙️ Twitter Monitor Configuration (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL_TWITTER` | Discord channel for Twitter alerts | (required) |
| `TWITTER_ACCOUNTS` | Comma-separated usernames (without @) | `pokegetinfomain` |
| `TWITTER_CHECK_INTERVAL` | Minutes between checks | `30` |
| `MINIMAX_API_KEY` | For AI summarization | (optional) |

**Example `.env` additions:**
```bash
DISCORD_WEBHOOK_URL_TWITTER="https://discord.com/api/webhooks/xxx/yyy"
TWITTER_ACCOUNTS="pokegetinfomain,PokeGetInfoMain"
TWITTER_CHECK_INTERVAL=30
MINIMAX_API_KEY="your_key_here"
```

## 🛠 Agent Operational Guidance

### Logs Interpretation
- `🔍 Checking @username...`: Currently fetching tweets
- `✨ Found N new tweet(s)!`: New content detected
- `✅ Sent to Discord!`: Successfully notified
- `⚠️ Failed to send to Discord`: Webhook error (check URL)

### Troubleshooting
- **No tweets detected**: Check if `seen_tweets.json` exists, delete to reset
- **MiniMax errors**: Verify `MINIMAX_API_KEY` is set correctly
- **Discord not working**: Confirm `DISCORD_WEBHOOK_URL_TWITTER` is valid

### Adding New Accounts
Edit `TWITTER_ACCOUNTS` in `.env`:
```bash
TWITTER_ACCOUNTS="pokegetinfomain,other_account,third_account"
```

## 📋 Available Scripts Summary

| Script | Purpose | Run Frequency |
|--------|---------|---------------|
| `scripts/market_monitor.py` | Renaiss arbitrage detection | Continuous (5min loop) |
| `scripts/twitter_monitor.py` | Twitter news monitoring | Continuous (30min loop) |
| `scripts/market_report_vision.py` | Image analysis engine | On-demand |
