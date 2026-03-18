import requests
import re
import json
import time
from datetime import datetime, timedelta
import os
import sys
import argparse

# Import search functions locally
import market_report_vision as mrv
from dotenv import load_dotenv

# 📜 載入 .env 檔案 (推薦)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# 📝 手動設定區 (若不使用 .env，請直接在此修改引號內的內容)
# ---------------------------------------------------------
DEFAULT_DISCORD_WEBHOOK = ""  # 在此填入 Webhook 網址
DEFAULT_WINDOW_DAYS = 30                        # 價格計算窗口 (天)
DEFAULT_PRICE_THRESHOLD = -30.0                  # 報警價差門檻 (USD) (預設 -30 代表接受高於均價 30 元以內的提示)
# ---------------------------------------------------------

def _collect_webhook_urls(*raw_values):
    """Collect webhook URLs from multiple env vars, dedupe, and keep order."""
    urls = []
    for raw in raw_values:
        if not raw:
            continue
        for token in re.split(r"[\s,]+", str(raw).strip()):
            t = token.strip()
            if t and t not in urls:
                urls.append(t)
    return urls

DISCORD_WEBHOOK_URL_LEGACY = os.getenv("DISCORD_WEBHOOK_URL") or DEFAULT_DISCORD_WEBHOOK
DISCORD_WEBHOOK_URLS = _collect_webhook_urls(
    DISCORD_WEBHOOK_URL_LEGACY,
    os.getenv("DISCORD_WEBHOOK_URL_2"),
    os.getenv("DISCORD_WEBHOOK_URLS"),
)
WINDOW_DAYS = int(os.getenv("WINDOW_DAYS") or DEFAULT_WINDOW_DAYS)
PRICE_THRESHOLD = float(os.getenv("PRICE_THRESHOLD") or DEFAULT_PRICE_THRESHOLD)

# 📦 狀態管理：追蹤已處理過的掛單 ID
SEEN_IDS_FILE = os.path.join(os.path.dirname(__file__), "seen_ids.txt")
SEEN_IDS = {}

# 📣 報警冷卻管理：防止同一張卡短期內重覆轟炸
SEEN_NAMES_FILE = os.path.join(os.path.dirname(__file__), "seen_names.json")
SEEN_NAMES = {} # 格式: { "name_grade": { "last_price": 100.0, "last_time": 1709900000 } }

WHITELIST_FILE = os.path.join(os.path.dirname(__file__), "whitelist.txt")

def load_whitelist():
    """從檔案載入白名單關鍵字與條件"""
    if not os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
                f.write("# 在這裡輸入你想要追蹤的卡片關鍵字 (每行一個)\n"
                        "# 若要無條件觸發，例如: pikachu v 005\n"
                        "# 若要低於特定價格才觸發，請加上 <= 價格，例如: pikachu v 005 <= 1500\n"
                        "# 全部小寫模糊匹配\n")
        except: pass
        return []
    
    rules = []
    try:
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip().lower()
                if not line or line.startswith('#'):
                    continue
                
                max_price = None
                if "<=" in line:
                    parts = line.split("<=")
                    kw_str = parts[0].strip()
                    try:
                        max_price = float(parts[1].strip())
                    except ValueError:
                        pass
                else:
                    kw_str = line
                
                if kw_str:
                    rules.append({
                        "keywords": kw_str.split(),
                        "max_price": max_price,
                        "raw_rule": line
                    })
        return rules
    except Exception as e:
        print(f"⚠️ 載入 whitelist.txt 失敗: {e}")
        return []

def load_seen_ids():
    """從檔案載入已見過的 ID 與對應價格"""
    result = {}
    if os.path.exists(SEEN_IDS_FILE):
        try:
            with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split(":")
                    if len(parts) == 2:
                        iid, price = parts[0], round(float(parts[1]), 2)
                        result[iid] = price
                    else:
                        # 相容舊有的純 ID 格式
                        result[line] = 0.0
        except Exception as e:
            print(f"⚠️ 載入 seen_ids.txt 失敗: {e}")
    return result

def load_seen_names():
    """載入卡片名稱級別的報警歷史"""
    if os.path.exists(SEEN_NAMES_FILE):
        try:
            with open(SEEN_NAMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_seen_names():
    """儲存卡片名稱級別的報警歷史"""
    try:
        with open(SEEN_NAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(SEEN_NAMES, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 儲存 seen_names.json 失敗: {e}")

def save_seen_id(item_id, price=0.0):
    """將單一 ID 與價格追加到檔案中（覆蓋或新增交給檔案追加，讀檔時會以最新為準）"""
    try:
        with open(SEEN_IDS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{item_id}:{float(price):.2f}\n")
    except Exception as e:
        print(f"⚠️ 儲存 seen_ids 失敗: {e}")

def parse_date_string(date_str):
    """解析 PC 和 SNKR 的各種日期格式，返回 datetime 對象"""
    now = datetime.now()
    date_str = date_str.strip()
    
    # 1. 處理 YYYY-MM-DD (PC or SNKR)
    try:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        if re.match(r'^\d{4}/\d{2}/\d{2}$', date_str):
            return datetime.strptime(date_str, '%Y/%m/%d')
    except: pass
    
    # 2. 處理 Mar 8, 2024 (PC)
    try:
        if re.match(r'^[A-Z][a-z]{2}\s\d{1,2},\s\d{4}$', date_str):
            return datetime.strptime(date_str, '%b %d, %Y')
    except: pass
    
    # 3. 處理相對時間 (SNKRJP: 5 分前, 2 時間前, 3 日前)
    m = re.match(r'^(\d+)\s*(分|時間|日)前$', date_str)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        if unit == '分': return now - timedelta(minutes=val)
        if unit == '時間': return now - timedelta(hours=val)
        if unit == '日': return now - timedelta(days=val)

    # 4. 處理相對時間 (SNKREN: 5 minutes ago, 2 hours ago, 3 days ago)
    m = re.search(r'(\d+)\s+(minute|hour|day)', date_str, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        unit = m.group(2).lower()
        if unit == 'minute': return now - timedelta(minutes=val)
        if unit == 'hour': return now - timedelta(hours=val)
        if unit == 'day': return now - timedelta(days=val)
        
    return None

def calculate_source_average(records, target_grade, window_days=30):
    """計算特定來源在指定天數內的平均價（含等級匹配與誤差過濾）"""
    if not records:
        return None, 0
    
    now = datetime.now()
    all_prices = []
    
    # 匹配等級（考慮 Unknown -> Ungraded）
    snkr_target = target_grade.replace(" ", "")
    
    for r in records:
        r_grade = r.get('grade', '')
        # 建立匹配邏輯
        matched = False
        if r_grade == target_grade:
            matched = True
        elif target_grade == "Unknown" and r_grade in ("Ungraded", "裸卡", "A"):
            matched = True
        elif r_grade == snkr_target:
            matched = True
            
        if not matched:
            continue
            
        # 檢查日期窗口
        d_str = r.get('date', '')
        d_obj = parse_date_string(d_str)
        if d_obj:
            if now - d_obj > timedelta(days=window_days):
                continue
        elif d_str: # 如果有日期但解析失敗，預設保留（或可選擇略過）
            pass
            
        # 提取價格
        p = r.get('price')
        if p and p > 0:
            all_prices.append(float(p))
            
    if not all_prices:
        return None, 0
        
    # IQR 過濾離群值 (至少 4 筆才過濾)
    if len(all_prices) >= 4:
        s_prices = sorted(all_prices)
        n = len(s_prices)
        q1 = s_prices[n // 4]
        q3 = s_prices[(n * 3) // 4]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = [p for p in s_prices if lower <= p <= upper]
        prices_to_use = filtered if filtered else s_prices
    else:
        prices_to_use = all_prices
        
    avg = sum(prices_to_use) / len(prices_to_use)
    return avg, len(all_prices)

def fetch_jpy_rate():
    """實時獲取 美金對日圓(USD->JPY) 匯率"""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rate = data.get('rates', {}).get('JPY')
            if rate:
                return float(rate)
    except Exception as e:
        print(f"⚠️ 獲取實時匯率失敗 ({e})，使用預設值 150.0")
    return 150.0

def calculate_true_average_with_window(pc_records, snkr_records, target_grade):
    """(兼容舊版或輔助調用) 使用全局設定的天數計算均價"""
    pc_avg, pc_count = calculate_source_average(pc_records, target_grade, window_days=WINDOW_DAYS)
    snkr_avg, snkr_count = calculate_source_average(snkr_records, target_grade, window_days=WINDOW_DAYS)
    return (pc_avg, pc_count), (snkr_avg, snkr_count)
def extract_set_code_from_name(full_name):
    """從 full_name 提取 Set Code 短碼（如 S8b, sv2a, OP02, sv1s, SV5K, SV-P）
    優先順序：最長/最精確的匹配優先
    """
    # 寶可夢 Promo 系列 (優先匹配，因包含 dash)：SV-P, S-P, SM-P, XY-P 等
    m = re.search(r'\b(SV-P|S-P|SM-P|XY-P|BW-P|DP-P|L-P|ADV-P|SV-G|S8a-G)\b', full_name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
        
    # [FIX] 處理 "SV Promo" 或 "Sv Promo" 這種空格寫法，統一轉為 "SV-P"
    m = re.search(r'\b(SV|S|SM|XY|BW|DP|L|ADV)\s+Promo\b', full_name, re.IGNORECASE)
    if m:
        return f"{m.group(1).upper()}-P"
    # 航海王格式：OP+數字, ST+數字, EB+數字 (必須在寶可夢之前，避免被 SV 吃掉)
    m = re.search(r'\b(OP\d+|ST\d+|EB\d+)\b', full_name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # 寶可夢 SV 系列：SV+數字+可選字母 (e.g. SV5K, sv2a, SV1S)
    m = re.search(r'\b(SV\d+[A-Za-z]*)\b', full_name, re.IGNORECASE)
    if m:
        return m.group(1)
    # 寶可夢 SWSH 系列：S+數字+可選字母 (e.g. S8b, S9a, S12a)
    m = re.search(r'\b(S\d+[A-Za-z]?)\b', full_name)
    if m:
        # 防止誤匹配 SEC、SR 等縮寫
        candidate = m.group(1)
        if re.match(r'^S\d', candidate):
            return candidate
    # 寶可夢 Sun & Moon 系列：SM+數字+可選字母 (e.g. SM1+, SM8b)
    m = re.search(r'\b(SM\d*[A-Za-z+]?)\b', full_name, re.IGNORECASE)
    if m:
        return m.group(1)
    # 寶可夢 XY 系列：XY+數字+可選字母
    m = re.search(r'\b(XY\d*[A-Za-z]?)\b', full_name, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def parse_renaiss_name(full_name):
    """從 full_name 提取 grade, number, set_code, set_name, card_name
    注意：這只是後備方案，正確做法是優先從 attributes 取得結構化資料
    """
    # 1. 提取 grade
    grade_m = re.search(r'(PSA|BGS|CGC|SGC)\s+(\d+(?:\.\d+)?)', full_name)
    grade_tag = f"{grade_m.group(1)} {grade_m.group(2)}" if grade_m else "Unknown"

    # 2. 提取 set_code 短碼
    set_code = extract_set_code_from_name(full_name)

    # 3. 檢查有無卡片編號（#XXX 或 #XXX/YYY 格式），以此為界切分 系列名(前) 與 卡名(後)
    m = re.search(r'#([A-Za-z0-9]+(?:/[A-Za-z0-9-]+)?)', full_name)
    if m:
        number = m.group(1)
        before_num = full_name[:m.start()]
        after_num = full_name[m.end():]
        
        set_name_candidate = before_num
        card_name_candidate = after_num
    else:
        number = "0"
        set_name_candidate = full_name
        card_name_candidate = full_name

    # 4. 清洗 set_name (去除年份、語言、品相字眼)
    if grade_m:
        set_name_candidate = set_name_candidate.replace(grade_m.group(0), "")
    if set_code:
        set_name_candidate = re.sub(re.escape(set_code) + r'[^\s]*', '', set_name_candidate, flags=re.IGNORECASE).strip()
    set_name_candidate = re.sub(r'\b20\d{2}\b', '', set_name_candidate).strip()
    
    for kw in ["Pokemon", "Japanese", "English", "Simplified Chinese", "Traditional Chinese",
               "Korean", "Gem Mint", "Mint", "One Piece"]:
        set_name_candidate = re.sub(rf'\b{re.escape(kw)}\b', '', set_name_candidate, flags=re.IGNORECASE).strip()
    set_name = ' '.join(set_name_candidate.split())

    # 5. 清洗 card_name (去除雜訊字眼與版本字眼)
    if grade_m:
        card_name_candidate = card_name_candidate.replace(grade_m.group(0), "")
    
    # [FIX] 移除 redundant set_name 避免搜尋字串爆炸
    if set_name:
        # 嘗試移除 set_name 中已知的字眼，避免重複
        _sn_clean = set_name.lower().strip()
        _cn_clean = card_name_candidate.lower()
        if _sn_clean in _cn_clean:
             card_name_candidate = re.sub(re.escape(set_name), '', card_name_candidate, flags=re.IGNORECASE).strip()

    if set_code:
        card_name_candidate = re.sub(re.escape(set_code) + r'[^\s]*', '', card_name_candidate, flags=re.IGNORECASE).strip()
    card_name_candidate = re.sub(r'\b20\d{2}\b', '', card_name_candidate).strip()
    
    for kw in ["Pokemon", "Japanese", "English", "Simplified Chinese", "Traditional Chinese",
               "Korean", "Gem Mint", "Mint", "One Piece", "FOIL", "SP", "ALT ART", "Parallel", "WANTED", "Leader", "SEC", "SR", "Special Card", "Promo"]:
        card_name_candidate = re.sub(rf'\b{re.escape(kw)}\b', '', card_name_candidate, flags=re.IGNORECASE).strip()
    card_name = ' '.join(card_name_candidate.split())

    # 若切分完發現後半段是空的(可能是特例)，就 fallback 回 set_name
    if not card_name:
        card_name = set_name

    return card_name, number, set_code, set_name, grade_tag


def clean_price(v):
    if not v or v == "NO-OFFER-PRICE": return None
    v = v.replace("$n", "")
    if len(v) > 10:
        return round(float(v) / (10**18), 2)
    return round(float(v) / 100, 2)

def _price_to_cents(price):
    return int(round(float(price) * 100))

def fetch_market_data():
    url = f"https://www.renaiss.xyz/marketplace?_t={int(time.time())}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        # Capture the whole item JSON object
        pattern = r'\{\\"id\\":\\"[^"]+\\",\\"tokenId\\":\\"[^"]+\\".*?\\"buybackBaseValueInUSD\\":\\"[^"]+\\"\}'
        matches = re.finditer(pattern, resp.text)
        
        parsed_items = []
        for m in matches:
            try:
                raw_json_str = m.group(0).encode().decode('unicode_escape')
                data = json.loads(raw_json_str)
                token_id_raw = str(data.get("tokenId") or "")
                token_id_clean = token_id_raw.replace("$n", "").strip()
                item_id = str(data.get("itemId") or "")
                parsed_items.append({
                    "id": str(data.get("id")),
                    "item_id": item_id,
                    "name": data.get("name"),
                    "ask_price": clean_price(data.get("askPriceInUSDT")),
                    "fmv": clean_price(data.get("fmvPriceInUSD")),
                    "grade": f"{data.get('gradingCompany')} {data.get('grade')}",
                    "attributes": data.get("attributes", []),
                    "image_url": data.get("frontImageUrl", ""),
                    # Renaiss card URL expects tokenId (large integer), not itemId UUID.
                    "renaiss_url": (
                        f"https://www.renaiss.xyz/card/{token_id_clean}"
                        if token_id_clean
                        else (f"https://www.renaiss.xyz/card/{item_id}" if item_id else "https://www.renaiss.xyz/marketplace")
                    )
                })
            except: pass
        return parsed_items
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 網路請求失敗: {e}")
        return []

def fetch_and_analyze_realtime(item_id, full_name, grading_company, year, current_jpy_rate=150.0, attributes=None):
    """現場發動爬蟲並分析價格 (分開回傳 PC 與 SNKR 的數據)"""
    print(f"  🔍 正在對 {full_name} 進行實時市場分析... (匯率: 1 USD = {current_jpy_rate} JPY)")
    
    # ── Step 1: 用 regex 後備方案拆解 full_name ─────────────────────────────
    card_name, number, set_code, set_name, grade_tag = parse_renaiss_name(full_name)
    is_jp = "Japanese" in full_name
    category = "One Piece" if any(
        kw in full_name for kw in ["One Piece", "WANTED"]
    ) or (set_code and re.match(r'^(OP|ST|EB)\d', set_code, re.I)) else "Pokemon"

    # ── Step 2: 用 attributes (結構化資料) 覆蓋 regex 結果 ─────────────────
    # attributes 來自 Renaiss marketplace API，優先度高於 regex
    attr_number = ""
    attr_set_name = ""
    attr_language = ""
    attr_category = ""
    for attr in (attributes or []):
        t = attr.get("trait", "").lower()
        v = attr.get("value", "").strip()
        if not v:
            continue
        if t == "card number":
            attr_number = v.replace("#", "").strip()
        elif t == "set":
            attr_set_name = v
        elif t == "language":
            attr_language = v
        elif t == "category":
            attr_category = v

    # 覆蓋：attributes 優先
    if attr_number:
        number = attr_number
        print(f"    📋 attributes.card_number 覆蓋 → {number}")
    if attr_set_name:
        set_name = attr_set_name
        # 同時嘗試從 set_name 推斷 set_code（如果 regex 沒抓到的話）
        if not set_code:
            extracted = extract_set_code_from_name(attr_set_name)
            if extracted:
                set_code = extracted
        print(f"    📋 attributes.set 覆蓋 → set_name={set_name}, set_code={set_code or '(從名稱提取)'}")
    if attr_language:
        is_jp = "japanese" in attr_language.lower()
        print(f"    📋 attributes.language 覆蓋 → is_jp={is_jp}")
    if attr_category:
        category = attr_category
        print(f"    📋 attributes.category 覆蓋 → {category}")

    # 類別二次補強（以 set_code 輔助確認）
    if set_code and re.match(r'^(OP|ST|EB)\d', set_code, re.I):
        category = "One Piece"
    
    print(f"    🔑 搜尋參數 → name={card_name!r} | number={number!r} | set_code={set_code!r} | grade={grade_tag} | lang={'JP' if is_jp else 'EN'}")

    # ── Step 3: 變體偵測 ────────────────────────────────────────────────────
    variant_map = {
        "manga": ["コミパラ", "manga"],
        "parallel": ["パラレル"],
        "wanted": ["wanted"],
        "-sp": ["sp", "-sp"],
        "l-p": ["l-p"],
        "sr-p": ["sr-p"],
        "flagship": ["flagship", "フラッグシップ", "フラシ"]
    }
    snkr_variants = []
    name_lower = full_name.lower()
    for _kw, kws in variant_map.items():
        if any(kw in name_lower for kw in kws):
            snkr_variants.append(kws[0])
    is_alt_art = len(snkr_variants) > 0 or any(x in name_lower for x in ["special card", "alt art", "alternative"])

    # 輸出結構化的解析結果至 debug 資料夾，方便核對為什麼會這樣搜
    meta_json = {
        "name": card_name,
        "set_code": set_code,
        "number": number,
        "grade": grade_tag,
        "jp_name": "",
        "c_name": "",
        "category": category,
        "release_info": f"{year} - {set_name}" if set_name else str(year),
        "illustrator": "Unknown",
        "market_heat": "N/A",
        "features": ", ".join(snkr_variants) if snkr_variants else "",
        "collection_value": "N/A",
        "competitive_freq": "N/A",
        "is_alt_art": is_alt_art
    }
    mrv._debug_save("step1_meta.json", json.dumps(meta_json, indent=2, ensure_ascii=False))

    # ── Step 4: 執行搜尋 ────────────────────────────────────────────────────
    pc_records, pc_url, _ = mrv.search_pricecharting(
        name=card_name, number=number, set_code=set_code,
        target_grade=grade_tag, is_alt_art=is_alt_art, category=category,
        set_name=set_name
    )
    pc_avg, pc_count = calculate_source_average(pc_records, grade_tag, window_days=WINDOW_DAYS)

    snkr_records, _, snkr_url = mrv.search_snkrdunk(
        en_name=card_name, jp_name="", number=number, set_code=set_code,
        target_grade=grade_tag, is_alt_art=is_alt_art, card_language="JP" if is_jp else "EN",
        snkr_variant_kws=snkr_variants, set_name=set_name
    )
    snkr_avg_jpy, snkr_count = calculate_source_average(snkr_records, grade_tag, window_days=WINDOW_DAYS)
    snkr_avg_usd = (snkr_avg_jpy / current_jpy_rate) if snkr_avg_jpy else None

    return (pc_avg, pc_count, pc_url), (snkr_avg_usd, snkr_count, snkr_url)


def send_discord_alert(full_name, ask, pc_info, snkr_info, custom_trigger=None, debug_mode=False, image_url=None, renaiss_url=None):
    """發送 Discord Webhook 通知 (含雙來源詳細數據)。未設定 Webhook 或開啟 debug_mode 時將輸出至終端機。"""
    
    pc_avg, pc_count, pc_url = pc_info if pc_info else (None, 0, None)
    snkr_avg, snkr_count, snkr_url = snkr_info if snkr_info else (None, 0, None)

    fields = [
        {"name": "卡片名稱", "value": full_name, "inline": False},
        {"name": "賣家開價", "value": f"${ask:.2f} USD", "inline": True},
    ]
    
    if pc_avg:
        fields.append({"name": "PC 30天均價", "value": f"${pc_avg:.2f} USD ({pc_count}筆)", "inline": True})
    if snkr_avg:
        fields.append({"name": "SNKR 30天均價", "value": f"${snkr_avg:.2f} USD ({snkr_count}筆)", "inline": True})

    is_whitelist = "WHITELIST" in (custom_trigger or "")
    
    trigger_text = custom_trigger if custom_trigger else f"觸發來源: 價格判定 (門檻: ${PRICE_THRESHOLD})"
    title_text = "✨ 白名單指定卡片上架！" if is_whitelist else "發現套利機會！"
    color_code = 16766720 if is_whitelist else 16711680 # Gold for whitelist, red for arbitrage

    desc_links = []
    if renaiss_url: desc_links.append(f"[🛒 Renaiss]({renaiss_url})")
    if pc_url: desc_links.append(f"[🔗 PriceCharting]({pc_url})")
    if snkr_url: desc_links.append(f"[🔗 SNKRDUNK]({snkr_url})")
    desc_str = "\n".join(desc_links) if desc_links else "無可用的參考連結"

    # 如果沒有配置 Webhook 或開啟了 debug_mode，改版輸出至終端機
    if not DISCORD_WEBHOOK_URLS or debug_mode:
        print("\n" + "="*60)
        print("🔔 [終端機警報模式]")
        print(f"[{title_text}] {full_name}")
        print(f"開價: ${ask:.2f} USD")
        if pc_avg: print(f"PC 30天均價: ${pc_avg:.2f} USD ({pc_count}筆)")
        if snkr_avg: print(f"SNKR 30天均價: ${snkr_avg:.2f} USD ({snkr_count}筆)")
        print(f"{trigger_text}")
        print("="*60 + "\n")
        
    if not DISCORD_WEBHOOK_URLS:
        return

    embed = {
        "title": title_text,
        "color": color_code,
        "fields": fields,
        "description": f"**{trigger_text}**\n\n{desc_str}"
    }
    if image_url and isinstance(image_url, str) and image_url.startswith("http"):
        # Use thumbnail only to keep alert compact.
        embed["thumbnail"] = {"url": image_url}

    payload = {
        "content": f"🚨 **[{'白名單秒殺警告' if is_whitelist else '真正撿漏警報'}]** {full_name}",
        "embeds": [embed]
    }
    
    for webhook_url in DISCORD_WEBHOOK_URLS:
        try:
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"  ⚠️ Discord Webhook failed ({webhook_url[:40]}...): {e}")

# LEGACY: background_idle_update removed for real-time focus


def run_monitor_cycle(limit=None, force_process=False, debug_dir=None):
    """
    監控循環：
    - limit: 限制處理筆數 (用於啟動測試)
    - force_process: 是否忽略 SEEN_IDS 檢查 (用於啟動測試)
    - debug_dir: 儲存 debug 紀錄的資料夾
    """
    raw_items = fetch_market_data()
    if not raw_items:
        return
        
    if limit:
        raw_items = raw_items[:limit]
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🧪 測試模式：僅檢查前 {limit} 筆掛單...")
    
    # ── Step 1: 同週期去重 (同一張卡多個賣家時，只保留最划算的那個) ──────
    # 將卡片依據名稱與等級分組
    grouped_items = {}
    for it in raw_items:
        # 建立卡片唯一標識 (名稱 + 等級)
        # 注意：fetch_market_data 已經提供了 name 和 grade
        key = f"{it['name']}_{it['grade']}".lower()
        if key not in grouped_items:
            grouped_items[key] = it
        else:
            # 如果發現同款卡片更便宜的掛單，替換掉
            if float(it['ask_price']) < float(grouped_items[key]['ask_price']):
                grouped_items[key] = it
    
    items = list(grouped_items.values())

    # ── Step 2: 過濾已見過的 ID (如果是全新的 ID 或改價才處理) ──────────
    if not force_process:
        new_items = []
        for it in items:
            iid = it['item_id']
            ask = float(it['ask_price'])
            prev_ask = SEEN_IDS.get(iid)
            if prev_ask is None:
                new_items.append(it)
                continue

            ask_cents = _price_to_cents(ask)
            prev_cents = _price_to_cents(prev_ask)
            if ask_cents < prev_cents:
                new_items.append(it)
            elif ask_cents > prev_cents:
                # 漲價只更新追蹤狀態，不觸發重新分析
                SEEN_IDS[iid] = ask
                save_seen_id(iid, ask)
                print(f"  [價格上調] {it['name']} | ${float(prev_ask):.2f} -> ${ask:.2f} (不重報)")
                
        if not new_items:
            print(f"  └ 目前沒有發現新掛單或降價，將繼續監控...")
            return 
        items = new_items
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✨ 發現 {len(items)} 筆新品或價格異動上架，開始檢查...")
    else:
        if not limit:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 成功抓取 {len(items)} 筆掛單進行完全分析...")
    
    current_jpy_rate = fetch_jpy_rate()
    whitelist = load_whitelist()
    now_ts = time.time()
    
    for idx, item in enumerate(items, 1):
        if debug_dir:
            safe_name = re.sub(r'[^A-Za-z0-9_]', '_', item['name'])[:50]
            item_debug_dir = os.path.join(debug_dir, f"{idx:02d}_{safe_name}")
            os.makedirs(item_debug_dir, exist_ok=True)
            import market_report_vision as mrv
            mrv._set_debug_dir(item_debug_dir)

        item_id = item['item_id']
        ask = float(item['ask_price'])
        prev_ask = SEEN_IDS.get(item_id)
        is_price_drop_item = (
            prev_ask is not None and _price_to_cents(ask) < _price_to_cents(prev_ask)
        )
        full_name = item['name']
        grade = item['grade']
        name_grade_key = f"{full_name}_{grade}".lower()

        # ── Step 3: 名稱級別的報警冷卻與降價判斷 ─────────────────────
        # 邏輯：如果 1 小時內報過同一張卡，且沒降價超過 5%，就跳過通知
        def check_cooldown(p_key, current_p):
            if p_key in SEEN_NAMES:
                hist = SEEN_NAMES[p_key]
                last_time = hist.get("last_time", 0)
                last_price = hist.get("last_price", 999999)
                
                # 如果在 1 小時內
                if now_ts - last_time < 3600:
                    # 除非降價超過 5%
                    if current_p >= last_price * 0.95:
                        return True, last_price # 處於冷卻中
            return False, None

        # 白名單命中判斷
        is_whitelisted = False
        whitelist_triggered_rule = None
        full_name_lower = full_name.lower()
        for rule in whitelist:
            if all(kw in full_name_lower for kw in rule["keywords"]):
                if rule["max_price"] is None or ask <= rule["max_price"]:
                    is_whitelisted = True
                    whitelist_triggered_rule = rule
                    break
        
        if is_whitelisted and not debug_dir:
            is_cool = False
            old_p = None
            if is_price_drop_item:
                print(
                    f"  [降價重報] {full_name} | ${float(prev_ask):.2f} -> ${ask:.2f} "
                    f"(同 item_id 降價，略過冷卻)"
                )
            else:
                is_cool, old_p = check_cooldown(name_grade_key, ask)

            if is_cool:
                print(f"  [冷卻中] {full_name} | 現價: ${ask:.2f} | 上次報警: ${old_p:.2f} (1小時內且無過 5% 降幅，跳過通知)")
            else:
                print(f"\\n🌟 [白名單命中] {full_name}")
                print(f"   => 賣家開價: ${ask:.2f} USD")
                cond_str = f" (價格 \u003c= ${whitelist_triggered_rule['max_price']})" if whitelist_triggered_rule['max_price'] is not None else " (無條件)"
                print(f"   🔥 你的追蹤清單命中這張卡{cond_str}，發送通知！\\n")
                
                trigger_reason = f"WHITELIST 白名單命中{cond_str}"
                if is_price_drop_item:
                    trigger_reason += f" | 降價 ${float(prev_ask):.2f} -> ${ask:.2f}"
                send_discord_alert(
                    full_name, ask, None, None,
                    custom_trigger=trigger_reason,
                    debug_mode=bool(debug_dir),
                    image_url=item.get("image_url"),
                    renaiss_url=item.get("renaiss_url")
                )
                
                # 更新報警歷史
                SEEN_NAMES[name_grade_key] = {"last_time": now_ts, "last_price": ask}
                save_seen_names()

            # 無論是否通知，都要更新 ID 歷史避免重覆跑實時分析
            if item_id not in SEEN_IDS or SEEN_IDS[item_id] != ask:
                SEEN_IDS[item_id] = ask
                save_seen_id(item_id, ask)
            continue
        
        # [NEW] 如果在 Debug 且是白名單，我們繼續往下跑以產生 meta.json 和完整日誌
        if is_whitelisted and debug_dir:
             print(f"  [DEBUG] 白名單命中但繼續分析流程以產生 Log: {full_name}")
            
        # 1. 直接發動實時爬蟲 (市價查詢)
        company = full_name.split()[0] if "PSA" in full_name or "BGS" in full_name else "Unknown"
        year_match = re.search(r'20\d{2}', full_name)
        year = year_match.group(0) if year_match else 0
        pc_res, snkr_res = fetch_and_analyze_realtime(
            item_id, full_name, company, year, current_jpy_rate, attributes=item.get("attributes")
        )
        pc_avg, pc_count, pc_url = pc_res
        snkr_avg, snkr_count, snkr_url = snkr_res
        
        # 2. 獨立判斷折扣 (只要其中一個來源符合就報警)
        alert_pc = (pc_avg and (pc_avg - ask) >= PRICE_THRESHOLD)
        alert_snkr = (snkr_avg and (snkr_avg - ask) >= PRICE_THRESHOLD)
        
        # 日誌輸出
        log_parts = []
        if pc_avg: log_parts.append(f"PC({WINDOW_DAYS}d): ${pc_avg:.2f}")
        if snkr_avg: log_parts.append(f"SNKR({WINDOW_DAYS}d): ${snkr_avg:.2f}")
        print(f"  [掃描中] {full_name} | Ask: ${ask:.2f} | {' / '.join(log_parts) if log_parts else f'無{WINDOW_DAYS}天內數據'}")

        if alert_pc or alert_snkr:
            is_cool = False
            old_p = None
            if is_price_drop_item:
                 print(
                     f"  [降價重報] {full_name} | ${float(prev_ask):.2f} -> ${ask:.2f} "
                     f"(同 item_id 降價，略過冷卻)"
                 )
            else:
                is_cool, old_p = check_cooldown(name_grade_key, ask)

            if is_cool:
                 print(f"  [警報冷卻中] {full_name} 已滿足撿漏條件，但 1 小時內已發過通知且未顯著跌價，不重覆觸發。")
            else:
                triggered_by = []
                if alert_pc: triggered_by.append(f"PC(${(pc_avg-ask):.2f})")
                if alert_snkr: triggered_by.append(f"SNKR(${(snkr_avg-ask):.2f})")
                
                print(f"\n🚨 [真正撿漏警報] {full_name}")
                print(f"   => 賣家開價: ${ask:.2f} USD")
                print(f"   🔥 觸發來源: {' & '.join(triggered_by)}！(門檻: ${PRICE_THRESHOLD}, 窗口: {WINDOW_DAYS}天) 請立刻注意把這張卡買下來！\n")
                
                # 發送 Discord Webhook
                send_discord_alert(
                    full_name, ask, pc_res, snkr_res,
                    debug_mode=bool(debug_dir),
                    image_url=item.get("image_url"),
                    renaiss_url=item.get("renaiss_url")
                )
                
                # 更新報警歷史
                SEEN_NAMES[name_grade_key] = {"last_time": now_ts, "last_price": ask}
                save_seen_names()
        
        # 標記為已見過並持久化 (含最新價格)
        if item_id not in SEEN_IDS or _price_to_cents(SEEN_IDS[item_id]) != _price_to_cents(ask):
            SEEN_IDS[item_id] = float(ask)
            save_seen_id(item_id, float(ask))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renaiss Market Monitor")
    parser.add_argument("--debug", help="Enable debug mode and specify output directory for traces")
    parser.add_argument("--clear-history", action="store_true", help="Clear the seen_ids historical record")
    args = parser.parse_args()

    if args.clear_history:
        if os.path.exists(SEEN_IDS_FILE):
            os.remove(SEEN_IDS_FILE)
            print("🗑️  歷史紀錄 (seen_ids.txt) 已成功清空！")
        else:
            print("⚠️ 歷史紀錄已是空的，不需清空。")
        sys.exit(0)

    if args.debug:
        mrv._set_debug_dir(args.debug)
        print(f"🛠️ Debug 模式已開啟，詳細搜尋日誌將儲存至: {args.debug}")

    print("啟動 Renaiss 極致「全實時」監控機器人 (現場抓取分析模式)...")
    print(f"⚙️  當前設定: 價差門檻=${PRICE_THRESHOLD} USD | 時間窗口={WINDOW_DAYS} 天")
    if DISCORD_WEBHOOK_URLS:
        print(f"🔔  Discord 通知: 已開啟 ({len(DISCORD_WEBHOOK_URLS)} 個 webhook)")
    else:
        print("🔔  Discord 通知: 未開啟 (請設定 DISCORD_WEBHOOK_URL 或 DISCORD_WEBHOOK_URLS)")
    
    # 💥 初始狀態初始化：載入持久化數據 + 同步目前市場掛單
    print("📡 正在初始化市場狀態...")
    SEEN_IDS = load_seen_ids()
    SEEN_NAMES = load_seen_names()
    print(f"📂 已從檔案載入 {len(SEEN_IDS)} 筆 ID 記錄與 {len(SEEN_NAMES)} 筆報警歷史")
    
    try:
        initial_items = fetch_market_data()
        new_count = 0
        for it in initial_items:
            iid = it['item_id']
            ask = float(it['ask_price'])
            if iid not in SEEN_IDS or _price_to_cents(SEEN_IDS[iid]) != _price_to_cents(ask):
                SEEN_IDS[iid] = ask
                save_seen_id(iid, ask)
                new_count += 1
        print(f"✅ 已同步目前市場 {len(initial_items)} 筆掛單 (新增 {new_count} 筆至持久化)")
    except Exception as e:
        print(f"Initialization Failed: {e}")

    # 🚀 初次啟動：強行針對前 5 筆進行實時分析測試
    try:
        run_monitor_cycle(limit=5, force_process=True, debug_dir=args.debug)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🏁 啟動測試完成，5 秒後進入 1 分鐘循環監控...", flush=True)
        time.sleep(5)
    except Exception as e:
        print(f"Startup Test Failed: {e}", flush=True)

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔃 正在掃描市場新掛單...", flush=True)
            run_monitor_cycle(debug_dir=args.debug)
        except Exception as e:
            print(f"Monitor Crash: {e}", flush=True)

            
        time.sleep(60)
