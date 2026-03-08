---
name: renassis-market-arbitrage-monitor
description: A portable, end-to-end guide for AI agents to operate, debug, and configure the Renassis Market Arbitrage Monitor.
---

# Renassis Market Arbitrage Monitor: Field Manual for AI Agents

This skill enables an AI agent to operate a real-time arbitrage detection system. The monitor scans the **Renaiss Marketplace**, extracts card metadata (Name, Set, Number, Grade), and cross-references them against **PriceCharting (US Market)** and **SNKRDUNK (JP Market)** to find price gaps.

---

## 🏗 System Architecture & Workflow

1.  **Ingestion**: Fetches JSON data from Renaiss API (with cache-busting).
2.  **Deduplication**: Checks `scripts/seen_ids.txt`. If the `item_id` and `price` are unchanged, it skips the item.
3.  **Decomposition**: 
    - Uses `parse_renaiss_name()` to split strings by the `#` number (e.g., `"Sword & Shield #046 Snorlax Vmax"` -> Set: `Sword & Shield`, Card: `Snorlax Vmax`).
    - Prioritizes structured `attributes` from the API over regular expressions.
4.  **Instant Filter (Whitelist)**: If keywords match `scripts/whitelist.txt` AND the price satisfies the `<= [LIMIT]` condition (if present), it alerts **instantly** without further analysis.
5.  **Market Analysis**:
    - **PriceCharting**: Scrapes recent sales, matches the grade, filters outliers (IQR).
    - **SNKRDUNK**: Searches for Japanese equivalents, matches variants (Manga/Parallel).
6.  **Comparison**: If `(Market_Avg - List_Price) >= PRICE_THRESHOLD`, it triggers a high-priority alert.
7.  **Notification**: Sends formatted alerts to Discord Webhook and/or Terminal.

---

## 🚀 Deployment & Operational Commands

Always execute commands from the **project root directory**.

### 1. Basic Operation
```bash
python3 scripts/market_monitor.py
```
- Starts with a **Startup Test**: Analyzes the first 5 items regardless of history to verify connectivity.
- Enters a loop (default: 60s) for continuous monitoring.

### 2. Debug & Trace Mode
```bash
python3 scripts/market_monitor.py --debug <output_folder_path>
```
- Overrides silent mode and prints full comparison details to the terminal.
- Dumps `step1_meta.json` into the specified folder, showing exactly how the card name was parsed.

### 3. Clear Historical Cache
```bash
python3 scripts/market_monitor.py --clear-history
```
- **Action**: Deletes `scripts/seen_ids.txt`.
- **Use Case**: When you want the monitor to re-analyze every single listing currently on the market (e.g., after changing search logic).

---

## ⚙️ Configuration Files

### `.env` (Global Settings)
Located in the project root.
- `DISCORD_WEBHOOK_URL`: Your Discord channel webhook. If empty, alerts go to Terminal only.
- `PRICE_THRESHOLD`: Minimum dollar profit required to trigger a standard alert (default: `20.0`).
- `WINDOW_DAYS`: Number of days of historical sales to include in average calculation (default: `30`).

### `scripts/whitelist.txt` (Target Tracking)
Syntax rules:
- **Keyword Match**: `charizard vmax` (Triggers alert if name contains "charizard" and "vmax").
- **Price Cap**: `charizard vmax <= 1500` (Triggers only if price is $1500 or less).
- **Comments**: Any line starting with `#` is ignored.

---

## 🛠 Troubleshooting & Mental Model for Agents

As an AI agent, follow these diagnostic steps when encountering issues:

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **No alerts on repeat items** | `seen_ids.txt` is blocking them. | Run with `--clear-history` to reset. |
| **Search results are "NO_MATCH"** | Card name parsing failed (Name/Set noise). | Use `--debug` to check `step1_meta.json`. Adjust `parse_renaiss_name` regex if needed. |
| **Price looks weirdly low/high** | Outliers or wrong edition matched. | Check the `PC_URL` or `SNKR_URL` generated in the logs to see if it's the correct card page. |
| **Terminal appears frozen** | Loop is running but finding no new items. | Look for the heartbeat message: `🔃 正在掃描市場新掛單...`. |
| **Jina 429 Errors** | Rate limited by Jina AI reader. | This is normal under heavy load. The monitor will automatically skip and retry next cycle. |

---

## 📝 Best Practices for AI-to-AI Collaboration

- **Don't rewrite from scratch**: If search results are bad, check `extract_set_code_from_name` or `parse_renaiss_name` first.
- **Always Verify**: After making a code change, run `python3 scripts/test_snorlax.py` (or a similar test script) to confirm the parsing logic behaves as expected before pushing to the main loop.
- **Portability**: Keep paths relative to the project structure (`scripts/...`, `main/...`) so this guide works across different environments.
