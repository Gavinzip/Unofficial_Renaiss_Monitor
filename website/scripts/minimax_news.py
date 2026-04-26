#!/usr/bin/env python3
"""MiniMax search helpers for latest Pokemon news."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except Exception:  # MCP is optional when NEWS_SEARCH_PROVIDER=mmx.
    ClientSession = None  # type: ignore[assignment]
    StdioServerParameters = None  # type: ignore[assignment]
    stdio_client = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
ENV_FILES = [
    PROJECT_ROOT / ".env",
    ROOT / ".env",
    PROJECT_ROOT / "old" / "tcg_pro" / ".env",
]
DEFAULT_QUERIES = [
    "pokemon latest news official 2026",
    "pokemon tcg latest news 2026",
    "寶可夢 最新消息 官方 2026",
]
MINIMAX_TEXT_URL = "https://api.minimax.io/v1/text/chatcompletion_v2"
OFFICIAL_SOURCE_SUFFIXES = (
    "pokemon.com",
    "pokemongolive.com",
    "pokemon.co.jp",
    "nintendo.com",
)
SECONDARY_SOURCE_SUFFIXES = (
    "youtube.com",
    "ign.com",
    "polygon.com",
    "gamespot.com",
    "eurogamer.net",
)
BLOCKED_SOURCE_SUFFIXES = (
    "x.com",
    "twitter.com",
    "threads.com",
    "facebook.com",
    "instagram.com",
    "reddit.com",
    "tiktok.com",
)
MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return out
    for line in raw.splitlines():
        row = line.strip()
        if not row or row.startswith("#"):
            continue
        if row.startswith("export "):
            row = row[7:].strip()
        if "=" not in row:
            continue
        key, value = row.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            out[key] = value
    return out


def _resolve_minimax_credentials() -> tuple[str, str]:
    env_map: dict[str, str] = {}
    for path in ENV_FILES:
        env_map.update(_read_env_file(path))
    api_key = (
        os.getenv("MINIMAX_API_KEY")
        or env_map.get("MINIMAX_API_KEY")
        or os.getenv("MINIMAX_KEY")
        or env_map.get("MINIMAX_KEY")
        or ""
    ).strip()
    api_host = (
        os.getenv("MINIMAX_API_HOST")
        or env_map.get("MINIMAX_API_HOST")
        or "https://api.minimax.io"
    ).strip()
    return api_key, api_host


def _extract_text_payload(call_result) -> str:
    chunks = []
    for part in (getattr(call_result, "content", None) or []):
        text = getattr(part, "text", None)
        if text:
            chunks.append(text)
    return "\n".join(chunks).strip()


def _normalize_text(value: str) -> str:
    text = unescape(str(value or ""))
    text = text.replace("\u200b", " ").replace("\ufeff", " ")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_lang(lang: str | None) -> str:
    raw = str(lang or "").strip().lower()
    if raw.startswith("zh-hant") or raw in {"zh-tw", "zh-hk", "zh-mo"}:
        return "zh-Hant"
    if raw.startswith("zh"):
        return "zh-Hans"
    if raw.startswith("ja"):
        return "ja"
    if raw.startswith("ko"):
        return "ko"
    if raw.startswith("en"):
        return "en"
    return "zh-Hant"


def _lang_prompt_hint(lang: str) -> str:
    mapping = {
        "zh-Hant": "繁體中文",
        "zh-Hans": "简体中文",
        "ja": "日本語",
        "ko": "한국어",
        "en": "English",
    }
    return mapping.get(lang, "繁體中文")


def _default_queries_for_lang(lang: str) -> list[str]:
    if lang == "zh-Hans":
        return [
            "site:pokemon.com pokemon news 2026",
            "site:pokemongolive.com pokemon go 2026 news",
            "宝可梦 TCG 最新消息 官方 2026",
        ]
    if lang == "zh-Hant":
        return [
            "site:pokemon.com pokemon news 2026",
            "site:pokemongolive.com pokemon go 2026 news",
            "寶可夢 TCG 最新消息 官方 2026",
        ]
    if lang == "ja":
        return [
            "ポケモン 最新ニュース 公式 2026",
            "ポケモンカード 最新ニュース 2026",
            "pokemon latest news official 2026",
        ]
    if lang == "ko":
        return [
            "포켓몬 최신 뉴스 공식 2026",
            "포켓몬 카드 최신 뉴스 2026",
            "pokemon latest news official 2026",
        ]
    return [
        "site:pokemon.com pokemon latest news 2026",
        "site:pokemongolive.com pokemon go latest news 2026",
        "pokemon tcg official latest news 2026",
    ]


def _source_name(url: str) -> str:
    try:
        host = (urlparse(str(url or "")).netloc or "").lower()
    except Exception:
        host = ""
    host = re.sub(r"^www\.", "", host)
    return host or "unknown"


def _is_official_source(source: str) -> bool:
    s = _normalize_text(source).lower()
    return bool(s and any(s == suffix or s.endswith(f".{suffix}") for suffix in OFFICIAL_SOURCE_SUFFIXES))


def _is_secondary_source(source: str) -> bool:
    s = _normalize_text(source).lower()
    return bool(s and any(s == suffix or s.endswith(f".{suffix}") for suffix in SECONDARY_SOURCE_SUFFIXES))


def _is_blocked_source(source: str) -> bool:
    s = _normalize_text(source).lower()
    return bool(s and any(s == suffix or s.endswith(f".{suffix}") for suffix in BLOCKED_SOURCE_SUFFIXES))


def _is_allowed_source(source: str) -> bool:
    if _is_blocked_source(source):
        return False
    if _is_official_source(source) or _is_secondary_source(source):
        return True
    return False


def _canonical_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw.startswith(("http://", "https://")):
        return raw
    try:
        parsed = urlparse(raw)
        scheme = parsed.scheme.lower() or "https"
        host = (parsed.netloc or "").lower()
        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/")
        return f"{scheme}://{host}{path}"
    except Exception:
        return raw


def _is_generic_news_hub(url: str) -> bool:
    raw = str(url or "").strip()
    if not raw.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(raw)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "/").rstrip("/") or "/"
    except Exception:
        return False
    if host.endswith("pokemon.com") and path in {"/us/pokemon-news", "/en-us/pokemon-news", "/pokemon-news"}:
        return True
    if host.endswith("pokemon.com") and path in {"/us", "/en-us", "/"}:
        return True
    return False


def _reader_url(source_url: str) -> str:
    cleaned = re.sub(r"^https?://", "", str(source_url or "").strip(), flags=re.I)
    return f"https://r.jina.ai/http://{cleaned}"


def _strip_html_tags(raw_html: str) -> str:
    text = str(raw_html or "")
    text = re.sub(r"(?is)<(script|style|noscript|svg|footer|header|nav).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    return _normalize_text(text)


def _clean_content_text(text: str) -> str:
    raw = str(text or "")
    raw = re.sub(r"(?is)^.*?Markdown Content:\s*", "", raw)
    raw = re.sub(r"(?im)^Title:\s*.*?$", " ", raw)
    raw = re.sub(r"(?im)^URL Source:\s*.*?$", " ", raw)
    raw = re.sub(r"(?im)^Published Time:\s*.*?$", " ", raw)
    raw = re.sub(r"(?im)^#+\s*", " ", raw)
    raw = re.sub(r"(?is)\[image[^\]]*\]", " ", raw)
    raw = re.sub(r"(?is)\[[^\]]{1,220}\]\((https?://[^)]+)\)", " ", raw)
    raw = re.sub(r"(?im)^\s*[-*]\s*\[[^\]]+\]\([^)]*\)\s*$", " ", raw)
    raw = raw.replace("[](", " ")
    raw = raw.replace(")[](", " ")
    raw = re.sub(r"\*{2,}", " ", raw)
    raw = re.sub(r"https?://[^\s]+", " ", raw)
    cleaned = _normalize_text(raw)
    cleaned = re.sub(r"(?:\bHome\b|\bMenu\b|\bNews\b|\bLog In\b|\bSign Up\b)(?:\s*[|/·-]\s*)?", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def _extract_meta_descriptions(html: str) -> list[str]:
    rows: list[str] = []
    patterns = [
        r'(?is)<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
        r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        r'(?is)<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\'](.*?)["\']',
    ]
    for pattern in patterns:
        for match in re.findall(pattern, html or ""):
            text = _clean_content_text(match)
            if len(text) >= 24 and text not in rows:
                rows.append(text)
    return rows


def _extract_html_paragraphs(html: str, limit: int = 6) -> list[str]:
    body = str(html or "")
    chunks = re.findall(r"(?is)<p[^>]*>(.*?)</p>", body)
    out: list[str] = []
    for chunk in chunks:
        text = _clean_content_text(_strip_html_tags(chunk))
        if len(text) < 38:
            continue
        if text in out:
            continue
        out.append(text)
        if len(out) >= max(1, int(limit)):
            break
    return out


def _fetch_html_excerpt(url: str, timeout_sec: int = 12) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout_sec)
        if resp.status_code >= 400:
            return ""
        html = str(resp.text or "")
        if len(html) < 120:
            return ""
        meta = _extract_meta_descriptions(html)
        paras = _extract_html_paragraphs(html, limit=4)
        stack: list[str] = []
        for row in [*meta, *paras]:
            cleaned = _clean_content_text(row)
            if len(cleaned) < 24 or cleaned in stack:
                continue
            stack.append(cleaned)
        if not stack:
            fallback = _clean_content_text(_strip_html_tags(html))
            if len(fallback) >= 120:
                stack.append(fallback[:900])
        return _normalize_text(" ".join(stack))[:1200]
    except Exception:
        return ""


def _fetch_reader_excerpt(url: str, timeout_sec: int = 12) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(_reader_url(url), headers=headers, timeout=timeout_sec)
        if resp.status_code >= 400:
            return ""
        raw = _clean_content_text(str(resp.text or ""))
        if len(raw) < 120:
            return ""
        return raw[:1400]
    except Exception:
        return ""


def _fetch_article_excerpt(url: str, timeout_sec: int = 12) -> str:
    if not str(url or "").startswith(("http://", "https://")):
        return ""
    html_excerpt = _fetch_html_excerpt(url, timeout_sec=timeout_sec)
    if len(html_excerpt) >= 80:
        return html_excerpt
    return _fetch_reader_excerpt(url, timeout_sec=timeout_sec)


def _parse_json_block(text: str) -> dict | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _minimax_chat(prompt: str, api_key: str, max_tokens: int | None = None) -> str:
    model_name = str(
        os.getenv("MINIMAX_TEXT_MODEL")
        or os.getenv("MINIMAX_MODEL")
        or "MiniMax-M2.7"
    ).strip() or "MiniMax-M2.7"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.25,
        "reasoning_split": False,
    }
    token_limit = max_tokens
    env_limit = str(os.getenv("MINIMAX_NEWS_MAX_TOKENS") or "").strip()
    if token_limit is None and env_limit:
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
    timeout_sec = 180
    env_timeout = str(os.getenv("MINIMAX_TEXT_TIMEOUT_SECONDS") or "").strip()
    if env_timeout:
        try:
            timeout_sec = max(30, int(env_timeout))
        except Exception:
            timeout_sec = 180
    resp = requests.post(MINIMAX_TEXT_URL, headers=headers, json=payload, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    # Some providers may return text in alternate fields.
    direct = data.get("reply") or data.get("output_text") or data.get("text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    base_resp = data.get("base_resp") if isinstance(data.get("base_resp"), dict) else {}
    status_msg = str(base_resp.get("status_msg") or "").strip()
    if status_msg:
        raise RuntimeError(f"MiniMax text response error: {status_msg}")
    raise RuntimeError(f"MiniMax text response missing content: model={model_name} keys={sorted(list(data.keys()))}")


def _extract_items(payload_text: str, query: str) -> list[dict]:
    if not payload_text:
        return []
    try:
        data = json.loads(payload_text)
    except Exception:
        data = None

    out: list[dict] = []
    if isinstance(data, dict):
        organic = data.get("organic")
        if isinstance(organic, list):
            for row in organic:
                if not isinstance(row, dict):
                    continue
                url = str(row.get("link") or row.get("url") or "").strip()
                if not url.startswith(("http://", "https://")):
                    continue
                title = str(row.get("title") or url).strip()
                date_text = str(row.get("date") or row.get("publishedDate") or "").strip()
                snippet = str(row.get("snippet") or row.get("description") or "").strip()
                out.append(
                    {
                        "title": title,
                        "url": url,
                        "date": date_text,
                        "snippet": snippet,
                        "source": _source_name(url),
                        "query": query,
                    }
                )
        if out:
            return out

    # Fallback: URL regex extraction from raw text.
    links = re.findall(r"https?://[^\s)>\"]+", payload_text)
    for link in links[:10]:
        out.append({"title": link, "url": link, "date": "", "snippet": "", "source": _source_name(link), "query": query})
    return out


def _extract_mmx_search_items(payload_text: str, query: str) -> list[dict]:
    rows = _extract_items(payload_text, query)
    if rows:
        return rows
    raw = str(payload_text or "")
    out: list[dict] = []
    line_chunks = [x.strip() for x in raw.splitlines() if x.strip()]
    for line in line_chunks:
        urls = re.findall(r"https?://[^\s)>\"]+", line)
        for url in urls:
            title = line.replace(url, " ").strip(" -:|")
            out.append(
                {
                    "title": title or url,
                    "url": url,
                    "date": "",
                    "snippet": title,
                    "source": _source_name(url),
                    "query": query,
                }
            )
    return out


def _mmx_bin() -> str:
    configured = str(os.getenv("MINIMAX_CLI_BIN") or "").strip()
    if configured:
        return configured
    return shutil.which("mmx") or ""


def _run_single_mmx_search(bin_path: str, query: str, api_key: str, api_host: str, timeout_sec: int) -> str:
    env = os.environ.copy()
    if api_key:
        env["MINIMAX_API_KEY"] = api_key
    if api_host:
        env["MINIMAX_API_HOST"] = api_host
        # mmx-cli uses MINIMAX_BASE_URL / --base-url instead of MINIMAX_API_HOST.
        env["MINIMAX_BASE_URL"] = api_host
    env["MINIMAX_OUTPUT"] = "json"
    variants = [
        [bin_path, "search", "query", "--q", query, "--output", "json", "--non-interactive"],
        [bin_path, "search", "web", "--q", query, "--output", "json", "--non-interactive"],
        [bin_path, "search", query, "--output", "json", "--non-interactive"],
    ]
    last_error = ""
    for cmd in variants:
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=max(8, int(timeout_sec)),
                env=env,
            )
        except Exception as exc:
            last_error = str(exc)
            continue
        stdout = str(proc.stdout or "").strip()
        stderr = str(proc.stderr or "").strip()
        if proc.returncode == 0 and stdout:
            return stdout
        last_error = stderr or stdout or f"exit {proc.returncode}"
        if "unknown command" not in last_error.lower() and "unknown option" not in last_error.lower():
            break
    raise RuntimeError(f"MiniMax CLI search failed: {last_error or 'no output'}")


def _run_queries_mmx_cli(queries: list[str], api_key: str, api_host: str, timeout_sec: int = 45) -> list[dict]:
    bin_path = _mmx_bin()
    if not bin_path:
        raise RuntimeError("MiniMax CLI not installed: install with `npm install -g mmx-cli` and authenticate with `mmx auth login --api-key ...`")
    collected: list[dict] = []
    per_query_timeout = max(10, min(int(timeout_sec), 60))
    for query in queries:
        payload_text = _run_single_mmx_search(bin_path, query, api_key, api_host, per_query_timeout)
        collected.extend(_extract_mmx_search_items(payload_text, query))
    return collected


async def _run_queries_mcp(queries: list[str], api_key: str, api_host: str) -> list[dict]:
    if ClientSession is None or StdioServerParameters is None or stdio_client is None:
        raise RuntimeError("MCP package is not installed; use NEWS_SEARCH_PROVIDER=mmx or install mcp dependencies")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "uv", "tool", "run", "minimax-coding-plan-mcp", "-y"],
        env={
            "MINIMAX_API_KEY": api_key,
            "MINIMAX_API_HOST": api_host,
        },
    )
    collected: list[dict] = []
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            if "web_search" not in names:
                raise RuntimeError(f"MiniMax MCP 缺少 web_search，tools={sorted(names)}")
            for query in queries:
                reply = await session.call_tool("web_search", {"query": query})
                payload_text = _extract_text_payload(reply)
                collected.extend(_extract_items(payload_text, query))
    return collected


def _news_search_provider() -> str:
    raw = str(os.getenv("NEWS_SEARCH_PROVIDER") or os.getenv("POKEMON_NEWS_PROVIDER") or "mmx").strip().lower()
    if raw in {"cli", "mmx", "minimax_cli"}:
        return "mmx"
    if raw in {"mcp", "minimax_mcp"}:
        return "mcp"
    if raw in {"off", "false", "0", "disabled", "none"}:
        return "disabled"
    if raw == "auto":
        return "auto"
    return "mmx"


def _run_queries(queries: list[str], api_key: str, api_host: str, timeout_sec: int = 45) -> tuple[list[dict], str]:
    provider = _news_search_provider()
    if provider == "disabled":
        raise RuntimeError("News search disabled by NEWS_SEARCH_PROVIDER=disabled")
    if provider == "mcp":
        return asyncio.run(asyncio.wait_for(_run_queries_mcp(queries, api_key, api_host), timeout=max(10, int(timeout_sec)))), "minimax_mcp_web_search"
    if provider == "auto":
        errors: list[str] = []
        try:
            return _run_queries_mmx_cli(queries, api_key, api_host, timeout_sec=timeout_sec), "minimax_cli_search"
        except Exception as exc:
            errors.append(f"mmx={exc}")
        if str(os.getenv("NEWS_ALLOW_MCP_FALLBACK") or "").strip().lower() in {"1", "true", "yes", "on"}:
            try:
                return asyncio.run(asyncio.wait_for(_run_queries_mcp(queries, api_key, api_host), timeout=max(10, int(timeout_sec)))), "minimax_mcp_web_search"
            except Exception as exc:
                errors.append(f"mcp={exc}")
        raise RuntimeError("; ".join(errors) or "no news search provider succeeded")
    return _run_queries_mmx_cli(queries, api_key, api_host, timeout_sec=timeout_sec), "minimax_cli_search"


def _dedupe_items(items: list[dict], max_items: int) -> list[dict]:
    prepared: list[tuple[int, dict]] = []
    generic_pool: list[tuple[int, dict]] = []
    for idx, row in enumerate(items):
        if not isinstance(row, dict):
            continue
        item = dict(row)
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        source = _source_name(url)
        if not _is_allowed_source(source):
            continue
        item["source"] = source
        if _is_generic_news_hub(url):
            generic_pool.append((idx, item))
        else:
            prepared.append((idx, item))

    if not prepared and generic_pool:
        prepared = generic_pool

    indexed = prepared
    indexed.sort(
        key=lambda pair: (
            _source_priority((pair[1] or {}).get("source") or _source_name((pair[1] or {}).get("url"))),
            pair[0],
        )
    )
    out: list[dict] = []
    seen: set[str] = set()
    for _, item in indexed:
        url = str(item.get("url") or "").strip()
        key = _canonical_url(url)
        if not url or key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= max(1, int(max_items)):
            break

    if len(out) < max(2, min(4, max_items)) and generic_pool:
        generic_pool.sort(
            key=lambda pair: (
                _source_priority((pair[1] or {}).get("source") or _source_name((pair[1] or {}).get("url"))),
                pair[0],
            )
        )
        for _, item in generic_pool:
            url = str(item.get("url") or "").strip()
            key = _canonical_url(url)
            if not url or key in seen:
                continue
            seen.add(key)
            out.append(item)
            if len(out) >= max(1, int(max_items)):
                break
    return out


def _source_priority(source: str) -> int:
    s = _normalize_text(source).lower()
    if not s:
        return 9
    if _is_official_source(s):
        return 0
    if _is_secondary_source(s):
        return 1
    if _is_blocked_source(s):
        return 7
    return 4


def _truncate_text(text: str, limit: int) -> str:
    safe = _normalize_text(text)
    if len(safe) <= max(1, int(limit)):
        return safe
    return f"{safe[:max(1, int(limit) - 1)].rstrip()}…"


def _clean_title(text: str) -> str:
    title = _normalize_text(text)
    if not title:
        return "未命名消息"
    # Strip common source suffixes.
    title = re.sub(r"\s*[|｜]\s*(pokemon\.com|youtube|polygon|reddit|x|twitter|threads).*$", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*(youtube|pokemon\.com|polygon|reddit|x|twitter|threads).*$", "", title, flags=re.I)
    title = _normalize_text(title)
    return title or "未命名消息"


def _split_sentences(text: str) -> list[str]:
    raw = _clean_content_text(_normalize_text(text))
    if not raw:
        return []
    parts = re.split(r"(?:[。！？!?；;]+|(?<=[a-z0-9])\.(?=\s+[A-Z]))", raw)
    out: list[str] = []
    for part in parts:
        row = _clean_content_text(_normalize_text(part))
        if len(row) < 12:
            continue
        if len(row) > 240:
            row = _truncate_text(row, 240)
        out.append(row)
    return out


def _is_noise_sentence(text: str) -> bool:
    row = _normalize_text(text).lower()
    if not row:
        return True
    noisy_terms = [
        "official site",
        "instagram",
        "tiktok",
        "snapchat",
        "subscribe",
        "cookie",
        "privacy policy",
        "all rights reserved",
        "sign in",
        "log in",
        "view all",
        "watch now",
        "javascript",
        "skip to main",
        "skip to navigation",
        "terms of use",
        "cookie policy",
        "not responsible for the content",
        "privacy practices may differ",
        "privacy policies and security practices may differ",
        "please note that these websites",
        "click continue to visit",
        "if you click on the youtube video",
        "leave pokemon.com",
    ]
    if any(term in row for term in noisy_terms):
        return True
    if row.startswith("[image") or row.startswith("image "):
        return True
    if "source=" in row or "utm_" in row or "url source:" in row or "published time:" in row:
        return True
    if "http://" in row or "https://" in row:
        return True
    if re.search(r"(?:\[\]|\*\s*){3,}", row):
        return True
    if re.search(r"^\[[^\]]{1,30}\:\s*", row):
        return True
    if re.search(r"\.(png|jpg|jpeg|webp|gif)\b", row):
        return True
    if row.startswith(("home ", "menu ", "news ", "share ", "comments ")):
        return True
    if len(re.findall(r"[\[\]\*\(\)]", row)) >= 8:
        return True
    alpha_num = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", row)
    if len(alpha_num) < 8:
        return True
    return False


def _extract_focus_sentences(item: dict, limit: int = 4) -> list[str]:
    title = _clean_content_text(_normalize_text(item.get("title") or ""))
    snippet = _clean_content_text(_normalize_text(item.get("snippet") or ""))
    excerpt = _clean_content_text(_normalize_text(item.get("article_excerpt") or ""))
    stack: list[str] = []
    for src in (snippet, excerpt, title):
        for sentence in _split_sentences(src):
            if _is_noise_sentence(sentence):
                continue
            norm = sentence.lower()
            if any(norm == s.lower() or norm in s.lower() or s.lower() in norm for s in stack):
                continue
            stack.append(sentence)
            if len(stack) >= max(1, int(limit)):
                break
        if len(stack) >= max(1, int(limit)):
            break
    if not stack and title:
        stack.append(title)
    return stack[: max(1, int(limit))]


def _infer_topic(title: str, snippet: str, excerpt: str, source: str) -> str:
    blob = _normalize_text(" ".join([title, snippet, excerpt, source])).lower()
    if any(x in blob for x in ["pokemon go", "raid", "community day", "go battle", "go fest"]):
        return "Pokémon GO"
    if any(x in blob for x in ["patch", "update notes", "version", "roadmap", "maintenance", "hotfix"]):
        return "功能/版本更新"
    if any(x in blob for x in ["event", "fest", "tour", "festival", "championship", "tournament", "ticket", "register", "presents"]):
        return "活動/賽事"
    if any(x in blob for x in ["tcg", "booster", "elite trainer box", "expansion", "product release", "collection", "set"]):
        return "卡牌/商品發售"
    if any(x in blob for x in ["reward", "bonus", "gift", "prize", "drop"]):
        return "福利/獎勵消息"
    return "官方消息"


def _extract_time_hint(date_text: str, title: str, snippet: str, excerpt: str) -> str:
    explicit = _normalize_text(date_text)
    if explicit:
        return explicit
    blob = _normalize_text(" ".join([title, snippet, excerpt]))
    match_iso = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", blob)
    if match_iso:
        y, m, d = match_iso.groups()
        return f"{y}/{int(m):02d}/{int(d):02d}"
    match_month = re.search(r"\b([A-Za-z]{3,9})\s+(\d{1,2})(?:,\s*(20\d{2}))?\b", blob)
    if match_month:
        month_raw, day_raw, year_raw = match_month.groups()
        month_num = MONTH_MAP.get(month_raw.lower())
        if month_num:
            if year_raw:
                return f"{year_raw}/{month_num:02d}/{int(day_raw):02d}"
            return f"{month_num}/{int(day_raw)}"
    match_zh = re.search(r"(\d{1,2})月(\d{1,2})[日号號]?", blob)
    if match_zh:
        return f"{match_zh.group(1)}/{match_zh.group(2)}"
    return "未標示"


def _extract_reward_hint(title: str, snippet: str, excerpt: str) -> str:
    blob = _normalize_text(" ".join([title, snippet, excerpt]))
    lower = blob.lower()
    reward_terms = ["reward", "bonus", "gift", "prize", "drop", "sbt", "coupon", "ticket", "invitation"]
    if not any(term in lower for term in reward_terms):
        return ""
    lines = _split_sentences(blob)
    for line in lines:
        l = line.lower()
        if any(term in l for term in reward_terms):
            if _is_noise_sentence(line):
                continue
            return _truncate_text(line, 72)
    return "提及獎勵或福利條件，建議閱讀原文確認領取方式。"


def _build_action_hint(topic: str, title: str, snippet: str, excerpt: str) -> str:
    blob = _normalize_text(" ".join([title, snippet, excerpt])).lower()
    if any(k in blob for k in ["update", "patch", "version"]):
        return "先看更新內容與適用版本，再安排是否跟進。"
    if any(k in blob for k in ["release", "launch", "available", "preorder"]):
        return "先記下上線或發售時間，確認購買/下載管道。"
    if topic == "活動/賽事" and any(k in blob for k in ["register", "registration", "ticket", "sign up", "apply"]):
        return "先確認報名/購票條件與截止時間。"
    if topic == "活動/賽事":
        return "先確認時區、地點與參與方式。"
    return "先讀原文確認完整條件，再決定是否追蹤。"


def _summary_title_from_topic(topic: str, title: str) -> str:
    clean = _clean_title(title)
    if topic == "活動/賽事":
        return _truncate_text(f"活動快訊｜{clean}", 136)
    if topic == "卡牌/商品發售":
        return _truncate_text(f"發售更新｜{clean}", 136)
    if topic == "功能/版本更新":
        return _truncate_text(f"功能更新｜{clean}", 136)
    if topic == "Pokémon GO":
        return _truncate_text(f"GO 更新｜{clean}", 136)
    if topic == "福利/獎勵消息":
        return _truncate_text(f"獎勵資訊｜{clean}", 136)
    return _truncate_text(f"官方消息｜{clean}", 136)


def _fallback_summary_item(item: dict, lang: str) -> dict:
    title = _clean_title(item.get("title") or "")
    snippet = _clean_content_text(_normalize_text(item.get("snippet") or ""))
    excerpt = _clean_content_text(_normalize_text(item.get("article_excerpt") or ""))
    source = _normalize_text(item.get("source") or _source_name(item.get("url")))
    date_text = _normalize_text(item.get("date") or "")
    focus_lines = _extract_focus_sentences(item, limit=4)
    topic = _infer_topic(title, snippet, excerpt, source)
    lead = _truncate_text(focus_lines[0] if focus_lines else (snippet or title), 118)
    time_hint = _extract_time_hint(date_text, title, snippet, excerpt)
    reward_hint = _extract_reward_hint(title, snippet, excerpt)
    action_hint = _build_action_hint(topic, title, snippet, excerpt)
    if lang.startswith("zh"):
        summary = f"{topic}重點：{title}"
        if lead and lead.lower() not in title.lower():
            summary += f"；摘要：{_truncate_text(lead, 66)}"
        points = [
            f"這在講什麼：{_truncate_text(lead or title, 98)}",
            f"時間：{time_hint}",
            f"你要做什麼：{action_hint}",
        ]
        detail_lines = [
            f"主題分類：{topic}",
            f"內容摘要：{_truncate_text(lead or snippet or title, 180)}",
            f"時間資訊：{time_hint}",
            f"執行建議：{action_hint}",
        ]
        if reward_hint:
            detail_lines[1] = f"內容摘要：{_truncate_text(lead or snippet or title, 122)}；獎勵線索：{reward_hint}"
    elif lang == "ja":
        summary = _truncate_text(snippet or "詳細は原文リンクで確認してください。", 220)
        points = [
            f"ソース: {source}",
            f"日付: {date_text or '未記載'}",
            "要点: 公式情報を優先して確認。",
        ]
        detail_lines = focus_lines[:4] or ["公式情報を確認してください。"]
    elif lang == "ko":
        summary = _truncate_text(snippet or "상세 내용은 원문 링크에서 확인하세요.", 220)
        points = [
            f"출처: {source}",
            f"날짜: {date_text or '미표기'}",
            "핵심: 공식 공지를 우선 확인.",
        ]
        detail_lines = focus_lines[:4] or ["원문 링크에서 공지 내용을 확인하세요."]
    else:
        summary = _truncate_text(snippet or "Open the original source for complete details.", 220)
        points = [
            f"Source: {source}",
            f"Date: {date_text or 'N/A'}",
            "Key: verify official details before acting.",
        ]
        detail_lines = focus_lines[:4] or ["Open original source for complete details."]
    return {
        "summary_title": _summary_title_from_topic(topic, title),
        "summary": _truncate_text(summary, 260),
        "key_points": [p[:120] for p in points],
        "detail_lines": [str(x)[:220] for x in detail_lines if _normalize_text(x)][:4],
    }


def _is_low_quality_generated_text(text: str) -> bool:
    row = _normalize_text(text).lower()
    if not row:
        return True
    flags = [
        "url source:",
        "markdown content",
        "http://",
        "https://",
        "all rights reserved",
        "privacy policy",
        "skip to",
        "依網址判断",
        "依網址判斷",
        "從網址判斷",
        "根据网址判断",
        "根據網址判斷",
        "猜測",
        "推測",
        "probably",
        "likely",
        "from the url",
        "based on the url",
    ]
    return any(flag in row for flag in flags)


def _batch_summarize_items(items: list[dict], api_key: str, lang: str) -> list[dict]:
    if not items:
        return []
    if len(items) > 1:
        out: list[dict] = []
        for item in items:
            try:
                out.extend(_batch_summarize_items([item], api_key=api_key, lang=lang))
            except Exception:
                out.append({**item, **_fallback_summary_item(item, lang)})
        return out
    lang_hint = _lang_prompt_hint(lang)
    compact_rows = []
    for idx, item in enumerate(items, start=1):
        compact_rows.append(
            {
                "idx": idx,
                "url": _normalize_text(item.get("url")),
                "title": _normalize_text(item.get("title")),
                "date": _normalize_text(item.get("date")),
                "source": _normalize_text(item.get("source")),
                "snippet": _normalize_text(item.get("snippet")),
                "excerpt": _normalize_text(item.get("article_excerpt"))[:1800],
            }
        )

    prompt = (
        "你是專業新聞編輯。請逐條閱讀輸入內容，對每則新聞輸出可讀整理。"
        f"所有輸出必須使用：{lang_hint}。\n"
        "輸出只允許 JSON，格式："
        '{"items":[{"idx":1,"summary_title":"...","summary":"...","key_points":["...","...","..."],"detail_lines":["...","...","...","..."]}]}\n'
        "規則：\n"
        "1) summary_title 必須是讀者看得懂的整理標題，不可原樣複製整段英文。\n"
        "2) summary 需為濃縮摘要，突出事件本質，避免空話。\n"
        "3) key_points 固定 3 條，內容要有資訊密度（時間/內容/影響）。\n"
        "4) detail_lines 固定 4 條，列出更細的重點敘述。\n"
        "5) 若資訊不足，明確指出需看原文確認。\n"
        "6) 禁止捏造；不可依網址、標題或常識猜地點/時間/獎勵。沒有明確寫出就寫「未標示」或「需看原文確認」。\n"
        "7) 禁止出現「依網址判斷」「猜測」「推測」「probably」「likely」等字眼。\n\n"
        f"新聞資料：{json.dumps(compact_rows, ensure_ascii=False)}"
    )

    raw = _minimax_chat(prompt, api_key)
    parsed = _parse_json_block(raw) or {}
    rows = parsed.get("items") if isinstance(parsed.get("items"), list) else []

    out: list[dict] = []
    index_map = {int(i + 1): items[i] for i in range(len(items))}
    if not rows:
        for item in items:
            out.append({**item, **_fallback_summary_item(item, lang)})
        return out

    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            idx = int(row.get("idx"))
        except Exception:
            continue
        source_item = index_map.get(idx)
        if not source_item:
            continue
        seen.add(idx)
        summary_title = _clean_content_text(_normalize_text(row.get("summary_title") or source_item.get("title")))
        summary = _clean_content_text(_normalize_text(row.get("summary") or source_item.get("snippet")))
        key_points_raw = row.get("key_points") if isinstance(row.get("key_points"), list) else []
        key_points = [_clean_content_text(_normalize_text(x))[:120] for x in key_points_raw if _normalize_text(x)]
        detail_lines_raw = row.get("detail_lines") if isinstance(row.get("detail_lines"), list) else []
        detail_lines = [_clean_content_text(_normalize_text(x))[:220] for x in detail_lines_raw if _normalize_text(x)]
        low_quality = _is_low_quality_generated_text(summary_title) or _is_low_quality_generated_text(summary)
        if len(key_points) < 3:
            low_quality = True
        if low_quality:
            fb = _fallback_summary_item(source_item, lang)
            summary_title = fb["summary_title"]
            summary = fb["summary"]
            key_points = list(key_points) if key_points else []
            for p in fb["key_points"]:
                if len(key_points) >= 3:
                    break
                if p not in key_points:
                    key_points.append(p)
            detail_lines = list(detail_lines) if detail_lines else []
            for line in fb.get("detail_lines", []):
                if len(detail_lines) >= 4:
                    break
                if line not in detail_lines:
                    detail_lines.append(line)
        out.append(
            {
                **source_item,
                "summary_title": _truncate_text(summary_title[:140] or _clean_title(source_item.get("title")), 140),
                "summary": _truncate_text(summary[:260] or _fallback_summary_item(source_item, lang)["summary"], 260),
                "key_points": key_points[:3],
                "detail_lines": detail_lines[:4],
            }
        )

    # Append missing indices with fallback.
    for idx, source_item in index_map.items():
        if idx in seen:
            continue
        out.append({**source_item, **_fallback_summary_item(source_item, lang)})

    # Keep original order.
    ordered: list[dict] = []
    url_pos = {str(x.get("url")): i for i, x in enumerate(items)}
    ordered = sorted(out, key=lambda x: url_pos.get(str(x.get("url")), 9999))
    return ordered


def translate_pokemon_news_payload(payload: dict, lang: str, api_key: str | None = None) -> dict:
    """Translate a canonical Pokemon news payload without running web search again."""
    target_lang = _normalize_lang(lang)
    source = dict(payload) if isinstance(payload, dict) else {}
    source_lang = _normalize_lang(str(source.get("lang") or "zh-Hant"))
    if target_lang == source_lang:
        out = dict(source)
        out["lang"] = target_lang
        return out

    items = source.get("items") if isinstance(source.get("items"), list) else []
    if not items:
        out = dict(source)
        out["lang"] = target_lang
        out["translation_source_lang"] = source_lang
        out["summary_mode"] = f"{source.get('summary_mode') or 'unknown'}+translated"
        return out
    if len(items) > 1:
        translated_items: list[dict] = []
        for item in items:
            chunk_payload = dict(source)
            chunk_payload["items"] = [item]
            try:
                translated_items.extend(translate_pokemon_news_payload(chunk_payload, target_lang, api_key=api_key).get("items") or [])
            except Exception:
                translated_items.extend(dict(x) for x in chunk_payload.get("items", []) if isinstance(x, dict))
        out = dict(source)
        out["lang"] = target_lang
        out["translation_source_lang"] = source_lang
        out["summary_mode"] = f"{source.get('summary_mode') or 'ai'}+translated"
        out["items"] = translated_items
        return out

    key = (api_key or _resolve_minimax_credentials()[0]).strip()
    if not key:
        raise RuntimeError("未設定 MINIMAX_API_KEY，無法翻譯 NewsAgent 快取")

    lang_hint = _lang_prompt_hint(target_lang)
    rows = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "idx": idx,
                "summary_title": _normalize_text(item.get("summary_title") or item.get("title")),
                "summary": _normalize_text(item.get("summary")),
                "key_points": [_normalize_text(x) for x in (item.get("key_points") if isinstance(item.get("key_points"), list) else [])],
                "detail_lines": [_normalize_text(x) for x in (item.get("detail_lines") if isinstance(item.get("detail_lines"), list) else [])],
                "detail_excerpt": _normalize_text(item.get("detail_excerpt")),
            }
        )

    prompt = (
        "你是 News Translation Agent。請只翻譯已整理好的新聞卡片，不要重新搜尋、不要改變事實、不要新增猜測。\n"
        f"目標語言：{lang_hint}\n"
        "輸出只允許 JSON，格式："
        '{"items":[{"idx":1,"summary_title":"...","summary":"...","key_points":["..."],"detail_lines":["..."],"detail_excerpt":"..."}]}\n'
        "規則：\n"
        "1) idx 必須對應原資料，順序不重要但不可漏。\n"
        "2) 保留 URL、來源、日期、數字、貨幣、Pokemon/Pokémon、TCG、SBT 等專有名詞。\n"
        "3) 不可把未標示改成具體時間或地點。\n"
        "4) 不要輸出 Markdown，不要附註解。\n\n"
        f"source={json.dumps(rows, ensure_ascii=False)}"
    )
    raw = _minimax_chat(prompt, key)
    parsed = _parse_json_block(raw) or {}
    translated_rows = parsed.get("items") if isinstance(parsed.get("items"), list) else []
    by_idx: dict[int, dict] = {}
    for row in translated_rows:
        if not isinstance(row, dict):
            continue
        try:
            idx = int(row.get("idx"))
        except Exception:
            continue
        by_idx[idx] = row

    out_items = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        new_item = dict(item)
        row = by_idx.get(idx) or {}
        for key_name in ("summary_title", "summary", "detail_excerpt"):
            value = _clean_content_text(_normalize_text(row.get(key_name) or ""))
            if value and not _is_low_quality_generated_text(value):
                new_item[key_name] = _truncate_text(value, 760 if key_name == "detail_excerpt" else 260)
        for key_name, limit, item_limit in (("key_points", 3, 140), ("detail_lines", 4, 240)):
            value = row.get(key_name)
            if isinstance(value, list):
                cleaned = [_clean_content_text(_normalize_text(x))[:item_limit] for x in value if _normalize_text(x)]
                if cleaned:
                    new_item[key_name] = cleaned[:limit]
        out_items.append(new_item)

    out = dict(source)
    out["lang"] = target_lang
    out["translation_source_lang"] = source_lang
    out["summary_mode"] = f"{source.get('summary_mode') or 'ai'}+translated"
    out["items"] = out_items
    return out


def fetch_pokemon_latest_news(
    *,
    max_items: int = 8,
    timeout_sec: int = 45,
    queries: list[str] | None = None,
    lang: str = "zh-Hant",
) -> dict:
    api_key, api_host = _resolve_minimax_credentials()
    if not api_key:
        raise RuntimeError("未設定 MINIMAX_API_KEY（可放在專案 .env 或 old/tcg_pro/.env）")
    out_lang = _normalize_lang(lang)
    query_seed = queries if queries else _default_queries_for_lang(out_lang)
    query_list = [str(x).strip() for x in query_seed if str(x).strip()]
    if not query_list:
        raise RuntimeError("查詢字串為空")

    collected, provider = _run_queries(query_list, api_key, api_host, timeout_sec=timeout_sec)
    merged = _dedupe_items(collected, max_items=max_items)
    for item in merged:
        item["source"] = _source_name(item.get("url"))
        item["title"] = _clean_title(item.get("title") or "")
        item["snippet"] = _clean_content_text(item.get("snippet") or "")
        item["article_excerpt"] = _clean_content_text(_fetch_article_excerpt(str(item.get("url") or "")))
    summary_mode = "ai"
    try:
        summarized = _batch_summarize_items(merged, api_key=api_key, lang=out_lang)
    except Exception:
        summary_mode = "fallback"
        summarized = [{**item, **_fallback_summary_item(item, out_lang)} for item in merged]
    for item in summarized:
        excerpt_sentences = [s for s in _split_sentences(item.get("article_excerpt") or "") if not _is_noise_sentence(s)]
        item["detail_excerpt"] = _truncate_text(" ".join(excerpt_sentences[:3]), 760)
        item.pop("article_excerpt", None)

    return {
        "generated_at": _now_iso(),
        "provider": provider,
        "lang": out_lang,
        "summary_mode": summary_mode,
        "query_count": len(query_list),
        "items": summarized,
    }
