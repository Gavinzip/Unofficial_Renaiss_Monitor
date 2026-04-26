#!/usr/bin/env bash

set -euo pipefail

API_BASE="${1:-${INTEL_API_BASE:-${INTEL_API_BASE_OVERRIDE:-https://gavinx.zeabur.app}}}"
TIMEOUT=10

echo "=== 1) API base ==="
echo "INTEL_API_BASE=${INTEL_API_BASE:-<empty>}"
echo "Using base: ${API_BASE}"
echo

echo "=== 2) Process / port check ==="
if command -v lsof >/dev/null 2>&1; then
  echo "--- LISTEN ports (5000/8787) ---"
  lsof -iTCP -sTCP:LISTEN -P 2>/dev/null | rg ":(5000|8787) " || echo "No process on 5000/8787 from lsof result."
else
  echo "lsof not available"
fi

echo "--- ai_intel_server.py processes ---"
if command -v pgrep >/dev/null 2>&1; then
  if pgrep -f "ai_intel_server.py" >/dev/null 2>&1; then
    pgrep -f "ai_intel_server.py"
  else
    echo "No ai_intel_server.py process found."
  fi
else
  echo "pgrep not available"
fi
echo

echo "=== 3) Env sanity ==="
if [ -f "${PWD}/.env" ]; then
  if command -v rg >/dev/null 2>&1; then
    echo "MINIMAX_API_KEY in .env: $(rg -n '^\\s*MINIMAX_API_KEY\\s*=\\s*' .env | sed 's/.*=//g' | head -n 1 | sed 's/....$/*xxx/')"
  else
    echo ".env exists, rg unavailable."
  fi
else
  echo "No .env at ${PWD}/.env"
fi
echo

echo "=== 4) Probe /api/intel/feed langs ==="
python3 - "$API_BASE" "$TIMEOUT" <<'PY'
import json
import sys
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

base = sys.argv[1]
timeout = int(sys.argv[2])
langs = ["zh-Hant", "zh-Hans", "en", "ko"]

for lang in langs:
    url = f"{base.rstrip('/')}/api/intel/feed?lang={lang}"
    try:
        with urlopen(url, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
    except HTTPError as e:
        print(f"[{lang}] HTTP {e.code} {e.reason}")
        continue
    except (URLError, TimeoutError) as e:
        print(f"[{lang}] request failed: {e}")
        continue
    except Exception as e:
        print(f"[{lang}] parse failed: {e}")
        continue

    if not data.get("ok"):
        print(f"[{lang}] ok=False error={data.get('error')}")
        continue

    feed = data.get("feed", {})
    i18n = feed.get("_i18n", {}) if isinstance(feed, dict) else {}
    state = i18n.get("state", {}) if isinstance(i18n, dict) else {}
    qa = i18n.get("qa", {}) if isinstance(i18n, dict) else {}
    lp = state.get("lang_progress", {}) if isinstance(state, dict) else {}
    entry = lp.get(lang, {}) if isinstance(lp, dict) else {}

    head = (feed.get("digest") or {}).get("headline", "")
    mode = i18n.get("mode", "")
    coverage = qa.get("coverage")
    state_status = state.get("status")
    print(f"[{lang}] mode={mode} coverage={coverage} state={state_status} build={entry.get('status')} mode={entry.get('mode')} done={entry.get('done')}/{entry.get('total')} remaining={entry.get('remaining')} percent={entry.get('percent')}")
    print(f"       headline={head[:60]}")
    print(f"       state_status={state_status} langs={state.get('langs', [])}")
    print()
PY

echo "=== Done ==="
