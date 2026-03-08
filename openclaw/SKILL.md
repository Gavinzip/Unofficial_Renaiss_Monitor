---
name: openclaw
description: TCG Vision & Market Intelligence skill. Identifies card images and generates market reports.
---

# OpenClaw: TCG Vision & Market Intelligence

OpenClaw is a specialized skill for identifying TCG cards (Pokémon, One Piece) from images and providing real-time market valuations. It leverages vision models (MiniMax/OpenAI) and live web crawlers (PriceCharting, SNKRDUNK).

## 🛠 Usage Modes

### 1. Mode: JSON (Recognition Only)
Analyzes an image and returns structured metadata. Use this when you only need to know "what card is this?".
- **Command**: `python3 scripts/openclaw_facade.py <image_path> --mode json`
- **Output**: JSON object containing `name`, `number`, `set_code`, `grade`, `category`, etc.

### 2. Mode: FULL (Market Report)
Performs recognition AND crawls primary market sources to generate a human-readable arbitrage report and a visual poster.
- **Command**: `python3 scripts/openclaw_facade.py <image_path> --mode full`
- **Output**: Markdown text report and (optionally) generated poster images in the debug directory.

## ⚙️ Requirements
- Environment variables: `MINIMAX_API_KEY` or `OPENAI_API_KEY`.
- Core logic resides in `openclaw/market_report_vision.py`.
- Facade entry point: `scripts/openclaw_facade.py`.

## 🧪 Quick Test
To test if OpenClaw is working properly, run the test script:
```bash
python3 scripts/test_openclaw.py --image path/to/sample.jpg
```
