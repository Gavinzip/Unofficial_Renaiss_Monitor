# SKILL: Market Arbitrage Monitor 📈

## Description
This skill enables the AI agent to monitor the Renaiss marketplace in real-time and identify arbitrage opportunities by comparing current asking prices with 30-day historical averages from PriceCharting and SNKRDUNK.

## Configuration (Adjustable)
The monitor can be adjusted by the user or the AI agent through the following environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DISCORD_WEBHOOK_URL` | The URL for Discord notifications. | None |
| `WINDOW_DAYS` | The time window (in days) used for historical averages. | `30` |
| `PRICE_THRESHOLD` | The price difference ($ USD) required to trigger an alert. | `20.0` |

## How to use
An AI agent can "adjust" the skill by asking the user to set these environment variables or by modifying the launch command:

```bash
# Example: 7-day window with a strict $50 threshold
export WINDOW_DAYS=7
export PRICE_THRESHOLD=50
python3 -u market_monitor.py
```

## Agent Capabilities
- **Incremental Monitoring**: The monitor tracks seen items and only processes genuine NEW listings in subsequent cycles, protecting Jina API rate limits.
- **Fast Response**: Polling interval is set to 1 minute to detect new listings rapidly.
- **Status Reporting**: Read `market_monitor.log` or the startup output to know the current configuration.
