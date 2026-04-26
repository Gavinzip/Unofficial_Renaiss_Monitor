#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 website/scripts/sync_doc.py
python3 website/scripts/sync_x_intel.py --days 30 --accounts "TCGRWA,ChenYichiao,renaissxyz"

echo "Source data refreshed: website/data/renaiss_doc_index.json"
echo "X intel feed refreshed: website/data/x_intel_feed.json"
