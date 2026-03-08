---
name: renassis-market-arbitrage-monitor
description: A comprehensive guide and real-time arbitrage monitor for the Renaiss marketplace, cross-referencing PriceCharting and SNKRDUNK.
---

# Renassis Market Arbitrage Monitor - Agent Operation Guide

🚨 **CRITICAL AGENT INSTRUCTION:** 
The very first time you are invoked with this skill by a user, you **MUST** immediately introduce this skill. 
1. Briefly explain what this monitor does (real-time arbitrage detection between Renaiss, PriceCharting, and SNKRDUNK).
2. Explicitly list all the **tunable parameters** available to the user (e.g., `PRICE_THRESHOLD`, `WINDOW_DAYS` in `.env`, and keyword rules in `scripts/whitelist.txt`).
3. Offer to configure these settings or start the monitor for them.

This skill automates the detection of profitable card listings on the Renaiss marketplace by comparing live asking prices against historical market averages on PriceCharting (US market) and SNKRDUNK (Japanese market).

---

## 🚀 Quick Start: How to Run the Monitor

As an AI, if the user asks you to "start monitoring", "run the bot", or "check for deals", you must execute the following commands in the terminal:

1. **Navigate to the Project Directory:**
   ```bash
   cd /Users/gavin/.gemini/antigravity/playground/luminescent-cosmos/renassis
   ```

2. **Execute the Monitor Script:**
   ```bash
   python3 scripts/market_monitor.py
   ```
   *Note: If the user wants to see detailed output in the terminal (for example, if they don't have a Discord Webhook set up), run it with the debug flag:*
   ```bash
   python3 scripts/market_monitor.py --debug debug_logs
   ```

---

## 🎯 The Whitelist (`scripts/whitelist.txt`)

The whitelist is a powerful feature that allows the user to specify cards they want to buy immediately, bypassing the slow market average checks. 

**As an agent, you must know how to edit this file for the user.**

*   **Location:** `scripts/whitelist.txt`
*   **Syntax Rules:**
    *   One rule per line.
    *   Case-insensitive (e.g., "Pikachu" and "pikachu" are the same).
    *   **Unconditional Match:** Just keywords. Example: `pikachu sv promo 001`. If a card name contains ALL of these words, it triggers immediately.
    *   **Conditional Match (Max Price):** Keywords followed by `<= PRICE`. Example: `snorlax vmax 046 <= 200.0`. It only triggers if the seller's asking price is less than or equal to $200.0.

**How to help the user:** If the user says "Add Snorlax Vmax to my whitelist under $150", you must use your file editing tools to append `snorlax vmax <= 150` to the `scripts/whitelist.txt` file.

---

## 🧠 Core Monitoring Logic (Explain this if the user asks)

1. **Incremental Scanning:** The monitor fetches all listings from Renaiss but only checks the **newest** listings to save time and API calls. It remembers what it has seen in a file called `seen_ids.txt`.
2. **Cross-Platform Analysis:** 
   *   **PriceCharting (PC):** Looks at the last 30 days of sales (adjustable) for graded cards (PSA/BGS/CGC).
   *   **SNKRDUNK (SNKR):** Looks at the Japanese market.
3. **Alert Trigger:** The bot calculates a "True Market Average" and compares it to the Renaiss seller's Ask Price. 
   *   `Alert = (Market Average) - (Ask Price) >= PRICE_THRESHOLD`

---

## ⚙️ Configuration & Environment (`.env`)

The core behavior is controlled by variables in the `.env` file located in the `renassis` root directory. **You should check and modify these if the user asks to change the bot's behavior.**

*   `DISCORD_WEBHOOK_URL`: The URL where alerts are sent. (If empty, alerts only print to the terminal, especially when `--debug` is used).
*   `PRICE_THRESHOLD`: (Default: `20.0`) The minimum profit margin in USD required to trigger an alert. If set to `10.0`, the system will alert if a card is listed $10 below market average.
*   `WINDOW_DAYS`: (Default: `30`) How many days of historical sales data to look back at when calculating the average market price.

---

## 🛠 Troubleshooting & Agent Commands

If the user complains that the bot isn't finding anything, or they want the bot to "restart from scratch", utilize these debugging steps:

### 1. Clearing Historical Memory
The bot remembers previously seen cards in `scripts/seen_ids.txt` to avoid duplicate alerts. If the user wants to re-scan the entire market, you **MUST** clear this history.
*   **Command:** 
    ```bash
    python3 scripts/market_monitor.py --clear-history
    ```
    *Execute this command on behalf of the user when they want to reset the bot's memory.*

### 2. Diagnosing Search Issues (Debug Mode)
If a specific card is failing to match correctly on SNKRDUNK or PriceCharting, run the monitor in debug mode.
*   **Command:**
    ```bash
    python3 scripts/market_monitor.py --debug my_test_dir
    ```
*   **What it does:** This forces the bot to create a folder (e.g., `my_test_dir`) and dump `step1_meta.json` files for every card it scans. You (the AI) can then read these JSON files to see exactly how the card name was split (e.g., `card_name`, `set_code`, `number`) to diagnose parsing errors.

### 3. Jina 429 Errors
If the terminal prints `429` errors, the system is hitting rate limits. Advise the user that the bot will automatically sleep and retry, but they may need to reduce how often they restart the script.
