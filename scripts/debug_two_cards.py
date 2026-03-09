import os
import sys
import json
import re

# Insert path to market_monitor if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import market_report_vision as mrv
from market_monitor import fetch_and_analyze_realtime, clean_price

# 目標卡片
TARGETS = [
    "PSA 10 Gem Mint 2014 Pokemon Japanese Xy Tidal Storm #051 M Gardevoir Ex",
    "PSA 10 Gem Mint 2025 Pokemon Simplified Chinese Sv-P Promo #004 Pikachu"
]

JSON_FILE = "/Users/gavin/.gemini/antigravity/playground/luminescent-cosmos/test/json/renaiss_market_20260309_144121.json"

def get_attributes_from_json(target_name):
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item.get("name") == target_name:
                    return item.get("attributes", [])
    except Exception as e:
        print(f"Error loading JSON: {e}")
    return []

def main():
    debug_dir = os.path.join(os.path.dirname(__file__), "debug_specific_cards")
    os.makedirs(debug_dir, exist_ok=True)
    
    print(f"Starting debug run for 2 specific cards. Logs will be in {debug_dir}")
    print("-" * 60)

    for idx, full_name in enumerate(TARGETS, 1):
        safe_name = re.sub(r'[^A-Za-z0-9_]', '_', full_name)[:50]
        item_debug_dir = os.path.join(debug_dir, f"{idx:02d}_{safe_name}")
        os.makedirs(item_debug_dir, exist_ok=True)
        mrv._set_debug_dir(item_debug_dir)
        
        # 模擬 fetch_and_analyze_realtime 前面的準備工作
        company = full_name.split()[0] if "PSA" in full_name or "BGS" in full_name else "Unknown"
        year_match = re.search(r'20\d{2}', full_name)
        year = year_match.group(0) if year_match else 0
        
        attributes = get_attributes_from_json(full_name)
        
        print(f"\n[{idx}] 正在測試: {full_name}")
        print(f"  └ Company: {company}, Year: {year}")
        if attributes:
            print(f"  └ 找到結構化屬性: {attributes}")
        else:
            print(f"  └ 未在 JSON 中找到完全匹配的紀錄，將使用名稱解析 (Regex fallback)")
            
        try:
            # Fake item_id
            item_id = f"test-id-{idx}"
            pc_res, snkr_res = fetch_and_analyze_realtime(
                item_id, full_name, company, year, current_jpy_rate=150.0, attributes=attributes
            )
            print(f"\n✅ 分析完成:")
            print(f"  PC 結果: {pc_res}")
            print(f"  SNKR 結果: {snkr_res}")
            print("-" * 60)
        except Exception as e:
            print(f"\n❌ 分析失敗: {e}")
            print("-" * 60)

if __name__ == "__main__":
    main()
