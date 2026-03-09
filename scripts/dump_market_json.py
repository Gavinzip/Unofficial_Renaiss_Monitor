import os
import time
import requests
import re
import json
from datetime import datetime

def dump_renaiss_market_data():
    fetch_dir = "/Users/gavin/.gemini/antigravity/playground/luminescent-cosmos/test/json"
    os.makedirs(fetch_dir, exist_ok=True)

    url = f"https://www.renaiss.xyz/marketplace?_t={int(time.time())}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    try:
        print(f"Fetching data from {url}...")
        resp = requests.get(url, headers=headers, timeout=15)
        
        # 這是從市場頁面抓取原始 Next.js JSON 的正則邏輯
        pattern = r'\{\\"id\\":\\"[^"]+\\",\\"tokenId\\":\\"[^"]+\\".*?\\"buybackBaseValueInUSD\\":\\"[^"]+\\"\}'
        matches = re.finditer(pattern, resp.text)
        
        parsed_items = []
        for m in matches:
            try:
                raw_json_str = m.group(0).encode().decode('unicode_escape')
                data = json.loads(raw_json_str)
                parsed_items.append(data)
            except Exception as e:
                print(f"解析單筆項目失敗: {e}")
        
        if parsed_items:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            outfile = os.path.join(fetch_dir, f"renaiss_market_{timestamp}.json")
            
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(parsed_items, f, indent=4, ensure_ascii=False)
            
            print(f"✅ 成功抓取！一共 {len(parsed_items)} 筆掛單結構化資料已經儲存至：\n{outfile}")
        else:
            print("⚠️ 未找到任何結構化掛單資料。可能網站結構有變動。")
            
    except Exception as e:
        print(f"網路請求失敗: {e}")

if __name__ == "__main__":
    dump_renaiss_market_data()
