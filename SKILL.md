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

## Usage & Setup
Before starting the monitor, you **MUST** configure the `.env` file:

1.  **Initialize .env**: Run `cp .env.example .env` in the project root.
2.  **Configure Webhook**: Open `.env` and fill in your `DISCORD_WEBHOOK_URL`.
3.  **Adjust Thresholds (Optional)**:
    - `WINDOW_DAYS`: Historical average window (Default: 30).
    - `PRICE_THRESHOLD`: Min arbitrage profit (Default: 20.0).

### Command
```bash
python3 market_monitor.py
```

## Agent Capabilities
- **Incremental Monitoring**: The monitor tracks seen items and only processes genuine NEW listings in subsequent cycles, protecting Jina API rate limits.
- **Fast Response**: Polling interval is set to 1 minute to detect new listings rapidly.
- **Status Reporting**: Read `market_monitor.log` or the startup output to know the current configuration.
