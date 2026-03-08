import requests
import json
import re

url = "https://www.renaiss.xyz/marketplace"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>', resp.text)
if match:
    try:
        data = json.loads(match.group(1))
        queries = data.get('props', {}).get('pageProps', {}).get('trpcState', {}).get('json', {}).get('queries', [])
        found_cards = False
        for q in queries:
            query_key = q.get('queryKey', [])
            if any(isinstance(k, str) and ('collectible.list' in k or 'item' in k) for k in query_key):
                items = q.get('state', {}).get('data', {}).get('json', [])
                if isinstance(items, list) and len(items) > 0:
                    found_cards = True
                    print(f"Found {len(items)} cards in structured data!")
                    print("Sample of first card metadata:")
                    print(json.dumps(items[0], indent=2, ensure_ascii=False))
                    break
        
        if not found_cards:
            print("Could not find collectible list inside __NEXT_DATA__")
            
    except Exception as e:
        print(f"Error parsing json: {e}")
else:
    print("__NEXT_DATA__ not found.")
