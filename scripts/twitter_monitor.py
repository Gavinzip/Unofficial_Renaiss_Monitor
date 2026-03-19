import os
import json
import re
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TWITTER_ACCOUNTS = os.getenv("TWITTER_ACCOUNTS", "pokegetinfomain").split(",")
TWITTER_ACCOUNTS = [acc.strip() for acc in TWITTER_ACCOUNTS if acc.strip()]

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL_TWITTER")
CHECK_INTERVAL_MINUTES = int(os.getenv("TWITTER_CHECK_INTERVAL", "30"))

SEEN_TWEETS_FILE = "scripts/seen_tweets.json"


def load_seen_tweets():
    if os.path.exists(SEEN_TWEETS_FILE):
        with open(SEEN_TWEETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen_tweets(data):
    os.makedirs("scripts", exist_ok=True)
    with open(SEEN_TWEETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_tweets_via_jina(username):
    url = f"https://r.jina.ai/https://x.com/{username}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Jina fetch failed for @{username}: {e}")
        return None


def extract_tweets(content, username):
    pattern = rf"https://x\.com/{re.escape(username)}/status/(\d+)"
    tweet_ids = re.findall(pattern, content, re.IGNORECASE)
    tweet_ids = list(dict.fromkeys(tweet_ids))
    tweets = []
    for tid in tweet_ids:
        tweets.append({
            "id": tid,
            "url": f"https://x.com/{username}/status/{tid}"
        })
    return tweets


def extract_tweet_content(content, username):
    pattern = rf"https://x\.com/{re.escape(username)}/status/\d+"
    blocks = re.split(pattern, content, flags=re.IGNORECASE)
    contents = []
    for block in blocks:
        block = block.strip()
        if block and len(block) > 10:
            block = re.sub(r"\[Image \d+.*?\]", "", block)
            block = re.sub(r"!\[\d+\].*?\)", "", block)
            block = re.sub(r"Image \d+:.*", "", block)
            block = re.sub(r"\|", " ", block)
            block = re.sub(r"\s+", " ", block)
            block = block.strip()
            if block and len(block) > 5:
                contents.append(block)
    return contents


def summarize_with_minimax(tweets_data, username):
    if not MINIMAX_API_KEY:
        print("⚠️ MINIMAX_API_KEY not set, skipping summarization")
        return None

    api_key = MINIMAX_API_KEY.strip().replace('\u2028', '').replace('\n', '').replace('\r', '')

    tweet_summaries = []
    for tweet in tweets_data[:5]:
        tweet_summaries.append(f"• {tweet['content'][:500]}")

    prompt = f"""你是一個寶可夢卡片新聞的專業摘要員。請用繁體中文整理以下推文內容，整理成簡潔的重點摘要。

**目標格式：**
📰 【新聞標題】
• 重點1
• 重點2
• 重點3

**推文來源：** @{username}

**原始內容：**
{chr(10).join(tweet_summaries)}

請直接輸出摘要，不要加任何標記或額外說明。"""

    url = "https://api.minimax.io/v1/text/chatcompletion_v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000
    }

    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip()
        except Exception as e:
            print(f"⚠️ MiniMax API error (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(2)
    return None


def send_to_discord(summary, username, new_tweet_count):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL_TWITTER not set, skipping Discord notification")
        return False

    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")
    embed = {
        "embeds": [
            {
                "title": f"🐦 @{username} 最新推文摘要",
                "description": summary or "（無摘要內容）",
                "color": 5811263,
                "url": f"https://x.com/{username}",
                "footer": {
                    "text": f"📅 {timestamp} | 📊 {new_tweet_count} 篇新推文"
                },
                "thumbnail": {
                    "url": "https://abs-0.twimg.com/emoji/v2/svg/1f426.svg"
                }
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed, timeout=15)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Discord webhook error: {e}")
        return False


def main():
    print(f"\n{'='*50}")
    print(f"🐦 Twitter Monitor Started")
    print(f"⏰ Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    print(f"📋 Accounts: {', '.join(['@' + acc for acc in TWITTER_ACCOUNTS])}")
    print(f"{'='*50}\n")

    seen_tweets = load_seen_tweets()
    total_new = 0

    for account in TWITTER_ACCOUNTS:
        print(f"\n🔍 Checking @{account}...")

        content = fetch_tweets_via_jina(account)
        if not content:
            continue

        tweets = extract_tweets(content, account)
        tweet_contents = extract_tweet_content(content, account)

        account_seen = seen_tweets.get(account, [])
        new_tweets = []

        for i, tweet in enumerate(tweets):
            if tweet["id"] not in account_seen:
                new_tweets.append({
                    "id": tweet["id"],
                    "url": tweet["url"],
                    "content": tweet_contents[i] if i < len(tweet_contents) else ""
                })

        if new_tweets:
            print(f"  ✨ Found {len(new_tweets)} new tweet(s)!")
            total_new += len(new_tweets)

            tweets_for_summary = []
            for tweet in new_tweets[:5]:
                tweets_for_summary.append({
                    "id": tweet["id"],
                    "content": tweet["content"]
                })

            summary = summarize_with_minimax(tweets_for_summary, account)

            if send_to_discord(summary, account, len(new_tweets)):
                print(f"  ✅ Sent to Discord!")
            else:
                print(f"  ⚠️ Failed to send to Discord")

            for tweet in new_tweets:
                account_seen.append(tweet["id"])

            seen_tweets[account] = account_seen[-100:]

            print(f"\n📝 Summary Preview:")
            print("-" * 40)
            print(summary[:500] if summary else "(no summary)")
            print("-" * 40)
        else:
            print(f"  ✅ No new tweets")

        time.sleep(2)

    save_seen_tweets(seen_tweets)

    if total_new > 0:
        print(f"\n🎉 Total new tweets this round: {total_new}")
    else:
        print(f"\n😴 No new tweets this round.")


if __name__ == "__main__":
    main()
