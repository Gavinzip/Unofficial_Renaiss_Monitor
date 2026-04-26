from __future__ import annotations

from . import bootstrap as _bootstrap
from . import editorial as _editorial

globals().update(vars(_bootstrap))
globals().update(vars(_editorial))

# Domain: MiniMax refine, X/Twitter providers, Discord provider, thread merge

def minimax_chat(prompt: str, api_key: str, max_tokens: int | None = None) -> str:
    model_name = str(
        os.getenv("MINIMAX_TEXT_MODEL")
        or os.getenv("MINIMAX_MODEL")
        or "MiniMax-M2.7"
    ).strip() or "MiniMax-M2.7"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "reasoning_split": False,
    }
    token_limit = None
    env_limit = str(os.getenv("MINIMAX_TEXT_MAX_TOKENS") or "").strip()
    if env_limit:
        try:
            token_limit = int(env_limit)
        except Exception:
            token_limit = None
    if token_limit is not None and token_limit > 0:
        payload["max_tokens"] = int(token_limit)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(MINIMAX_URL, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    direct = data.get("reply") or data.get("output_text") or data.get("text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    base_resp = data.get("base_resp") if isinstance(data.get("base_resp"), dict) else {}
    status_msg = str(base_resp.get("status_msg") or "").strip()
    if status_msg:
        raise RuntimeError(f"MiniMax response error: {status_msg}")
    raise RuntimeError(f"MiniMax response missing content; model={model_name}")


def apply_minimax_story_refine(cards: list[StoryCard], api_key: str, feedback_context: str = "") -> None:
    for card in cards:
        prompt = (
            "你是TCG社群編輯。請先完整讀懂內容，再輸出『非抄寫』重整版本。"
            "輸出必須是 JSON，欄位固定為："
            "title,summary,bullets(長度3),card_type(layout可選:poster/brief/data/timeline),"
            "confidence(0~1),tags(最多3),event_facts(可選，僅 event 使用: reward/participation/audience/location/schedule),"
            "topic_labels(可多選: events/official/sbt/pokemon/alpha/tools/other)。"
            "限制："
            "1) 不可逐句複製原文；"
            "2) summary 要用第三人稱重述；"
            "3) bullets 每條都要是可行動或可追蹤的資訊；"
            "4) card_type 只能是 event/feature/announcement/market/report/insight；"
            "5) 必須用語意判斷分類，不可只用關鍵字；"
            "6) 只有含明確活動訊號（時間/地點/報名/參與方式）才可標為 event；"
            "7) 產品進度、版本更新、開放計畫優先標為 feature 或 announcement，不算 event；"
            "8) 單句互動、祝賀、表情、聊天回覆通常是 insight；"
            "9) topic_labels 可以多選，允許同時屬於 events 與 sbt（例如活動獎勵包含 SBT）；"
            "10) 繁體中文，不可捏造；"
            "11) 禁止使用『核心訊號/關鍵數字/決策建議/判讀建議/分析主題/文中數據/使用方式』這種模板詞；"
            "12) 若出現數字，必須說明它代表什麼（單位/情境/用途），不能只列數字；"
            "13) summary 需涵蓋『發生了什麼、為何重要、影響誰、下一步該看什麼』；"
            "14) 若為串文(thread)或多段內容，先整合後再輸出單一版本；"
            "15) 禁止空話（例如『社群互動貼文、重點在現場動態與回饋』），必須寫出實際更新內容；"
            "16) 禁止猜測語氣（例如『可能/通常/推測/大概』），除非原文明確使用該語氣；"
            "17) 若提到數字，必須同句交代該數字對應的對象與意義（例如價格、版本、名額、成交）；"
            "18) 不可使用 Markdown code fence（```）；"
            "19) 長度限制：title<=40字、summary<=150字、每條bullet<=34字；"
            "20) 若使用者回饋記憶與原始推斷衝突，以使用者回饋記憶優先；"
            "21) 整份 JSON 請控制在約 800 字元內。\n\n"
            + (f"[使用者回饋記憶]\n{feedback_context}\n\n" if feedback_context else "")
            + f"來源帳號: @{card.account}\n"
            f"來源URL: {card.url}\n"
            f"內容: {card.raw_text[:4200]}"
        )
        try:
            raw = minimax_chat(prompt, api_key)
            parsed = parse_json_block(raw)
            if not parsed:
                compact_retry_prompt = (
                    "請直接輸出合法 JSON，不要任何前後文字，不要 ```。"
                    "欄位固定：title,summary,bullets(3),card_type,layout,tags,confidence,event_facts,topic_labels。"
                    "全部繁體中文，且每欄位要短：title<=40字、summary<=120字、每條bullet<=30字。"
                    "不可捏造，需依據提供內容。\n\n"
                    f"帳號:@{card.account}\n"
                    f"URL:{card.url}\n"
                    f"內容:{card.raw_text[:3200]}"
                )
                raw = minimax_chat(compact_retry_prompt, api_key)
                parsed = parse_json_block(raw)
            if not parsed:
                continue
            title = str(parsed.get("title") or "").strip()
            summary = str(parsed.get("summary") or "").strip()
            bullets = parsed.get("bullets") if isinstance(parsed.get("bullets"), list) else []
            card_type = str(parsed.get("card_type") or "").strip().lower()
            layout = str(parsed.get("layout") or "").strip().lower()
            tags = parsed.get("tags") if isinstance(parsed.get("tags"), list) else []
            confidence = parsed.get("confidence")
            event_facts = normalize_event_facts(parsed.get("event_facts"))
            topic_labels = normalize_topic_labels(parsed.get("topic_labels"))
            detail_summary = clean_text(str(parsed.get("detail_summary") or ""))[:420]
            detail_lines = normalize_detail_lines(parsed.get("detail_lines"), limit=6)

            if title:
                card.title = title[:120]
            if summary:
                card.summary = summary[:320]
            if bullets:
                card.bullets = [clean_text(str(x))[:120] for x in bullets if str(x).strip()][:3] or card.bullets
            if card_type in {"event", "market", "report", "announcement", "feature", "insight"}:
                card.card_type = card_type
            if layout in {"poster", "brief", "data", "timeline"}:
                card.layout = layout
            if tags:
                card.tags = [clean_text(str(x))[:16] for x in tags if str(x).strip()][:3]
            if isinstance(confidence, (int, float)):
                card.confidence = float(max(0.0, min(1.0, confidence)))
            if card.card_type == "event" and event_facts:
                card.event_facts = event_facts
            if topic_labels:
                card.topic_labels = topic_labels
            if detail_summary:
                card.detail_summary = detail_summary
            if detail_lines:
                card.detail_lines = detail_lines
            if (
                similarity_ratio(card.summary, card.raw_text) > 0.92
                or _summary_needs_rewrite(card.summary, card.raw_text)
                or _bullets_need_rewrite([clean_text(str(x)) for x in (card.bullets or [])], card.raw_text)
                or (card.card_type == "market" and _market_is_number_dump(card.summary, [clean_text(str(x)) for x in (card.bullets or [])]))
            ):
                fallback = build_editorial_copy(card.raw_text, card.card_type, card.account)
                card.summary = str(fallback.get("summary") or card.summary)[:320]
                fb = fallback.get("bullets")
                if isinstance(fb, list) and fb:
                    card.bullets = [clean_text(str(x))[:120] for x in fb if str(x).strip()][:3]
            enrich_detail_view(card)
            card.importance = score_card(card)
            enrich_card_metadata(card)
            normalize_card_semantics(card, preserve_type=True)
        except Exception:
            continue


def parse_json_block(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def aggregate_digest(
    cards: list[StoryCard],
    sections: dict[str, list[dict[str, Any]]],
    key_terms: list[str],
    api_key: str | None = None,
) -> dict[str, Any]:
    cards_sorted = sorted(cards, key=lambda c: c.published_at, reverse=True)
    top_titles = [f"- @{c.account}: {c.title}" for c in cards_sorted[:8]]

    digest = {
        "headline": "Spring AI 關鍵情報總結",
        "conclusion": "已從高訊號貼文中整理出官方更新、近期活動、即將開放與社群焦點，避免被零散回覆淹沒。",
        "takeaways": [
            "先看官方更新，確認產品與活動方向。",
            "近期活動用時間與參與方式呈現，減少漏看。",
            "社群焦點只保留有訊息密度的貼文，不再全貼。",
        ],
        "accounts_active": sorted({c.account for c in cards_sorted}),
        "key_terms": key_terms[:12],
    }

    if not api_key or not cards_sorted:
        return digest

    prompt = (
        "你是TCG情報總編。請根據貼文標題與四個情報分類，輸出 JSON：headline,conclusion,takeaways(長度3)。"
        "語氣要像『春季資訊刊』，但保持專業，繁體中文，不可捏造。\n\n"
        + "\n".join(top_titles)
        + "\n\n[official_updates]\n"
        + "\n".join(f"- {x['headline']}" for x in sections.get("official_updates", [])[:4])
        + "\n\n[upcoming_events]\n"
        + "\n".join(f"- {x['headline']}" for x in sections.get("upcoming_events", [])[:4])
        + "\n\n[upcoming_features]\n"
        + "\n".join(f"- {x['headline']}" for x in sections.get("upcoming_features", [])[:4])
    )
    try:
        raw = minimax_chat(prompt, api_key)
        parsed = parse_json_block(raw)
        if parsed:
            digest["headline"] = str(parsed.get("headline") or digest["headline"])[:80]
            digest["conclusion"] = str(parsed.get("conclusion") or digest["conclusion"])[:220]
            tks = parsed.get("takeaways")
            if isinstance(tks, list) and tks:
                digest["takeaways"] = [clean_text(str(x))[:90] for x in tks if str(x).strip()][:3]
    except Exception:
        pass

    return digest


def fetch_status_with_twitter_cli(url: str) -> str | None:
    if not shutil_which("twitter"):
        return None
    try:
        proc = subprocess.run(
            ["twitter", "tweet", url, "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=35,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        data = json.loads(proc.stdout)
        content = str(data.get("full_text") or data.get("text") or "").strip()
        if not content:
            return None
        created = str(data.get("created_at") or "").strip()
        title = f'Title: X on X: "{content}" / X\n\nURL Source: {url}\n'
        if created:
            title += f"\nPublished Time: {created}\n"
        title += f"\nMarkdown Content:\n{content}\n"
        return title
    except Exception:
        return None


def parse_datetime_guess(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None

    candidates = [raw]
    if raw.endswith("Z"):
        candidates.append(raw.replace("Z", "+00:00"))

    for cand in candidates:
        try:
            dt = datetime.fromisoformat(cand)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue

    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def parse_twitter_cli_output(stdout: str) -> list[dict[str, Any]]:
    text = (stdout or "").strip()
    if not text:
        return []

    parsed_objects: list[Any] = []
    try:
        parsed = json.loads(text)
        parsed_objects.append(parsed)
    except Exception:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed_objects.append(json.loads(line))
            except Exception:
                continue

    items: list[dict[str, Any]] = []
    for obj in parsed_objects:
        if isinstance(obj, list):
            for x in obj:
                if isinstance(x, dict):
                    items.append(x)
            continue
        if isinstance(obj, dict):
            candidate_lists = [
                obj.get("tweets"),
                obj.get("items"),
                obj.get("data"),
                obj.get("results"),
                obj.get("statuses"),
            ]
            expanded = False
            for arr in candidate_lists:
                if isinstance(arr, list):
                    expanded = True
                    for x in arr:
                        if isinstance(x, dict):
                            items.append(x)
            if not expanded:
                items.append(obj)
    return items


def build_storycard_from_twitter_cli_item(item: dict[str, Any], username: str) -> StoryCard | None:
    sid = str(item.get("id_str") or item.get("id") or item.get("tweet_id") or "").strip()
    if not sid:
        return None

    text = (
        item.get("full_text")
        or item.get("text")
        or item.get("content")
        or item.get("note_tweet", {}).get("text")
        or ""
    )
    text = clean_text(str(text))
    if len(text) < 8 or is_noise_text(text):
        return None

    created_raw = str(item.get("createdAt") or item.get("created_at") or item.get("date") or item.get("time") or "").strip()
    created_dt = parse_datetime_guess(created_raw) or snowflake_to_datetime(sid)
    url = str(item.get("url") or "").strip()
    if not url:
        url = f"https://x.com/{username}/status/{sid}"

    metrics_raw = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    metrics = {
        "likes": int(metrics_raw.get("likes", item.get("favorite_count", 0)) or 0),
        "retweets": int(metrics_raw.get("retweets", item.get("retweet_count", 0)) or 0),
        "replies": int(metrics_raw.get("replies", item.get("reply_count", 0)) or 0),
        "quotes": int(metrics_raw.get("quotes", item.get("quote_count", 0)) or 0),
        "views": int(metrics_raw.get("views", 0) or 0),
    }
    cover = extract_first_image(item.get("media"))
    reply_to_id = str(
        item.get("in_reply_to_status_id_str")
        or item.get("in_reply_to_status_id")
        or item.get("inReplyToStatusId")
        or ""
    ).strip()

    card_type, layout, tags = classify_story(text)
    shaped = build_editorial_copy(text, card_type, username)
    card = StoryCard(
        id=sid,
        account=username,
        url=url,
        title=str(shaped.get("title") or summarize_naive(text, 180)),
        summary=str(shaped.get("summary") or summarize_naive(text, 280)),
        bullets=shaped.get("bullets") if isinstance(shaped.get("bullets"), list) else extract_bullets(text),
        published_at=created_dt.isoformat(),
        confidence=0.7,
        card_type=card_type,
        layout=layout,
        tags=tags,
        raw_text=text[:2500],
        provider="twitter-cli",
        cover_image=cover,
        metrics=metrics,
        reply_to_id=reply_to_id,
    )
    card.importance = score_card(card)
    enrich_card_metadata(card)
    enrich_detail_view(card)
    return card


def fetch_account_cards_with_twitter_cli(
    username: str,
    since_dt: datetime,
    max_posts: int = DEFAULT_MAX_POSTS_PER_ACCOUNT,
) -> list[StoryCard]:
    if not shutil_which("twitter"):
        return []

    target_n = max(max_posts * 4, 36)
    commands = [
        ["twitter", "user-posts", username, "--json", "-n", str(target_n)],
        ["twitter", "search", "--from", username, "--json", "-n", str(target_n), "--exclude", "retweets"],
    ]

    cards: list[StoryCard] = []
    seen_ids: set[str] = set()
    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45,
                check=False,
            )
        except Exception:
            continue

        if proc.returncode != 0 or not proc.stdout.strip():
            continue

        for item in parse_twitter_cli_output(proc.stdout):
            card = build_storycard_from_twitter_cli_item(item, username=username)
            if not card:
                continue
            try:
                if datetime.fromisoformat(card.published_at) < since_dt:
                    continue
            except Exception:
                pass
            if card.id in seen_ids:
                continue
            seen_ids.add(card.id)
            cards.append(card)
            if len(cards) >= max_posts:
                return sorted(cards, key=lambda c: c.published_at, reverse=True)

        if cards:
            break

    cards.sort(key=lambda c: c.published_at, reverse=True)
    return cards[:max_posts]


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)


def fetch_status_markdown(username: str, tweet_id: str) -> tuple[str | None, str, dict[str, Any] | None]:
    url = f"https://x.com/{username}/status/{tweet_id}"
    meta = fetch_status_metadata(tweet_id)

    twitter_cli_data = fetch_status_with_twitter_cli(url)
    if twitter_cli_data:
        return twitter_cli_data, "twitter-cli", meta

    if isinstance(meta, dict):
        owner = str(meta.get("account") or "").strip().lower().lstrip("@")
        wanted = str(username or "").strip().lower().lstrip("@")
        if owner == wanted and str(meta.get("text") or "").strip():
            return build_markdown_from_status_meta(meta, url), "tweet-result", meta

    try:
        return fetch_text(f"https://r.jina.ai/http://x.com/{username}/status/{tweet_id}"), "r.jina.ai", meta
    except Exception:
        return None, "none", meta


def resolve_discord_monitor_config() -> dict[str, Any]:
    token = str(os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN") or "").strip()
    raw_channels = str(
        os.getenv("DISCORD_MONITOR_CHANNEL_IDS")
        or os.getenv("DISCORD_MONITOR_CHANNEL_ID")
        or ""
    ).strip()
    channels: list[str] = []
    for piece in re.split(r"[,\s]+", raw_channels):
        cid = piece.strip()
        if not cid or not re.fullmatch(r"\d{6,}", cid):
            continue
        channels.append(cid)
    channels = list(dict.fromkeys(channels))

    raw_limit = str(os.getenv("DISCORD_MONITOR_LIMIT") or DEFAULT_DISCORD_MONITOR_LIMIT).strip()
    try:
        limit = int(raw_limit)
    except Exception:
        limit = DEFAULT_DISCORD_MONITOR_LIMIT
    limit = max(10, min(100, limit))

    enabled_raw = str(os.getenv("DISCORD_MONITOR_ENABLED") or "").strip().lower()
    if enabled_raw in {"0", "false", "off", "no"}:
        enabled = False
    elif enabled_raw in {"1", "true", "on", "yes"}:
        enabled = True
    else:
        enabled = bool(token and channels)

    configured = bool(token and channels)
    return {
        "enabled": bool(enabled and configured),
        "configured": configured,
        "token": token,
        "channel_ids": channels,
        "limit": limit,
    }


def _discord_message_text(item: dict[str, Any]) -> str:
    parts: list[str] = [str(item.get("content") or "")]
    embeds = item.get("embeds") if isinstance(item.get("embeds"), list) else []
    for embed in embeds:
        if not isinstance(embed, dict):
            continue
        for key in ("title", "description"):
            val = str(embed.get(key) or "").strip()
            if val:
                parts.append(val)
        fields = embed.get("fields") if isinstance(embed.get("fields"), list) else []
        for field in fields:
            if not isinstance(field, dict):
                continue
            name = str(field.get("name") or "").strip()
            value = str(field.get("value") or "").strip()
            merged = " ".join(x for x in [name, value] if x)
            if merged:
                parts.append(merged)
    return clean_text(" ".join(parts))


def _discord_first_image(item: dict[str, Any]) -> str:
    attachments = item.get("attachments") if isinstance(item.get("attachments"), list) else []
    for att in attachments:
        if not isinstance(att, dict):
            continue
        content_type = str(att.get("content_type") or "").lower()
        is_image = content_type.startswith("image/") or bool(att.get("width"))
        if not is_image:
            continue
        url = str(att.get("proxy_url") or att.get("url") or "").strip()
        if url.startswith("http"):
            return url
    embeds = item.get("embeds") if isinstance(item.get("embeds"), list) else []
    for embed in embeds:
        if not isinstance(embed, dict):
            continue
        image = embed.get("image") if isinstance(embed.get("image"), dict) else {}
        thumbnail = embed.get("thumbnail") if isinstance(embed.get("thumbnail"), dict) else {}
        for source in (image, thumbnail):
            url = str(source.get("proxy_url") or source.get("url") or "").strip()
            if url.startswith("http"):
                return url
    return ""


def _discord_message_url(item: dict[str, Any], channel_id: str, message_id: str) -> str:
    guild_id = str(item.get("guild_id") or "").strip()
    if guild_id:
        return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
    return f"https://discord.com/channels/@me/{channel_id}/{message_id}"


def fetch_discord_channel_messages(channel_id: str, token: str, limit: int = DEFAULT_DISCORD_MONITOR_LIMIT) -> list[dict[str, Any]]:
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "RenaissIntelDiscordMonitor/1.0",
    }
    params = {"limit": max(1, min(limit, 100))}
    url = f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code >= 400:
        body = clean_text(resp.text or "")[:120]
        raise RuntimeError(f"HTTP {resp.status_code} {body}".strip())
    data = resp.json()
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def build_storycard_from_discord_message(item: dict[str, Any], channel_id: str) -> StoryCard | None:
    mid = str(item.get("id") or "").strip()
    if not mid:
        return None

    text = _discord_message_text(item)
    if len(text) < 8 or is_noise_text(text):
        return None

    created_raw = str(item.get("timestamp") or item.get("edited_timestamp") or "").strip()
    created_dt = parse_datetime_guess(created_raw) or datetime.now(timezone.utc)
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    account = str(author.get("global_name") or author.get("username") or author.get("id") or "discord").strip()
    reply_to_id = ""
    message_ref = item.get("message_reference") if isinstance(item.get("message_reference"), dict) else {}
    if message_ref:
        reply_to_id = str(message_ref.get("message_id") or "").strip()
    if not reply_to_id:
        referenced = item.get("referenced_message") if isinstance(item.get("referenced_message"), dict) else {}
        reply_to_id = str(referenced.get("id") or "").strip()

    card_type, layout, tags = classify_story(text)
    shaped = build_editorial_copy(text, card_type, account)
    card = StoryCard(
        id=f"discord-{channel_id}-{mid}",
        account=account,
        url=_discord_message_url(item, channel_id, mid),
        title=str(shaped.get("title") or summarize_naive(text, 180)),
        summary=str(shaped.get("summary") or summarize_naive(text, 280)),
        bullets=shaped.get("bullets") if isinstance(shaped.get("bullets"), list) else extract_bullets(text),
        published_at=created_dt.isoformat(),
        confidence=0.66,
        card_type=card_type,
        layout=layout,
        tags=tags,
        raw_text=text[:2500],
        provider="discord-rest",
        cover_image=_discord_first_image(item),
        metrics={},
        reply_to_id=reply_to_id,
    )
    card.importance = score_card(card)
    enrich_card_metadata(card)
    enrich_detail_view(card)
    return card


def collect_discord_cards(
    channel_ids: list[str],
    token: str,
    since_dt: datetime,
    limit_per_channel: int = DEFAULT_DISCORD_MONITOR_LIMIT,
) -> tuple[list[StoryCard], dict[str, int], list[str]]:
    cards: list[StoryCard] = []
    stats: dict[str, int] = {}
    errors: list[str] = []

    for cid in channel_ids:
        produced = 0
        try:
            messages = fetch_discord_channel_messages(cid, token=token, limit=limit_per_channel)
        except Exception as exc:
            errors.append(f"{cid}: {clean_text(str(exc))[:120]}")
            stats[cid] = 0
            continue

        for item in messages:
            created_raw = str(item.get("timestamp") or item.get("edited_timestamp") or "").strip()
            created_dt = parse_datetime_guess(created_raw)
            if created_dt and created_dt < since_dt:
                continue
            card = build_storycard_from_discord_message(item, channel_id=cid)
            if not card:
                continue
            cards.append(card)
            produced += 1
        stats[cid] = produced

    uniq: dict[str, StoryCard] = {}
    for c in cards:
        uniq[c.id] = c
    ordered = list(uniq.values())
    ordered.sort(key=lambda c: c.published_at, reverse=True)
    return ordered, stats, errors


def collect_account_cards(username: str, since_dt: datetime, max_posts: int = DEFAULT_MAX_POSTS_PER_ACCOUNT) -> list[StoryCard]:
    cached_payload = read_json(data_dir() / "x_intel_feed.json", {})
    cached_cards_raw = cached_payload.get("cards") if isinstance(cached_payload, dict) else []
    cached_cards: list[StoryCard] = []
    if isinstance(cached_cards_raw, list):
        for item in cached_cards_raw:
            try:
                if str(item.get("account", "")).lower() != username.lower():
                    continue
                published = str(item.get("published_at") or "")
                published_dt = datetime.fromisoformat(published) if published else datetime.now(timezone.utc)
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                if published_dt < since_dt:
                    continue
                provider_raw = str(item.get("provider") or "cache")
                if provider_raw.startswith("twitter-cli") and not shutil_which("twitter"):
                    provider_raw = "cache"
                cached_cards.append(
                    StoryCard(
                        id=str(item.get("id") or ""),
                        account=str(item.get("account") or username),
                        url=str(item.get("url") or ""),
                        title=str(item.get("title") or ""),
                        summary=str(item.get("summary") or ""),
                        bullets=[str(x) for x in item.get("bullets", []) if str(x).strip()][:3],
                        published_at=published_dt.isoformat(),
                        confidence=float(item.get("confidence") or 0.55),
                        card_type=str(item.get("card_type") or "insight"),
                        layout=str(item.get("layout") or "brief"),
                        tags=[str(x) for x in item.get("tags", []) if str(x).strip()][:3],
                        raw_text=str(item.get("raw_text") or ""),
                        provider=provider_raw,
                        cover_image=str(item.get("cover_image") or ""),
                        metrics=item.get("metrics") if isinstance(item.get("metrics"), dict) else {},
                        importance=float(item.get("importance") or 0.0),
                        template_id=str(item.get("template_id") or "community_brief"),
                        glance=str(item.get("glance") or ""),
                        timeline_date=str(item.get("timeline_date") or ""),
                        urgency=str(item.get("urgency") or "normal"),
                        manual_pick=bool(item.get("manual_pick") or False),
                        manual_pin=bool(item.get("manual_pin") or False),
                        manual_bottom=bool(item.get("manual_bottom") or False),
                        event_facts=normalize_event_facts(item.get("event_facts")),
                        topic_labels=normalize_topic_labels(item.get("topic_labels")),
                        detail_summary=str(item.get("detail_summary") or ""),
                        detail_lines=normalize_detail_lines(item.get("detail_lines"), limit=6),
                        reply_to_id=str(item.get("reply_to_id") or ""),
                    )
                )
            except Exception:
                continue

    cards: list[StoryCard] = fetch_account_cards_with_twitter_cli(
        username=username,
        since_dt=since_dt,
        max_posts=max_posts,
    )

    ids: list[str] = []
    for _ in range(3):
        profile_text = fetch_profile_page(username)
        ids = extract_status_ids(profile_text, username)
        if ids:
            break

    if len(ids) < max_posts:
        rss_ids = fetch_account_status_ids_from_nitter_rss(
            username,
            limit=max(max_posts * 10, 60),
        )
        if rss_ids:
            existing = set(ids)
            for sid in rss_ids:
                if sid in existing:
                    continue
                existing.add(sid)
                ids.append(sid)

    # fallback: keep previously cached IDs for stability when profile page is rate-limited
    if not ids:
        if isinstance(cached_cards_raw, list):
            for item in cached_cards_raw:
                if str(item.get("account", "")).lower() == username.lower() and item.get("id"):
                    ids.append(str(item["id"]))
        deduped: list[str] = []
        seen_ids: set[str] = set()
        for sid in ids:
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            deduped.append(sid)
        ids = deduped

    seen_card_ids: set[str] = {c.id for c in cards if c.id}
    queue: list[str] = []
    queued: set[str] = set()
    processed: set[str] = set()

    def enqueue_status_id(value: str) -> None:
        sid = str(value or "").strip()
        if not sid or sid in queued:
            return
        queued.add(sid)
        queue.append(sid)

    for sid in ids:
        enqueue_status_id(sid)
    for c in cards:
        if c.id:
            enqueue_status_id(c.id)

    max_fetch_rounds = max(max_posts * 8, 48)
    max_collected = max(max_posts * 3, 24)
    while queue and len(processed) < max_fetch_rounds:
        tweet_id = queue.pop(0)
        if tweet_id in processed:
            continue
        processed.add(tweet_id)

        try:
            if snowflake_to_datetime(tweet_id) < (since_dt - timedelta(days=2)):
                continue
        except Exception:
            continue

        status_markdown, provider, tweet_meta = fetch_status_markdown(username, tweet_id)
        if isinstance(tweet_meta, dict):
            reply_to_id = str(tweet_meta.get("reply_to_id") or tweet_meta.get("parent_id") or "").strip()
            reply_to_account = str(tweet_meta.get("reply_to_account") or tweet_meta.get("parent_account") or "").strip().lower().lstrip("@")
            if reply_to_id and reply_to_account == username.lower().lstrip("@"):
                enqueue_status_id(reply_to_id)

        if status_markdown:
            for rid in extract_status_ids(status_markdown, username):
                if rid != tweet_id:
                    enqueue_status_id(rid)

        if tweet_id in seen_card_ids:
            existing = next((x for x in cards if x.id == tweet_id), None)
            if existing and isinstance(tweet_meta, dict):
                if not existing.reply_to_id:
                    existing.reply_to_id = str(tweet_meta.get("reply_to_id") or tweet_meta.get("parent_id") or "").strip()
                if not existing.cover_image:
                    existing.cover_image = str(tweet_meta.get("cover_image") or "").strip()
                meta_text = clean_text(str(tweet_meta.get("text") or ""))
                if meta_text and len(meta_text) > len(clean_text(existing.raw_text or "")):
                    existing.raw_text = meta_text[:2500]
            continue

        if not status_markdown:
            continue

        card = parse_status_page(
            status_markdown,
            username=username,
            tweet_id=tweet_id,
            url=f"https://x.com/{username}/status/{tweet_id}",
            provider=provider,
            tweet_meta=tweet_meta,
        )
        if not card:
            continue
        cards.append(card)
        seen_card_ids.add(card.id)
        if len(cards) >= max_collected:
            break

    if cached_cards:
        merged: dict[str, StoryCard] = {c.id: c for c in cached_cards if c.id}
        for c in cards:
            merged[c.id] = c
        cards = list(merged.values())

    cards = merge_reply_chain_cards(cards)
    cards = merge_numbered_thread_cards(cards)
    cards.sort(key=lambda c: c.published_at, reverse=True)
    return cards[:max_posts]


def _thread_index(text: str) -> int | None:
    src = strip_links_mentions(clean_text(text))
    if not src:
        return None
    m = THREAD_PREFIX_RE.match(src)
    if not m:
        return None
    try:
        idx = int(m.group(1))
    except Exception:
        return None
    if 1 <= idx <= 20:
        return idx
    return None


def _thread_seed(text: str) -> str:
    src = strip_links_mentions(clean_text(text))
    src = THREAD_PREFIX_RE.sub("", src)
    return compact_point(src, 180)


def _content_token_set(text: str) -> set[str]:
    src = strip_links_mentions(clean_text(text)).lower()
    tokens = set(re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", src))
    stop = {
        "renaiss", "protocol", "official", "community", "today", "tonight",
        "我們", "今天", "今晚", "這次", "活動", "更新", "分享",
    }
    return {x for x in tokens if x not in stop}


def _token_overlap_ratio(a: str, b: str) -> float:
    a_set = _content_token_set(a)
    b_set = _content_token_set(b)
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / max(1, min(len(a_set), len(b_set)))


def _sum_metrics(cards: list[StoryCard]) -> dict[str, int]:
    out: dict[str, int] = {"likes": 0, "retweets": 0, "replies": 0, "quotes": 0, "views": 0}
    for card in cards:
        metrics = card.metrics if isinstance(card.metrics, dict) else {}
        for key in out:
            out[key] += int(metrics.get(key, 0) or 0)
    return out


def _merge_thread_group(group: list[StoryCard]) -> StoryCard:
    rows = sorted(group, key=lambda c: parse_datetime_guess(c.published_at) or datetime.now(timezone.utc))
    parts: list[str] = []
    for card in rows:
        idx = _thread_index(card.raw_text or card.title)
        prefix = f"{idx}/ " if idx else ""
        body = clean_text(card.raw_text or card.summary or card.title)
        if body:
            parts.append(f"{prefix}{body}")
    merged_raw = "\n\n".join(parts)[:7000]
    first = rows[0]
    last = rows[-1]
    tag_seen: set[str] = set()
    tags: list[str] = []
    for card in rows:
        for tag in card.tags or []:
            t = str(tag or "").strip()
            if not t or t in tag_seen:
                continue
            tag_seen.add(t)
            tags.append(t)
            if len(tags) >= 4:
                break
        if len(tags) >= 4:
            break
    cover = ""
    for card in rows:
        if card.cover_image:
            cover = card.cover_image
            break
    merged = StoryCard(
        id=first.id,
        account=first.account,
        url=first.url,
        title=first.title,
        summary=last.summary or first.summary,
        bullets=(last.bullets or first.bullets)[:3],
        published_at=last.published_at,
        confidence=max(float(c.confidence or 0.0) for c in rows),
        card_type=last.card_type,
        layout=last.layout,
        tags=tags[:3] if tags else (last.tags or first.tags or ["觀點"]),
        raw_text=merged_raw,
        provider=last.provider or first.provider,
        cover_image=cover,
        metrics=_sum_metrics(rows),
        reply_to_id=str(first.reply_to_id or ""),
    )
    merged.importance = max(float(c.importance or 0.0) for c in rows) + 0.8
    enrich_card_metadata(merged)
    enrich_detail_view(merged)
    return merged


def merge_reply_chain_cards(cards: list[StoryCard]) -> list[StoryCard]:
    if not cards:
        return cards

    by_account: dict[str, list[StoryCard]] = {}
    for card in cards:
        by_account.setdefault(card.account.lower(), []).append(card)

    merged_cards: list[StoryCard] = []
    member_ids: set[str] = set()

    for _account, rows in by_account.items():
        id_map: dict[str, StoryCard] = {c.id: c for c in rows if c.id}
        if len(id_map) < 2:
            continue

        dsu_parent: dict[str, str] = {sid: sid for sid in id_map}

        def find(x: str) -> str:
            while dsu_parent[x] != x:
                dsu_parent[x] = dsu_parent[dsu_parent[x]]
                x = dsu_parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra = find(a)
            rb = find(b)
            if ra != rb:
                dsu_parent[rb] = ra

        for card in rows:
            sid = card.id
            parent_id = str(card.reply_to_id or "").strip()
            if not sid or not parent_id or parent_id == sid:
                continue
            if parent_id in id_map:
                union(sid, parent_id)

        groups: dict[str, list[StoryCard]] = {}
        for sid, card in id_map.items():
            root = find(sid)
            groups.setdefault(root, []).append(card)

        for group in groups.values():
            if len(group) < 2:
                continue
            ordered = sorted(group, key=lambda c: parse_datetime_guess(c.published_at) or datetime.now(timezone.utc))
            dt_min = parse_datetime_guess(ordered[0].published_at) or datetime.now(timezone.utc)
            dt_max = parse_datetime_guess(ordered[-1].published_at) or dt_min
            # 避免把跨太久的不同討論硬合併成一張卡。
            if (dt_max - dt_min).total_seconds() > 5 * 24 * 3600:
                continue
            merged = _merge_thread_group(ordered)
            merged_cards.append(merged)
            for row in ordered:
                member_ids.add(row.id)

    if not merged_cards:
        return cards

    merged_by_id = {m.id: m for m in merged_cards}
    out: list[StoryCard] = []
    inserted_ids: set[str] = set()
    for card in cards:
        if card.id not in member_ids:
            out.append(card)
            continue
        replacement = merged_by_id.get(card.id)
        if replacement is None:
            continue
        if replacement.id in inserted_ids:
            continue
        out.append(replacement)
        inserted_ids.add(replacement.id)

    for merged in merged_cards:
        if merged.id in inserted_ids:
            continue
        if any(c.id == merged.id for c in out):
            continue
        out.append(merged)
        inserted_ids.add(merged.id)
    return out


def _find_neighbor_non_indexed(
    rows_sorted: list[StoryCard],
    pivot: StoryCard,
    direction: int,
    used_ids: set[str],
    max_hours: int = 12,
) -> StoryCard | None:
    if not rows_sorted:
        return None
    try:
        idx = rows_sorted.index(pivot)
    except ValueError:
        return None
    if direction not in {-1, 1}:
        return None

    base_dt = parse_datetime_guess(pivot.published_at) or datetime.now(timezone.utc)
    base_seed = _thread_seed(pivot.raw_text or pivot.title)
    base_topic = infer_topic_phrase(pivot.raw_text or pivot.title, pivot.card_type)
    p = idx + direction
    while 0 <= p < len(rows_sorted):
        cand = rows_sorted[p]
        p += direction
        if cand.id in used_ids:
            continue
        if _thread_index(cand.raw_text or cand.title):
            continue
        cand_dt = parse_datetime_guess(cand.published_at) or datetime.now(timezone.utc)
        if abs((cand_dt - base_dt).total_seconds()) > max_hours * 3600:
            continue
        cand_seed = _thread_seed(cand.raw_text or cand.title)
        cand_topic = infer_topic_phrase(cand.raw_text or cand.title, cand.card_type)
        overlap = _token_overlap_ratio(base_seed, cand_seed)
        topic_match = dedupe_key(base_topic) == dedupe_key(cand_topic)
        if overlap >= 0.18 or topic_match:
            return cand
    return None


def merge_numbered_thread_cards(cards: list[StoryCard]) -> list[StoryCard]:
    if not cards:
        return cards

    by_account: dict[str, list[StoryCard]] = {}
    for card in cards:
        by_account.setdefault(card.account.lower(), []).append(card)

    member_ids_in_merged: set[str] = set()
    merged_cards: list[StoryCard] = []

    for _account, rows in by_account.items():
        rows_sorted = sorted(rows, key=lambda c: parse_datetime_guess(c.published_at) or datetime.now(timezone.utc))
        n = len(rows_sorted)
        i = 0
        while i < n:
            base = rows_sorted[i]
            base_idx = _thread_index(base.raw_text or base.title)
            if not base_idx:
                i += 1
                continue
            base_dt = parse_datetime_guess(base.published_at) or datetime.now(timezone.utc)
            base_seed = _thread_seed(base.raw_text or base.title)
            base_topic = infer_topic_phrase(base.raw_text or base.title, base.card_type)

            group = [base]
            last_idx = base_idx
            j = i + 1
            while j < n:
                cand = rows_sorted[j]
                cand_idx = _thread_index(cand.raw_text or cand.title)
                if not cand_idx:
                    j += 1
                    continue
                cand_dt = parse_datetime_guess(cand.published_at) or datetime.now(timezone.utc)
                if abs((cand_dt - base_dt).total_seconds()) > 48 * 3600:
                    j += 1
                    continue
                cand_seed = _thread_seed(cand.raw_text or cand.title)
                cand_topic = infer_topic_phrase(cand.raw_text or cand.title, cand.card_type)
                overlap = _token_overlap_ratio(base_seed, cand_seed)
                topic_match = dedupe_key(base_topic) == dedupe_key(cand_topic)
                index_related = (
                    abs(cand_idx - last_idx) <= 10
                    or abs(cand_idx - base_idx) <= 10
                )
                if (overlap >= 0.2 or topic_match) and index_related:
                    group.append(cand)
                    last_idx = max(last_idx, cand_idx)
                    if len(group) >= 6:
                        break
                j += 1

            if group:
                group_sorted = sorted(group, key=lambda c: parse_datetime_guess(c.published_at) or datetime.now(timezone.utc))
                head = group_sorted[0]
                tail = group_sorted[-1]
                root_neighbor = _find_neighbor_non_indexed(rows_sorted, head, direction=-1, used_ids=member_ids_in_merged)
                tail_neighbor = _find_neighbor_non_indexed(rows_sorted, tail, direction=1, used_ids=member_ids_in_merged)
                if root_neighbor and all(root_neighbor.id != c.id for c in group):
                    group.append(root_neighbor)
                if tail_neighbor and all(tail_neighbor.id != c.id for c in group):
                    group.append(tail_neighbor)

            if len(group) >= 2:
                merged = _merge_thread_group(group)
                merged_cards.append(merged)
                for c in group:
                    member_ids_in_merged.add(c.id)
            i += 1

    if not merged_cards:
        return cards

    out: list[StoryCard] = []
    inserted_ids: set[str] = set()
    for card in cards:
        if card.id in member_ids_in_merged:
            if card.id in inserted_ids:
                continue
            replacement = next((m for m in merged_cards if m.id == card.id), None)
            if replacement is not None:
                out.append(replacement)
                inserted_ids.add(card.id)
            continue
        out.append(card)
    for merged in merged_cards:
        if merged.id not in inserted_ids and all(c.id != merged.id for c in out):
            out.append(merged)
            inserted_ids.add(merged.id)
    return out


def normalize_x_url(input_url: str) -> str:
    raw = (input_url or "").strip()
    if not raw:
        raise ValueError("empty URL")
    if raw.startswith("http://"):
        raw = "https://" + raw[len("http://") :]
    if not raw.startswith("https://"):
        raw = "https://" + raw

    parsed = urlparse(raw)
    if parsed.netloc not in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
        raise ValueError("only x.com/twitter.com URLs are supported")
    path = parsed.path.strip("/")
    match = STATUS_RE.search(f"https://x.com/{path}")
    if not match:
        raise ValueError("invalid tweet URL")

    username, tweet_id = match.group(1), match.group(2)
    return f"https://x.com/{username}/status/{tweet_id}"


def build_card_from_url(tweet_url: str, api_key: str | None = None) -> StoryCard:
    normalized = normalize_x_url(tweet_url)
    match = STATUS_RE.search(normalized)
    if not match:
        raise ValueError("invalid tweet URL")
    username, tweet_id = match.group(1), match.group(2)

    status_markdown, provider, tweet_meta = fetch_status_markdown(username, tweet_id)
    if not status_markdown:
        raise RuntimeError("unable to fetch tweet")
    card = parse_status_page(
        status_markdown,
        username,
        tweet_id,
        normalized,
        provider=provider,
        tweet_meta=tweet_meta,
    )
    if not card:
        raise RuntimeError("unable to parse tweet")

    if api_key:
        apply_minimax_story_refine([card], api_key, feedback_context=feedback_training_text())

    return card


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


