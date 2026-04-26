#!/usr/bin/env python3
"""Core pipeline for X account ingestion + AI digest rendering data."""

from __future__ import annotations

import json
import os
import re
import site
import subprocess
import sys
import time
from html import unescape
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse

import requests

from website_storage import get_website_data_dir

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback for minimal environments
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        return False

DEFAULT_ACCOUNTS = ["TCGRWA", "ChenYichiao", "renaissxyz", "davidcheang99"]
DEFAULT_WINDOW_DAYS = 30
DEFAULT_MAX_POSTS_PER_ACCOUNT = 20
DEFAULT_DISCORD_MONITOR_LIMIT = 80
DEFAULT_CURATED_MAX_CARDS = 24
MINIMAX_URL = "https://api.minimax.io/v1/text/chatcompletion_v2"
SYNDICATION_TWEET_URL = "https://cdn.syndication.twimg.com/tweet-result"
DISCORD_API_BASE_URL = "https://discord.com/api/v10"
ALLOWED_CARD_TYPES = {"event", "market", "report", "announcement", "feature", "insight"}
ALLOWED_TOPIC_LABELS = {"events", "official", "sbt", "pokemon", "alpha", "tools", "other"}
ALLOWED_FEEDBACK_LABELS = ALLOWED_CARD_TYPES | ALLOWED_TOPIC_LABELS | {"exclude"}
JINA_HOST = "r.jina.ai"
JINA_MIN_INTERVAL_SECONDS = 6.0
JINA_MAX_RETRIES = 3
JINA_RETRY_BASE_SECONDS = 0.9
JINA_RATE_LOCK = Lock()
JINA_LAST_REQUEST_AT = 0.0

STATUS_RE = re.compile(r"https?://x\.com/([A-Za-z0-9_]+)/status/(\d+)", re.I)
TITLE_RE = re.compile(r"^Title:\s*(.+?)\s*/\s*X\s*$", re.M | re.S)
PUBLISHED_RE = re.compile(r"^Published Time:\s*(.+)$", re.M)
MARKDOWN_RE = re.compile(r"Markdown Content:\s*(.*)$", re.S)
LINK_RE = re.compile(r"https?://[^\s)]+")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)]+)\)")
EVENT_SIGNAL_RE = re.compile(
    r"活動|\bevent\b|直播|\blive\b|\bama\b|\bspace\b|community\s*session|join us|報名|报名|\btour\b|\bfestival\b|開包活動|开包活动|参赛|參賽|竞猜|\bgathering\b|\bplaza\b|"
    r"goes live|restock(?:ing)?|poker night|get ready|drops?\b|開賣|开卖",
    re.I,
)
FEATURE_SIGNAL_RE = re.compile(
    r"progress update|roadmap|版本|version|beta|上線|上线|開放|开放|launch|功能|v2|2\.0|update|即將|coming|mfa|2fa|multi[-\s]*factor|authenticator|authentication|security|帳號安全|账号安全|登入保護|登录保护|setting page|設定頁|设置页",
    re.I,
)
GUIDE_SIGNAL_RE = re.compile(
    r"攻略|教學|教程|指南|心得|介紹|介绍|怎麼|怎么|如何|運費|运费|價格|价格|優點|缺點|集運|集运|buy and ship|分享",
    re.I,
)
LIVE_REWARD_RE = re.compile(
    r"((?:直播|live\s+(?:attendees?|session|stream)|ama|community\s*session).{0,42}(?:sbt|积分|積分|reward|rewards|奖励|獎勵|merch|周邊|周边))|"
    r"((?:sbt|积分|積分|reward|rewards|奖励|獎勵|merch|周邊|周边).{0,42}(?:直播|live\s+(?:attendees?|session|stream)|ama|community\s*session))",
    re.I,
)
PARTICIPATION_SIGNAL_RE = re.compile(
    r"join us|join on|register|signup|報名|报名|參與|参与|出席|attend|參加|参加|discord|space|直播|\blive\b|\bama\b|\bsession\b|地點|地点|venue|填表|投票|互動|互动|attendees?",
    re.I,
)
LOCATION_SIGNAL_RE = re.compile(
    r"hong\s*kong|taipei|台北|台灣|台湾|web3\s*festival|\btour\b|card\s*shop|\bplaza\b|\bvenue\b|線下|线下|\bmeetup\b|causeway\s*bay|restaurant|booth",
    re.I,
)
MARKET_SIGNAL_RE = re.compile(
    r"price|市場|市场|交易量|volume|成交|涨|漲|跌|估值|fmv|回購|回购|\$\d|sold\s+for|record\s*breaker",
    re.I,
)
ANNOUNCE_SIGNAL_RE = re.compile(
    r"announce|公告|發佈|发布|updated?|更新|official|官方|progress update|changelog|roadmap",
    re.I,
)
REPORT_SIGNAL_RE = re.compile(
    r"分析|report|投研|guide|教程|教學|教学|指南|策略|总结|總結|整理|懶人包|懒人包",
    re.I,
)
REWARD_SIGNAL_RE = re.compile(
    r"sbt|reward|rewards|獎勵|奖励|獎品|prize|airdrop|積分|积分|points?|merch|周邊|周边|coupon|白名單|whitelist",
    re.I,
)
AUDIENCE_SIGNAL_RE = re.compile(
    r"新手|玩家|觀眾|观众|社群|community|collectors?|holders?|參賽者|参赛者|all regions|多語|multi-language",
    re.I,
)
JOIN_SIGNAL_RE = re.compile(
    r"報名|报名|register|signup|join us|join on|填表|參與|参与|投票|互動|互动|discord|space|直播|\blive\b|\bama\b|\bsession\b|attendees?",
    re.I,
)
EVENT_LOCATION_RE = re.compile(
    r"香港|hong\s*kong|台北|taipei|線上|线上|discord|space|web3\s*festival|plaza|card\s*shop|場地|地点|venue",
    re.I,
)
REPORT_OPTION_START_RE = re.compile(
    r"(?:^|[\s。；;])(\d{1,2})\s*[\.、)\]]\s*([A-Za-z0-9\u4e00-\u9fff _&+\-]{2,40})\s*[:：]",
    re.I,
)
THREAD_PREFIX_RE = re.compile(r"^\s*(\d{1,2})\s*/\s*(?:\d{1,2})?\s*", re.I)
SBT_THRESHOLD_RE = re.compile(
    r"(?:(?:top|前)\s*([0-9]{1,3})\s*%[^0-9]{0,8}([0-9][0-9,]*)\s*(?:points?|pts?|分|積分)?)",
    re.I,
)
SBT_SNAPSHOT_RE = re.compile(r"(?i)(?:snapshot|快照)\s*[:：]?\s*([^\n。；;]{4,88})")
STRICT_EVENT_CALL_RE = re.compile(
    r"join us|join on|register|signup|報名|报名|參加|参加|參與|参与|attend|attendees?|live\s+(?:session|stream|ama)|community\s*session|ama|space|tour|festival|meetup|線下|线下|venue|booth|地點|地点",
    re.I,
)
SBT_THRESHOLD_NOTICE_RE = re.compile(
    r"((?:sbt|soulbound|points?|積分|积分).{0,42}(?:threshold|snapshot|top\s*\d+%|門檻|快照|排名|rank))|"
    r"((?:threshold|snapshot|top\s*\d+%|門檻|快照|排名|rank).{0,42}(?:sbt|soulbound|points?|積分|积分))",
    re.I,
)


@dataclass
class StoryCard:
    id: str
    account: str
    url: str
    title: str
    summary: str
    bullets: list[str]
    published_at: str
    confidence: float
    card_type: str
    layout: str
    tags: list[str]
    raw_text: str
    provider: str = "r.jina.ai"
    cover_image: str = ""
    metrics: dict[str, int] | None = None
    importance: float = 0.0
    template_id: str = "community_brief"
    glance: str = ""
    timeline_date: str = ""
    urgency: str = "normal"
    manual_pick: bool = False
    manual_pin: bool = False
    manual_bottom: bool = False
    event_facts: dict[str, str] | None = None
    topic_labels: list[str] | None = None
    detail_summary: str = ""
    detail_lines: list[str] | None = None
    reply_to_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "account": self.account,
            "url": self.url,
            "title": self.title,
            "summary": self.summary,
            "bullets": self.bullets,
            "published_at": self.published_at,
            "confidence": self.confidence,
            "card_type": self.card_type,
            "layout": self.layout,
            "tags": self.tags,
            "raw_text": self.raw_text,
            "provider": self.provider,
            "cover_image": self.cover_image,
            "metrics": self.metrics or {},
            "importance": self.importance,
            "template_id": self.template_id,
            "glance": self.glance,
            "timeline_date": self.timeline_date,
            "urgency": self.urgency,
            "manual_pick": self.manual_pick,
            "manual_pin": self.manual_pin,
            "manual_bottom": self.manual_bottom,
            "event_facts": self.event_facts or {},
            "topic_labels": self.topic_labels or [],
            "detail_summary": self.detail_summary,
            "detail_lines": self.detail_lines or [],
            "reply_to_id": self.reply_to_id,
        }


SYNDICATION_META_CACHE: dict[str, dict[str, Any]] = {}


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def website_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    path = get_website_data_dir(website_root())
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_environment() -> None:
    load_dotenv(project_root() / ".env")
    load_dotenv(website_root() / ".env")
    load_dotenv(project_root() / "old" / "tcg_pro" / ".env")
    user_bin = Path(site.getuserbase()) / "bin"
    py_minor_bin = Path.home() / "Library" / "Python" / f"{sys.version_info.major}.{sys.version_info.minor}" / "bin"
    path_parts = os.environ.get("PATH", "").split(":")
    for candidate in (user_bin, py_minor_bin):
        c = str(candidate)
        if candidate.exists() and c not in path_parts:
            path_parts.append(c)
    os.environ["PATH"] = ":".join([p for p in path_parts if p])


def resolve_minimax_key() -> str:
    candidates = [
        "MINIMAX_API_KEY",
        "MINIMAX_KEY",
        "MINIMAX_TEXT_API_KEY",
        "MINIMAX_TOKEN",
    ]
    for name in candidates:
        value = str(os.getenv(name) or "").strip()
        if value:
            return value
    return ""


def clean_text(text: str) -> str:
    text = unescape(str(text or ""))
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]*\)", " ", text)
    text = re.sub(r"(?i)\bshow translation\b", " ", text)
    text = re.sub(r"\bRead\\s+\\d+\\s+replies\\b", " ", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}:\d{2}:\d{2}\b", " ", text)
    text = re.sub(r"(?:^|\s)[·•]\s*\d[\d,]*(?:\s+\d[\d,]*){2,6}(?=\s*(?:Read\s+\d+\s+replies\b|$))", " ", text, flags=re.I)
    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_links_mentions(text: str) -> str:
    t = str(text or "")
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"@\w+", " ", t)
    t = re.sub(r"#\w+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def similarity_ratio(a: str, b: str) -> float:
    a_norm = re.sub(r"\s+", " ", strip_links_mentions(a).lower()).strip()
    b_norm = re.sub(r"\s+", " ", strip_links_mentions(b).lower()).strip()
    if not a_norm or not b_norm:
        return 0.0
    if a_norm in b_norm or b_norm in a_norm:
        return 1.0
    a_set = set(re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", a_norm))
    b_set = set(re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", b_norm))
    if not a_set or not b_set:
        return 0.0
    overlap = len(a_set & b_set)
    return overlap / max(len(a_set), len(b_set))


def split_sentences(text: str) -> list[str]:
    src = clean_text(text)
    if not src:
        return []
    parts = re.split(r"[。！？!?]|(?:\s{2,})|(?:\s*•\s*)", src)
    out: list[str] = []
    for p in parts:
        p = clean_text(p)
        p = re.sub(r"^\d+/\s*", "", p).strip()
        if len(strip_links_mentions(p)) < 8:
            continue
        out.append(p)
    return out


def pick_signal_lines(text: str, limit: int = 4) -> list[str]:
    lines = split_sentences(text)
    if not lines:
        return []
    ranked: list[tuple[float, str]] = []
    key_patterns = [
        r"\b(apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
        r"\b\d{1,2}/\d{1,2}\b",
        r"\b(utc|gmt|pm|am)\b",
        r"\b(v2|2\.0|beta|launch|open|coming)\b",
        r"活動|更新|公告|功能|市場|上線|開放|報名|直播|抽卡|統計",
        r"\$\d+|\d+%",
    ]
    for line in lines:
        plain = strip_links_mentions(line)
        score = min(2.6, len(plain) / 64.0)
        for pat in key_patterns:
            if re.search(pat, line, re.I):
                score += 0.8
        if len(re.findall(r"@\w+", line)) >= 3:
            score -= 0.5
        ranked.append((score, line))
    ranked.sort(key=lambda x: x[0], reverse=True)
    result: list[str] = []
    seen: set[str] = set()
    for _, line in ranked:
        key = dedupe_key(line)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        result.append(line)
        if len(result) >= limit:
            break
    return result


def extract_numeric_facts(text: str, limit: int = 3) -> list[str]:
    uniq: list[str] = []
    src = str(text or "")
    for m in re.finditer(r"\$?\d[\d,]*(?:\.\d+)?(?:[kKmMbB])?%?", src):
        h = clean_text(m.group(0))
        if not h:
            continue
        h = h.rstrip(",")
        if not h:
            continue
        if re.fullmatch(r"\d{1,2}", h):
            continue
        if re.fullmatch(r"\d{1,2}[:：]\d{2}", h):
            continue
        if h in {"0", "00"}:
            continue
        ctx = src[max(0, m.start() - 12) : min(len(src), m.end() + 12)].lower()
        has_unit = bool(
            re.search(
                r"card|cards|pack|packs|users|volume|成交|交易量|萬|千|億|usd|ntd|u\b|points|積分|sbt|%|billion|million|bn|mn",
                ctx,
                re.I,
            )
        )
        numeric = h.replace("$", "").replace(",", "").replace("%", "")
        scale = 1.0
        if numeric.lower().endswith("k"):
            scale = 1_000.0
            numeric = numeric[:-1]
        elif numeric.lower().endswith("m"):
            scale = 1_000_000.0
            numeric = numeric[:-1]
        elif numeric.lower().endswith("b"):
            scale = 1_000_000_000.0
            numeric = numeric[:-1]
        try:
            nval = float(numeric) * scale
        except Exception:
            nval = 0.0
        # Skip plain year-like tokens (e.g. 2023) unless they carry a financial/percentage signal.
        if 1900 <= nval <= 2099 and "$" not in h and "%" not in h and not has_unit:
            continue
        if nval and nval < 10 and "$" not in h and "%" not in h and not has_unit:
            continue
        if "%" not in h and "$" not in h and "," not in h and not has_unit and nval < 100:
            continue
        if h in uniq:
            continue
        uniq.append(h)
        if len(uniq) >= limit:
            break
    return uniq


def extract_schedule_facts(text: str, limit: int = 3) -> list[str]:
    src = clean_text(text)
    if not src:
        return []

    pats = [
        re.compile(
            r"(?<![:\d])(?:[01]?\d|2[0-3])[:：][0-5]\d\s*(?:am|pm)\b(?:\s*\(?(?:utc|gmt)\s*[+＋−-]?\d+\)?)?",
            re.I,
        ),
        re.compile(r"\b(?:apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:\s*-\s*\d{1,2})?", re.I),
        re.compile(r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}(?:\s*[-~到至]\s*\d{1,2})?", re.I),
        re.compile(r"(?:20\d{2}\s*年\s*)?\d{1,2}\s*月\s*\d{1,2}\s*(?:日|号|號)?(?:\s*[-~到至]\s*\d{1,2}\s*(?:日|号|號)?)?", re.I),
        re.compile(r"(?<![:\d])(?:1[0-2]|0?[1-9])\s*(?:am|pm)\b", re.I),
        re.compile(r"(?<![:\d])(?:[01]?\d|2[0-3])[:：][0-5]\d(?![:\d])", re.I),
        re.compile(r"\b(?:utc|gmt)\s*[+-]?\d+\b|utc[+＋−-]\d+", re.I),
        re.compile(r"(?:本週|下週|週末|明天|今晚|即將|今天|今日|稍後|稍后|tonight|tomorrow|today|live now|this week|next week)", re.I),
    ]
    found: list[str] = []
    for pat in pats:
        for match in pat.finditer(src):
            token = clean_text(match.group(0))
            if not token:
                continue
            if not _keep_schedule_fact(src, token, match.start(), match.end()):
                continue
            if token in found:
                continue
            found.append(token)
            if len(found) >= limit:
                return found
    return found


def _contains_calendar_date(text: str) -> bool:
    src = str(text or "")
    if not src:
        return False
    return bool(
        re.search(
            r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}\b|"
            r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}\b|"
            r"(?:20\d{2}\s*年\s*)?\d{1,2}\s*月\s*\d{1,2}\s*(?:日|号|號)?",
            src,
        )
    )


def _keep_schedule_fact(source: str, token: str, start: int, end: int) -> bool:
    low = token.lower()
    ctx = source[max(0, start - 20) : min(len(source), end + 24)].lower()
    if re.search(r"views?|repl(?:y|ies)|播放|觀看", ctx, re.I):
        return False
    if re.fullmatch(r"(?:[01]?\d|2[0-3])[:：][0-5]\d", token):
        if re.search(rf"{re.escape(token)}\s*(?:am|pm)", source, re.I):
            return True
        if re.search(r"(?:utc|gmt)\s*[+＋−-]?\d+", source, re.I):
            return True
        if re.search(r"[-~–—至到]\s*(?:[01]?\d|2[0-3])[:：][0-5]\d", ctx):
            return True
        if re.search(r"(join us|live|session|ama|活動|event|報名|register)", source, re.I):
            return True
        return False
    if re.search(r"today|tonight|tomorrow|今天|今晚|明天|本週|下週|週末|即將|稍後|稍后", low, re.I):
        return bool(re.search(r"(join us|live|session|ama|活動|event|報名|register|discord)", source, re.I))
    return True


def snowflake_to_datetime(tweet_id: str) -> datetime:
    # Twitter Snowflake epoch: 1288834974657
    ts_ms = (int(tweet_id) >> 22) + 1288834974657
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)


def _is_jina_url(url: str) -> bool:
    try:
        return urlparse(str(url or "")).netloc.lower() == JINA_HOST
    except Exception:
        return False


def _wait_for_jina_slot() -> None:
    global JINA_LAST_REQUEST_AT
    with JINA_RATE_LOCK:
        now = time.monotonic()
        wait_seconds = JINA_MIN_INTERVAL_SECONDS - (now - JINA_LAST_REQUEST_AT)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        JINA_LAST_REQUEST_AT = time.monotonic()


def _retry_after_seconds(resp: requests.Response | None) -> float:
    if resp is None:
        return 0.0
    raw = str(resp.headers.get("Retry-After") or "").strip()
    if not raw:
        return 0.0
    try:
        return max(0.0, min(float(raw), 30.0))
    except Exception:
        return 0.0


def fetch_text(url: str, timeout: int = 45) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RenaissXIntel/1.0)",
        "Accept": "text/plain, text/markdown;q=0.9, */*;q=0.8",
    }
    is_jina = _is_jina_url(url)
    attempts = JINA_MAX_RETRIES + 1 if is_jina else 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        resp: requests.Response | None = None
        try:
            if is_jina:
                _wait_for_jina_slot()
            resp = requests.get(url, headers=headers, timeout=timeout)
            if not is_jina or resp.status_code not in {429, 500, 502, 503, 504}:
                resp.raise_for_status()
                return resp.text
            resp.raise_for_status()
        except Exception as exc:
            last_error = exc
            if not is_jina or attempt >= attempts - 1:
                raise
            retry_after = _retry_after_seconds(resp)
            backoff = retry_after or (JINA_RETRY_BASE_SECONDS * (2 ** attempt))
            time.sleep(min(backoff, 12.0))
    if last_error:
        raise last_error
    raise RuntimeError("failed to fetch text")


def fetch_profile_page(username: str) -> str:
    variants = [
        f"https://r.jina.ai/http://x.com/{username}",
        f"https://r.jina.ai/http://x.com/{username}?mx=1",
    ]
    combined: list[str] = []
    for url in variants:
        try:
            combined.append(fetch_text(url))
        except Exception:
            continue
    return "\n\n".join(combined)


def fetch_account_status_ids_from_nitter_rss(username: str, limit: int = 80) -> list[str]:
    uname = str(username or "").strip().lstrip("@")
    if not uname:
        return []
    url = f"https://nitter.net/{uname}/rss"
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RenaissXIntel/1.0)"},
            timeout=30,
        )
        if resp.status_code != 200 or not resp.text.strip():
            return []
        text = resp.text
    except Exception:
        return []

    pat = re.compile(rf"/{re.escape(uname)}/status/(\d+)", re.I)
    out: list[str] = []
    seen: set[str] = set()
    for sid in pat.findall(text):
        if sid in seen:
            continue
        seen.add(sid)
        out.append(sid)
        if len(out) >= max(1, int(limit)):
            break
    return out


def _extract_syndication_cover(data: dict[str, Any]) -> str:
    photos = data.get("photos") if isinstance(data.get("photos"), list) else []
    for item in photos:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if url.startswith("http"):
            return url

    media = data.get("mediaDetails") if isinstance(data.get("mediaDetails"), list) else []
    for item in media:
        if not isinstance(item, dict):
            continue
        url = str(item.get("media_url_https") or "").strip()
        if url.startswith("http"):
            return url

    card = data.get("card") if isinstance(data.get("card"), dict) else {}
    bindings = card.get("binding_values") if isinstance(card.get("binding_values"), dict) else {}
    for key in (
        "broadcast_thumbnail_original",
        "broadcast_thumbnail_x_large",
        "broadcast_thumbnail_large",
        "broadcast_thumbnail",
        "photo_image_full_size_original",
        "photo_image_full_size_large",
    ):
        entry = bindings.get(key)
        if not isinstance(entry, dict):
            continue
        image_value = entry.get("image_value") if isinstance(entry.get("image_value"), dict) else {}
        url = str(image_value.get("url") or "").strip()
        if url.startswith("http"):
            return url
    return ""


def fetch_status_metadata(tweet_id: str, force: bool = False) -> dict[str, Any] | None:
    sid = str(tweet_id or "").strip()
    if not sid:
        return None
    if not force and sid in SYNDICATION_META_CACHE:
        cached = SYNDICATION_META_CACHE.get(sid) or {}
        return dict(cached) if cached else None
    params = {"id": sid, "token": "a"}
    try:
        resp = requests.get(SYNDICATION_TWEET_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    if not isinstance(data, dict) or not data:
        return None

    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    account = str(user.get("screen_name") or "").strip()
    display_name = str(user.get("name") or "").strip()
    note_tweet = data.get("note_tweet") if isinstance(data.get("note_tweet"), dict) else {}
    note_text = str(note_tweet.get("text") or "").strip()
    text = str(data.get("text") or "").strip()
    if len(note_text) > len(text):
        text = note_text

    created_raw = str(data.get("created_at") or "").strip()
    created_dt = parse_datetime_guess(created_raw)
    created_iso = created_dt.isoformat() if created_dt else ""

    reply_to_id = str(
        data.get("in_reply_to_status_id_str")
        or data.get("in_reply_to_status_id")
        or data.get("parent_tweet_id_str")
        or ""
    ).strip()
    reply_to_account = str(data.get("in_reply_to_screen_name") or "").strip()

    parent = data.get("parent") if isinstance(data.get("parent"), dict) else {}
    parent_id = str(parent.get("id_str") or "").strip()
    parent_user = parent.get("user") if isinstance(parent.get("user"), dict) else {}
    parent_account = str(parent_user.get("screen_name") or "").strip()
    parent_text = str(parent.get("text") or "").strip()
    if not reply_to_id and parent_id:
        reply_to_id = parent_id
    if not reply_to_account and parent_account:
        reply_to_account = parent_account

    meta = {
        "id": str(data.get("id_str") or sid),
        "account": account,
        "display_name": display_name,
        "text": clean_text(text),
        "created_at": created_raw,
        "created_at_iso": created_iso,
        "reply_to_id": reply_to_id,
        "reply_to_account": reply_to_account,
        "parent_id": parent_id,
        "parent_account": parent_account,
        "parent_text": clean_text(parent_text),
        "conversation_count": int(data.get("conversation_count") or 0),
        "cover_image": _extract_syndication_cover(data),
    }
    SYNDICATION_META_CACHE[sid] = meta
    return dict(meta)


def build_markdown_from_status_meta(meta: dict[str, Any], url: str) -> str:
    text = clean_text(str(meta.get("text") or ""))
    account = str(meta.get("account") or "x_user").strip()
    display_name = str(meta.get("display_name") or account).strip()
    created = str(meta.get("created_at") or "").strip()
    title = f'Title: {display_name} on X: "{text}" / X\n\nURL Source: {url}\n'
    if created:
        title += f"\nPublished Time: {created}\n"
    title += f"\nMarkdown Content:\n{text}\n"
    return title


def extract_status_ids(page_text: str, username: str) -> list[str]:
    if not page_text:
        return []
    wanted = username.lower().lstrip("@")
    seen: set[str] = set()
    result: list[str] = []
    for owner, sid in STATUS_RE.findall(page_text):
        if owner.lower().lstrip("@") != wanted:
            continue
        if sid in seen:
            continue
        seen.add(sid)
        result.append(sid)
    return result


def _extract_title(title_line: str) -> str:
    # pattern: user on X: "tweet text"
    marker = ' on X: '
    if marker in title_line:
        body = title_line.split(marker, 1)[1].strip()
        if body.startswith('"') and body.endswith('"'):
            body = body[1:-1]
        return clean_text(body)
    return clean_text(title_line)


def extract_focus_content(markdown_body: str) -> str:
    body = str(markdown_body or "")
    if not body:
        return ""

    for marker in ("# Conversation", "## Conversation", "# Post", "## Post"):
        if marker in body:
            body = body.split(marker, 1)[1]
            break

    for stop in ("## New to X?", "## Trending now", "Terms of Service", "© 2026 X Corp."):
        if stop in body:
            body = body.split(stop, 1)[0]

    boilerplate = [
        "Don’t miss what’s happening",
        "People on X are the first to know",
        "See new posts",
        "Sign up with Apple",
        "Sign up with Google",
    ]
    for token in boilerplate:
        body = body.replace(token, " ")

    body = re.sub(r"^#+\\s*", "", body, flags=re.M)
    body = re.sub(r"https://t\\.co/\\S+", " ", body)
    return clean_text(body)


def is_noise_text(text: str) -> bool:
    plain = strip_links_mentions(text)
    plain_lower = plain.lower()
    if len(plain) < 18:
        return True
    if re.fullmatch(r"[\W_]+", plain):
        return True
    if re.match(r"^(恭喜|讚|wow+|nice+|哈哈|lol|both~?)$", plain, re.I):
        return True
    has_signal_kw = bool(
        re.search(
            r"活動|event|update|公告|feature|launch|上線|即將|coming|tour|festival|market|price|volume|抽卡|空投|sbt|2\.0|v2",
            plain_lower,
            re.I,
        )
    )
    has_number = bool(re.search(r"\d", plain))
    token_count = len(re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", plain_lower))
    if token_count <= 3 and not has_signal_kw and not has_number:
        return True
    if plain.strip().startswith("@") and len(plain) < 64 and not has_signal_kw:
        return True
    return False


def extract_first_image(media: Any) -> str:
    if not isinstance(media, list):
        return ""
    for item in media:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if url.startswith("http"):
            return url
    return ""


def date_hint_from_text(text: str) -> str:
    t = str(text or "")
    patterns = [
        r"(?i)\b(apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:\s*-\s*\d{1,2})?",
        r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}(?:\s*-\s*\d{1,2})?",
        r"(?:20\d{2}\s*年\s*)?\d{1,2}\s*月\s*\d{1,2}\s*(?:日|号|號)?(?:\s*[-~到至]\s*\d{1,2}\s*(?:日|号|號)?)?",
        r"(?:本週|下週|週末|明天|今晚|今天|今日)",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            return m.group(0)
    return ""


def choose_template_id(card_type: str) -> str:
    mapping = {
        "event": "event_poster",
        "market": "market_signal",
        "announcement": "announcement_timeline",
        "feature": "announcement_timeline",
        "report": "community_brief",
        "insight": "community_brief",
    }
    return mapping.get(card_type, "community_brief")


def compute_urgency(card_type: str, importance: float, timeline_date: str = "") -> str:
    if card_type in {"event", "feature", "announcement"} and timeline_date:
        try:
            dt = datetime.fromisoformat(timeline_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days = (dt.date() - datetime.now(timezone.utc).date()).days
            if 0 <= days <= 3:
                return "high"
            if 4 <= days <= 10:
                return "medium"
        except Exception:
            pass
    if importance >= 10:
        return "high"
    if importance >= 6:
        return "medium"
    return "normal"


def extract_timeline_date(text: str, base_dt: datetime | None = None) -> tuple[str, str]:
    src = str(text or "")
    now = (base_dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    year = now.year
    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def _build_date(y: int, mon: int, day: int, day_end: int | None = None) -> tuple[str, str]:
        if not (1 <= mon <= 12 and 1 <= day <= 31):
            return "", ""
        try:
            dt = datetime(y, mon, day, 0, 0, tzinfo=timezone.utc)
            if dt < now - timedelta(days=120):
                dt = datetime(y + 1, mon, day, 0, 0, tzinfo=timezone.utc)
            label = f"{mon:02d}/{day:02d}"
            if day_end and day_end >= day:
                label = f"{label}-{day_end:02d}"
            return dt.isoformat(), label
        except Exception:
            return "", ""

    m = re.search(r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:\s*-\s*(\d{1,2}))?", src)
    if m:
        mon = month_map.get(m.group(1).lower()[:3], 0)
        day = int(m.group(2))
        day_end = int(m.group(3)) if m.group(3) else None
        iso, label = _build_date(year, mon, day, day_end=day_end)
        if iso:
            return iso, label

    m = re.search(
        r"(?i)\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s*-\s*(\d{1,2}))?",
        src,
    )
    if m:
        day = int(m.group(1))
        mon = month_map.get(m.group(2).lower()[:3], 0)
        day_end = int(m.group(3)) if m.group(3) else None
        iso, label = _build_date(year, mon, day, day_end=day_end)
        if iso:
            return iso, label

    m = re.search(r"\b((?:20\d{2})/)?(\d{1,2})/(\d{1,2})(?:\s*[-~到至]\s*(\d{1,2}))?", src)
    if m:
        year_hint = year
        if m.group(1):
            try:
                year_hint = int(str(m.group(1)).strip("/"))
            except Exception:
                year_hint = year
        mon = int(m.group(2))
        day = int(m.group(3))
        day_end = int(m.group(4)) if m.group(4) else None
        iso, label = _build_date(year_hint, mon, day, day_end=day_end)
        if iso:
            return iso, label

    m = re.search(
        r"(?:\b(20\d{2})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*(?:日|号|號)?(?:\s*[-~到至]\s*(\d{1,2})\s*(?:日|号|號)?)?",
        src,
    )
    if m:
        year_hint = int(m.group(1)) if m.group(1) else year
        mon = int(m.group(2))
        day = int(m.group(3))
        day_end = int(m.group(4)) if m.group(4) else None
        iso, label = _build_date(year_hint, mon, day, day_end=day_end)
        if iso:
            return iso, label

    src_low = clean_text(src).lower()
    time_context = bool(
        re.search(
            r"(join us|live|session|ama|活動|event|報名|register|discord|goes live|launch|release|snapshot|開放|上線|上线|提醒)",
            src_low,
            re.I,
        )
    )

    def _build_relative(days: int, label: str) -> tuple[str, str]:
        dt = (now + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.isoformat(), label

    if time_context and re.search(r"(後天|后天|day after tomorrow)", src_low, re.I):
        return _build_relative(2, "後天")
    if time_context and re.search(r"(明天|tomorrow)", src_low, re.I):
        return _build_relative(1, "明天")
    if time_context and re.search(r"(今天|今日|今晚|今夜|today|tonight|live now)", src_low, re.I):
        return _build_relative(0, "今天")

    weekday_map = {
        "mon": 0, "monday": 0, "週一": 0, "周一": 0,
        "tue": 1, "tues": 1, "tuesday": 1, "週二": 1, "周二": 1,
        "wed": 2, "wednesday": 2, "週三": 2, "周三": 2,
        "thu": 3, "thur": 3, "thurs": 3, "thursday": 3, "週四": 3, "周四": 3,
        "fri": 4, "friday": 4, "週五": 4, "周五": 4,
        "sat": 5, "saturday": 5, "週六": 5, "周六": 5,
        "sun": 6, "sunday": 6, "週日": 6, "周日": 6, "週天": 6, "周天": 6,
    }

    wk = re.search(
        r"(?i)\b(mon(?:day)?|tue(?:s|sday)?|wed(?:nesday)?|thu(?:r|rs|rsday|rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b|(?:週|周)([一二三四五六日天])",
        src,
    )
    if wk and time_context:
        token = (wk.group(1) or "").lower()
        if not token and wk.group(2):
            token = f"週{wk.group(2)}"
        target = weekday_map.get(token)
        if target is not None:
            delta = (target - now.weekday()) % 7
            if delta == 0 and re.search(r"(next week|下週|下周)", src_low, re.I):
                delta = 7
            dt = (now + timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)
            return dt.isoformat(), dt.strftime("%m/%d")

    if time_context and re.search(r"(this week|本週|本周|this weekend|週末|周末)", src_low, re.I):
        dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.isoformat(), "本週"
    if time_context and re.search(r"(next week|下週|下周|next weekend)", src_low, re.I):
        dt = (now + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.isoformat(), "下週"
    return "", ""


def parse_status_page(
    markdown: str,
    username: str,
    tweet_id: str,
    url: str,
    provider: str = "r.jina.ai",
    tweet_meta: dict[str, Any] | None = None,
) -> StoryCard | None:
    title_match = TITLE_RE.search(markdown)
    if not title_match:
        return None

    published_match = PUBLISHED_RE.search(markdown)
    markdown_match = MARKDOWN_RE.search(markdown)

    title = _extract_title(title_match.group(1))
    raw = markdown_match.group(1).strip() if markdown_match else ""
    raw_clean = extract_focus_content(raw) or clean_text(raw)

    if len(raw_clean) < 8 and len(title) < 8:
        return None

    content_source = raw_clean if len(raw_clean) > len(title) else title
    meta_text = ""
    if isinstance(tweet_meta, dict):
        meta_text = clean_text(str(tweet_meta.get("text") or ""))
    if len(meta_text) > max(24, len(content_source)):
        content_source = meta_text
    if is_noise_text(content_source):
        return None
    card_type, layout, tags = classify_story(content_source)
    shaped = build_editorial_copy(content_source, card_type, username)
    summary = str(shaped.get("summary") or summarize_naive(content_source, max_len=220))
    bullets = shaped.get("bullets") if isinstance(shaped.get("bullets"), list) else extract_bullets(content_source)
    normalized_title = str(shaped.get("title") or "").strip()

    published_at = ""
    if published_match:
        try:
            dt = datetime.strptime(published_match.group(1).strip(), "%a, %d %b %Y %H:%M:%S %Z")
            published_at = dt.replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            published_at = ""
    if not published_at and isinstance(tweet_meta, dict):
        meta_iso = str(tweet_meta.get("created_at_iso") or "").strip()
        if meta_iso:
            published_at = meta_iso
    if not published_at:
        published_at = snowflake_to_datetime(tweet_id).isoformat()

    cover = ""
    for img in IMAGE_RE.findall(markdown):
        if "pbs.twimg.com/media/" in img:
            cover = img
            break
    if not cover and isinstance(tweet_meta, dict):
        cover = str(tweet_meta.get("cover_image") or "").strip()

    reply_to_id = ""
    if isinstance(tweet_meta, dict):
        reply_to_id = str(tweet_meta.get("reply_to_id") or tweet_meta.get("parent_id") or "").strip()

    card = StoryCard(
        id=tweet_id,
        account=username,
        url=url,
        title=normalized_title or title or f"@{username} update",
        summary=summary,
        bullets=bullets,
        published_at=published_at,
        confidence=0.56,
        card_type=card_type,
        layout=layout,
        tags=tags,
        raw_text=content_source[:2500],
        provider=provider,
        cover_image=cover,
        metrics={},
        reply_to_id=reply_to_id,
    )
    card.importance = score_card(card)
    enrich_card_metadata(card)
    enrich_detail_view(card)
    return card


def _has_event_evidence(text: str, timeline_iso: str = "") -> bool:
    source = clean_text(text)
    has_time = bool(timeline_iso) or _has_actionable_event_schedule(source)
    has_event_signal = bool(EVENT_SIGNAL_RE.search(source))
    has_participation = bool(PARTICIPATION_SIGNAL_RE.search(source))
    has_location = bool(LOCATION_SIGNAL_RE.search(source))
    has_live_reward = bool(LIVE_REWARD_RE.search(source))
    has_explicit_event = bool(STRICT_EVENT_CALL_RE.search(source))
    has_recap_signal = bool(
        re.search(
            r"(that'?s a wrap|thanks to everyone who joined|活動回顧|行程回顧|回顧|結束回顧|tour recap|after the tour|during web3 festival)",
            source,
            re.I,
        )
    )
    looks_like_feature_update = bool(
        re.search(
            r"(threshold|snapshot|beta|v\d|2\.0|mfa|authentication|security|progress update|版本|功能|更新)",
            source,
            re.I,
        )
    )
    looks_like_sbt_threshold_notice = bool(SBT_THRESHOLD_NOTICE_RE.search(source))
    hypothetical = bool(re.search(r"\bwhat if\b|會不會|会不会|\bif\b.{0,18}\bama\b", source, re.I))
    explicit_call = bool(
        re.search(
            r"join us|live now|今晚|tonight|報名|register|discord|space|goes live|drop now|open now|開賣|开卖|參加|参加|attend",
            source,
            re.I,
        )
    )
    if hypothetical and not explicit_call:
        return False
    evidence_score = 0
    if has_event_signal:
        evidence_score += 1
    if has_time:
        evidence_score += 1
    if has_participation:
        evidence_score += 2
    if has_location:
        evidence_score += 1
    if has_live_reward:
        evidence_score += 1
    if has_explicit_event or explicit_call:
        evidence_score += 2
    if has_recap_signal and has_location:
        evidence_score += 1

    # 功能/快照類貼文不是一律排除；若同時有明確參與語意，仍可被判定為活動。
    if looks_like_sbt_threshold_notice and evidence_score < 4:
        return False
    if looks_like_feature_update and evidence_score < 4 and not has_location:
        return False
    if has_event_signal and has_location and has_recap_signal:
        return True
    return bool(
        evidence_score >= 3
        and has_time
        and (has_participation or has_location or has_live_reward or explicit_call or has_explicit_event)
    )


def _has_actionable_event_schedule(text: str) -> bool:
    src = clean_text(text)
    if not src:
        return False
    facts = extract_schedule_facts(src, limit=6)
    if not facts:
        return False
    joined = " ".join(facts)
    has_date = _contains_calendar_date(joined)
    has_time = bool(re.search(r"\b\d{1,2}\s*(?:am|pm)\b|(?<![:\d])(?:[01]?\d|2[0-3])[:：][0-5]\d(?![:\d])", joined, re.I))
    has_zone = bool(re.search(r"(?:utc|gmt)\s*[+＋−-]?\d+", joined, re.I))
    has_relative = bool(re.search(r"tonight|today|tomorrow|今晚|今天|明天|本週|下週|週末|即將", src, re.I))
    has_event_context = bool(STRICT_EVENT_CALL_RE.search(src))
    if has_date:
        return True
    if has_time and (has_zone or has_relative):
        return True
    if has_time and has_event_context:
        return True
    if has_relative and has_event_context:
        return True
    return False


def classify_story(text: str) -> tuple[str, str, list[str]]:
    source = clean_text(text)
    plain = strip_links_mentions(source)
    timeline_iso, _ = extract_timeline_date(plain)
    lower = plain.lower()
    has_event = _has_event_evidence(plain, timeline_iso=timeline_iso)
    has_guide = bool(GUIDE_SIGNAL_RE.search(plain))
    has_feature = bool(FEATURE_SIGNAL_RE.search(plain))
    has_announce = bool(ANNOUNCE_SIGNAL_RE.search(plain))
    has_market = bool(MARKET_SIGNAL_RE.search(plain))
    has_report = bool(REPORT_SIGNAL_RE.search(plain))
    has_numbers = bool(re.search(r"\d", plain))
    has_sbt_feature = bool(
        re.search(
            r"(\bsbt\b|soulbound|積分|积分|points?).{0,38}(threshold|snapshot|top\s*\d+%|排名|rank|門檻|快照|unlock|claim|mint|發放|领取|領取|取得|獲得)|"
            r"(threshold|snapshot|top\s*\d+%|排名|rank|門檻|快照).{0,38}(\bsbt\b|soulbound|積分|积分|points?)",
            plain,
            re.I,
        )
    )
    has_sbt_unlock = bool(
        re.search(
            r"(pull|open|mint|claim|join|attend|share|hold|buy|參加|参与|完成|快照|排名).{0,48}(\bsbt\b|soulbound|認證|认证)|"
            r"(\bsbt\b|soulbound).{0,48}(unlock|claim|get|receive|領取|领取|取得|獲得|解鎖|解锁)",
            plain,
            re.I,
        )
    )

    # 攻略/經驗分享優先，避免被「開放、活動」字眼誤判。
    if has_guide and not has_event:
        return "report", "brief", ["分析", "內容"]

    # 活動需要可辨識時間 + 參與/地點/直播獎勵等語意證據。
    if has_event:
        return "event", "poster", ["活動", "參與"]

    # SBT 門檻/快照/取得條件優先視為功能或公告，不落入市場模板。
    if has_sbt_feature or has_sbt_unlock:
        if has_announce and not has_feature:
            return "announcement", "timeline", ["更新", "公告"]
        return "feature", "timeline", ["功能", "即將開放"]

    # 市場訊號需搭配數字或明確交易語境。
    if has_market and has_numbers:
        return "market", "data", ["市場", "數據"]

    # 功能進度與公告分流：產品/版本/開放屬 feature，制度公告屬 announcement。
    if has_feature and not has_guide:
        return "feature", "timeline", ["功能", "即將開放"]
    if has_announce:
        return "announcement", "timeline", ["更新", "公告"]

    if has_report:
        return "report", "brief", ["分析", "內容"]

    # 純短互動或回覆訊息，統一走 insight。
    if len(re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", lower)) <= 5 and not has_numbers:
        return "insight", "brief", ["觀點"]
    return "insight", "brief", ["觀點"]


def default_style_for_type(card_type: str) -> tuple[str, list[str]]:
    mapping = {
        "event": ("poster", ["活動", "參與"]),
        "feature": ("timeline", ["功能", "即將開放"]),
        "market": ("data", ["市場", "數據"]),
        "report": ("brief", ["分析", "內容"]),
        "announcement": ("timeline", ["更新", "公告"]),
        "insight": ("brief", ["觀點"]),
    }
    return mapping.get(card_type, ("brief", ["觀點"]))


def score_card(card: StoryCard) -> float:
    score = 0.0
    if card.account.lower() == "renaissxyz":
        score += 5.0
    type_weight = {
        "event": 4.5,
        "feature": 4.2,
        "announcement": 3.8,
        "market": 3.4,
        "report": 3.0,
        "insight": 1.5,
    }
    score += type_weight.get(card.card_type, 1.0)

    text = card.raw_text or card.title
    if date_hint_from_text(text):
        score += 1.2
    if card.card_type == "event" and card.timeline_date:
        score += 0.9
    if LIVE_REWARD_RE.search(text or ""):
        score += 0.8
    if card.cover_image:
        score += 0.8

    metrics = card.metrics or {}
    likes = int(metrics.get("likes", 0) or 0)
    retweets = int(metrics.get("retweets", 0) or 0)
    replies = int(metrics.get("replies", 0) or 0)
    views = int(metrics.get("views", 0) or 0)
    score += min(4.0, likes / 25.0 + retweets / 8.0 + replies / 15.0 + views / 6000.0)

    # Penalize low-information short replies
    if len(strip_links_mentions(text)) < 28:
        score -= 2.2
    return round(score, 3)


def summarize_naive(text: str, max_len: int = 200) -> str:
    cleaned = clean_text(text)
    if len(cleaned) <= max_len:
        return cleaned
    snippet = cleaned[:max_len].rsplit(" ", 1)[0].strip()
    return snippet + "..."


def extract_bullets(text: str, limit: int = 3) -> list[str]:
    cleaned = clean_text(text)
    chunks = re.split(r"[。.!?！？]\s*", cleaned)
    items: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 18:
            continue
        items.append(chunk[:110])
        if len(items) >= limit:
            break
    if not items and cleaned:
        items = [cleaned[:120]]
    return items


def _headline_prefix(card_type: str) -> str:
    mapping = {
        "event": "活動重點",
        "market": "市場訊號",
        "announcement": "官方公告",
        "feature": "功能進度",
        "report": "重點分析",
        "insight": "社群觀點",
    }
    return mapping.get(card_type, "情報重點")


def _unique_non_empty(items: list[str], limit: int = 3) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in items:
        t = compact_point(raw, 120)
        if not t:
            continue
        k = dedupe_key(t)
        if k and k in seen:
            continue
        if k:
            seen.add(k)
        out.append(t)
        if len(out) >= limit:
            break
    return out


def _pick_fact_line(lines: list[str], patterns: list[re.Pattern[str]], max_len: int = 84) -> str:
    for line in lines:
        cleaned = clean_text(line)
        if not cleaned:
            continue
        for pat in patterns:
            if pat.search(cleaned):
                return compact_point(cleaned, max_len=max_len)
    return ""


def _clean_fact_value(text: str, max_len: int = 84) -> str:
    t = clean_text(str(text or ""))
    t = re.sub(r"^[\-\u2022•./:：()\s]+", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ;；,.。、")
    return compact_point(t, max_len=max_len)


def normalize_event_facts(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    allowed = ("reward", "participation", "audience", "location", "schedule")
    out: dict[str, str] = {}
    for key in allowed:
        raw = value.get(key)
        text = _clean_fact_value(str(raw or ""), max_len=92)
        if text:
            out[key] = text
    return out


def normalize_topic_labels(value: Any) -> list[str]:
    if isinstance(value, str):
        raw_items = re.split(r"[,，/|\\\s]+", value)
    elif isinstance(value, list):
        raw_items = [str(x) for x in value]
    else:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        label = str(raw or "").strip().lower()
        if not label or label in seen:
            continue
        if label not in ALLOWED_TOPIC_LABELS:
            continue
        seen.add(label)
        out.append(label)
        if len(out) >= 6:
            break
    return out


def _event_token_summary(text: str, token_map: list[tuple[re.Pattern[str], str]], max_items: int = 4) -> str:
    out: list[str] = []
    seen: set[str] = set()
    for pat, label in token_map:
        if pat.search(text):
            if label in seen:
                continue
            seen.add(label)
            out.append(label)
            if len(out) >= max_items:
                break
    return "、".join(out)


def _extract_number_values(text: str) -> list[int]:
    values: list[int] = []
    for n in re.findall(r"(\d{2,5})", str(text or "")):
        try:
            values.append(int(n))
        except Exception:
            continue
    return values


def _compact_clause(text: str, max_items: int = 2, max_len: int = 52) -> str:
    chunks = re.split(r"[，,。；;｜|]", clean_text(text))
    picked: list[str] = []
    for chunk in chunks:
        c = _clean_fact_value(chunk, max_len=48)
        if not c:
            continue
        if c in picked:
            continue
        picked.append(c)
        if len(picked) >= max_items:
            break
    if not picked:
        return ""
    return compact_point("、".join(picked), max_len=max_len)


def _normalize_price_text(raw: str) -> str:
    src = clean_text(raw)
    if not src:
        return ""
    pkg = "包稅" if re.search(r"包稅|含稅", src, re.I) else ""
    m = re.search(r"(\d{2,5})\s*(ntd|twd|usd|u|元)?", src, re.I)
    if not m:
        return _clean_fact_value(src, max_len=26)
    num = m.group(1)
    unit = str(m.group(2) or "")
    if unit.lower() in {"ntd", "twd", "usd"}:
        unit = unit.upper()
    elif unit.lower() == "u":
        unit = "U"
    core = f"{num}{unit}"
    return f"{pkg}{core}" if pkg else core


def extract_report_options(text: str, limit: int = 4) -> list[dict[str, str]]:
    src = clean_text(text)
    if not src:
        return []
    matches = list(REPORT_OPTION_START_RE.finditer(src))
    if not matches:
        return []

    options: list[dict[str, str]] = []
    for i, m in enumerate(matches[:limit]):
        name = _clean_fact_value(m.group(2), max_len=28)
        if not name:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(src)
        segment = clean_text(src[start:end])
        if not segment:
            continue

        price = ""
        pm = re.search(
            r"(?:價格|价格|價位|价位|費用|费用|運費|运费)[:：]?\s*([^。；;]{1,40}?)(?=(?:優點|优点|缺點|缺点|$))",
            segment,
            re.I,
        )
        if pm:
            price = _normalize_price_text(pm.group(1))
        if not price:
            pn = re.search(r"(\d{2,5}\s*(?:ntd|twd|usd|u|元)?)", segment, re.I)
            if pn:
                price = _normalize_price_text(pn.group(1))

        pros = ""
        pros_m = re.search(
            r"(?:優點|优点|優勢|优势|好處|好处)[:：]?\s*([^。；;]{2,72}?)(?=(?:缺點|缺点|價格|价格|$))",
            segment,
            re.I,
        )
        if pros_m:
            pros = _compact_clause(pros_m.group(1), max_items=2, max_len=54)

        cons = ""
        cons_m = re.search(
            r"(?:缺點|缺点|風險|风险|限制|缺陷)[:：]?\s*([^。；;]{2,72}?)(?=(?:價格|价格|使用方式|$))",
            segment,
            re.I,
        )
        if cons_m:
            cons = _compact_clause(cons_m.group(1), max_items=2, max_len=54)

        detail_parts: list[str] = []
        if price:
            detail_parts.append(f"價格 {price}")
        if pros:
            detail_parts.append(f"優點 {pros}")
        if cons:
            detail_parts.append(f"缺點 {cons}")
        if not detail_parts:
            detail_parts.append(_compact_clause(segment, max_items=2, max_len=88) or compact_point(segment, max_len=88))

        deduped_parts: list[str] = []
        seen_parts: set[str] = set()
        for part in detail_parts:
            key = dedupe_key(part)
            if key and key in seen_parts:
                continue
            if key:
                seen_parts.add(key)
            deduped_parts.append(part)

        options.append(
            {
                "name": name,
                "price": price,
                "pros": pros,
                "cons": cons,
                "detail": "｜".join(deduped_parts),
            }
        )
    return options


def build_report_digest(text: str) -> dict[str, Any]:
    src = clean_text(text)
    options = extract_report_options(src, limit=4)
    if not options:
        return {"summary": "", "bullets": []}

    names = [o["name"] for o in options if o.get("name")]
    summary_parts: list[str] = [f"整理出 {len(options)} 個方案：{' / '.join(names[:4])}。"]

    values: list[int] = []
    for o in options:
        for v in _extract_number_values(o.get("price", "")):
            if v < 20:
                continue
            values.append(v)
    if values:
        lo, hi = min(values), max(values)
        if lo == hi:
            summary_parts.append(f"主要價格落點約 {lo}。")
        else:
            summary_parts.append(f"價格區間約 {lo} - {hi}。")

    if any(o.get("pros") for o in options) or any(o.get("cons") for o in options):
        summary_parts.append("差異重點在速度、覆蓋範圍與額外費用。")

    bullets = [f"{o['name']}：{o['detail']}" for o in options if o.get("name")][:3]
    return {"summary": clean_text(" ".join(summary_parts))[:280], "bullets": bullets}


def build_event_facts(text: str) -> dict[str, str]:
    src = clean_text(text)
    if not src:
        return {}
    lines = pick_signal_lines(src, limit=8)
    if not lines:
        lines = split_sentences(src)[:8]

    schedule_items = extract_schedule_facts(src, limit=3)
    schedule = _clean_fact_value("、".join(schedule_items[:3]), max_len=56)

    reward = _event_token_summary(
        src,
        [
            (re.compile(r"\bsbt\b", re.I), "SBT"),
            (re.compile(r"積分|积分|points?", re.I), "積分"),
            (re.compile(r"merch|周邊|周边", re.I), "周邊"),
            (re.compile(r"airdrop|空投", re.I), "空投"),
            (re.compile(r"獎勵|奖励|獎品|prize|reward", re.I), "活動獎勵"),
        ],
        max_items=4,
    )

    participation_tokens = _event_token_summary(
        src,
        [
            (re.compile(r"discord", re.I), "Discord"),
            (re.compile(r"live|直播", re.I), "直播"),
            (re.compile(r"session|community\s*session", re.I), "社群 Session"),
            (re.compile(r"join us|join", re.I), "參與活動"),
            (re.compile(r"報名|报名|register|signup", re.I), "報名"),
            (re.compile(r"填表", re.I), "填表"),
            (re.compile(r"投票|互動|互动", re.I), "互動投票"),
        ],
        max_items=4,
    )
    participation = participation_tokens
    if not participation:
        participation = _pick_fact_line(lines, [JOIN_SIGNAL_RE, PARTICIPATION_SIGNAL_RE], max_len=72)
    if participation and len(participation) > 40:
        compact_participation = _event_token_summary(
            src,
            [
                (re.compile(r"discord", re.I), "Discord"),
                (re.compile(r"live|直播", re.I), "直播"),
                (re.compile(r"session|community\s*session", re.I), "社群 Session"),
                (re.compile(r"join us|join", re.I), "參與活動"),
                (re.compile(r"報名|报名|register|signup", re.I), "報名"),
                (re.compile(r"填表", re.I), "填表"),
                (re.compile(r"投票|互動|互动", re.I), "互動投票"),
            ],
            max_items=4,
        )
        if compact_participation:
            participation = compact_participation

    audience_parts: list[str] = []
    m = re.search(r"(\d+\s*位?(?:參賽者|参赛者))", src, re.I)
    if m:
        audience_parts.append(_clean_fact_value(m.group(1), max_len=24))
    if re.search(r"觀眾|观众", src, re.I):
        audience_parts.append("觀眾")
    if re.search(r"all regions|多語|multi-language", src, re.I):
        audience_parts.append("多語社群")
    if re.search(r"community|社群", src, re.I):
        audience_parts.append("社群玩家")
    audience = "、".join(list(dict.fromkeys([x for x in audience_parts if x]))[:3])

    location = ""
    if re.search(r"web3\s*festival", src, re.I) and re.search(r"hong\s*kong|香港", src, re.I):
        location = "香港 Web3 Festival"
    elif re.search(r"arcadia\s+restaurant", src, re.I):
        location = "Arcadia Restaurant & Bar（香港銅鑼灣）"
    elif re.search(r"causeway\s*bay|銅鑼灣", src, re.I):
        location = "香港銅鑼灣"
    elif re.search(r"midtown", src, re.I):
        location = "香港 Midtown"
    elif re.search(r"hong\s*kong|香港", src, re.I):
        location = "香港"
    elif re.search(r"discord|space|直播|live", src, re.I):
        location = "線上（Discord / Live）"
    elif re.search(r"plaza", src, re.I):
        location = "Renaiss Plaza"

    if not location and re.search(r"discord|space|live|直播", src, re.I):
        location = "線上（Discord / Live）"

    return normalize_event_facts(
        {
            "reward": reward,
            "participation": participation,
            "audience": audience,
            "location": location,
            "schedule": schedule,
        }
    )


