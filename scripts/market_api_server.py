import os
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

import market_monitor as mm


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe_cheapest(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for item in items:
        name = str(item.get("name") or "")
        grade = str(item.get("grade") or "")
        ask = float(item.get("ask_price") or 0.0)
        key = f"{name}_{grade}".lower()
        existing = grouped.get(key)
        if not existing or ask < float(existing.get("ask_price") or 0.0):
            grouped[key] = item
    return list(grouped.values())


def _safe_pct(avg_price: Optional[float], ask_price: float) -> Optional[float]:
    if avg_price is None or avg_price <= 0:
        return None
    return ((avg_price - ask_price) / avg_price) * 100.0


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _normalize_source_records(
    records: List[Dict[str, Any]],
    source: str,
    jpy_rate: float,
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for rec in records or []:
        raw = dict(rec or {})
        raw_date = str(raw.get("date") or "").strip()
        dt = mm.parse_date_string(raw_date) if raw_date else None
        price = _safe_float(raw.get("price"))

        if source == "snkrdunk":
            price_jpy = price
            price_usd = (price / jpy_rate) if (price is not None and jpy_rate > 0) else None
            currency = "JPY"
        else:
            price_jpy = None
            price_usd = price
            currency = "USD"

        normalized.append(
            {
                "date_raw": raw.get("date"),
                "date_iso": dt.isoformat() if dt else None,
                "grade": raw.get("grade"),
                "price": price,
                "price_usd": price_usd,
                "price_jpy": price_jpy,
                "currency": currency,
                "note": raw.get("note"),
                "record": raw,
            }
        )
    return normalized


def _target_grade_from_name(full_name: str) -> str:
    try:
        _, _, _, _, grade_tag = mm.parse_renaiss_name(full_name)
        return str(grade_tag or "Unknown")
    except Exception:
        return "Unknown"


def _filter_records_by_target_grade(
    records: List[Dict[str, Any]],
    target_grade: str,
) -> List[Dict[str, Any]]:
    if not records:
        return []

    grade_key = str(target_grade or "Unknown")
    grade_key_compact = grade_key.replace(" ", "")
    matched: List[Dict[str, Any]] = []
    for rec in records:
        r_grade = str((rec or {}).get("grade") or "")
        if r_grade == grade_key:
            matched.append(rec)
            continue
        if grade_key == "Unknown" and r_grade in ("Ungraded", "裸卡", "A"):
            matched.append(rec)
            continue
        if r_grade == grade_key_compact:
            matched.append(rec)
            continue
    return matched


def _pick_best_market(
    ask_price: float,
    pc_avg: Optional[float],
    snkr_avg: Optional[float],
) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    if pc_avg is not None:
        candidates.append(
            {
                "market": "PriceCharting",
                "profit_usd": pc_avg - ask_price,
                "diff_pct": _safe_pct(pc_avg, ask_price),
            }
        )
    if snkr_avg is not None:
        candidates.append(
            {
                "market": "SNKRDUNK",
                "profit_usd": snkr_avg - ask_price,
                "diff_pct": _safe_pct(snkr_avg, ask_price),
            }
        )
    if not candidates:
        return {"market": None, "profit_usd": None, "diff_pct": None}
    return max(candidates, key=lambda item: float(item["profit_usd"]))


def _analyze_listing(
    item: Dict[str, Any],
    threshold_pct: float,
    include_full_records: bool = True,
) -> Dict[str, Any]:
    item_id = str(item.get("item_id") or "")
    full_name = str(item.get("name") or "")
    ask = float(item.get("ask_price") or 0.0)
    company = full_name.split()[0] if ("PSA" in full_name or "BGS" in full_name) else "Unknown"

    year = 0
    for token in full_name.split():
        if token.isdigit() and len(token) == 4 and token.startswith("20"):
            year = int(token)
            break

    current_jpy_rate = mm.fetch_jpy_rate()
    pc_info, snkr_info = mm.fetch_and_analyze_realtime(
        item_id=item_id,
        full_name=full_name,
        grading_company=company,
        year=year,
        current_jpy_rate=current_jpy_rate,
        attributes=item.get("attributes"),
        include_records=include_full_records,
    )
    if include_full_records:
        pc_avg, pc_count, pc_url, pc_records = pc_info
        snkr_avg, snkr_count, snkr_url, snkr_records = snkr_info
    else:
        pc_avg, pc_count, pc_url = pc_info
        snkr_avg, snkr_count, snkr_url = snkr_info
        pc_records = []
        snkr_records = []

    target_grade = _target_grade_from_name(full_name)
    pc_records_filtered = _filter_records_by_target_grade(pc_records, target_grade)
    snkr_records_filtered = _filter_records_by_target_grade(snkr_records, target_grade)

    pc_diff_pct = _safe_pct(pc_avg, ask)
    snkr_diff_pct = _safe_pct(snkr_avg, ask)

    meets_pc = pc_diff_pct is not None and pc_diff_pct >= threshold_pct
    meets_snkr = snkr_diff_pct is not None and snkr_diff_pct >= threshold_pct

    best = _pick_best_market(ask, pc_avg, snkr_avg)
    estimated_profit_usd = best["profit_usd"]

    result = {
        "item_id": item_id,
        "name": full_name,
        "grade": item.get("grade"),
        "target_grade": target_grade,
        "ask_price_usd": ask,
        "renaiss_url": item.get("renaiss_url"),
        "image_url": item.get("image_url"),
        "sources": {
            "pricecharting": {
                "avg_price_usd": pc_avg,
                "sample_count": pc_count,
                "diff_pct": pc_diff_pct,
                "url": pc_url,
                "meets_threshold": meets_pc,
                "records_total": len(pc_records_filtered),
            },
            "snkrdunk": {
                "avg_price_usd": snkr_avg,
                "sample_count": snkr_count,
                "diff_pct": snkr_diff_pct,
                "url": snkr_url,
                "meets_threshold": meets_snkr,
                "records_total": len(snkr_records_filtered),
            },
        },
        "best_market": best["market"],
        "estimated_profit_usd": estimated_profit_usd,
        "estimated_diff_pct": best["diff_pct"],
        "is_opportunity": bool(meets_pc or meets_snkr),
    }

    if include_full_records:
        result["sources"]["pricecharting"]["records_raw"] = pc_records_filtered
        result["sources"]["snkrdunk"]["records_raw"] = snkr_records_filtered
        result["sources"]["pricecharting"]["records_normalized"] = _normalize_source_records(
            pc_records_filtered, "pricecharting", current_jpy_rate
        )
        result["sources"]["snkrdunk"]["records_normalized"] = _normalize_source_records(
            snkr_records_filtered, "snkrdunk", current_jpy_rate
        )

    return result


def _wallet_actionable(
    analyzed: Dict[str, Any],
    min_profit_usd: float,
    wallet_budget_usd: Optional[float],
) -> bool:
    if not analyzed.get("is_opportunity"):
        return False
    est_profit = analyzed.get("estimated_profit_usd")
    ask_price = float(analyzed.get("ask_price_usd") or 0.0)
    if est_profit is None or float(est_profit) < min_profit_usd:
        return False
    if wallet_budget_usd is not None and ask_price > wallet_budget_usd:
        return False
    return True


def _post_wallet_signal(payload: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = os.getenv("AGENT_WALLET_WEBHOOK_URL", "").strip()
    if not endpoint:
        return {"sent": False, "reason": "AGENT_WALLET_WEBHOOK_URL not set"}
    try:
        resp = requests.post(endpoint, json=payload, timeout=15)
        return {"sent": resp.status_code < 300, "status_code": resp.status_code}
    except Exception as exc:  # pragma: no cover
        return {"sent": False, "reason": str(exc)}


class ScanRequest(BaseModel):
    # Deprecated alias: if provided, it will override keep_limit for compatibility.
    limit: Optional[int] = Field(default=None, ge=1, le=30)
    scan_limit: int = Field(default=30, ge=1, le=100)
    keep_limit: int = Field(default=10, ge=1, le=30)
    threshold_percent: float = 10.0
    min_profit_usd: float = Field(default=0.0, ge=0.0)
    wallet_budget_usd: Optional[float] = Field(default=None, ge=0.0)
    include_full_records: bool = True
    only_actionable: bool = True
    notify_wallet: bool = False
    use_cache: bool = True
    force_refresh: bool = False
    cache_ttl_seconds: Optional[int] = Field(default=None, ge=0, le=86400)
    reference_id: Optional[str] = None


class AnalyzeByItemIdRequest(BaseModel):
    item_id: str = Field(min_length=1)
    threshold_percent: float = 10.0
    min_profit_usd: float = Field(default=0.0, ge=0.0)
    wallet_budget_usd: Optional[float] = Field(default=None, ge=0.0)
    include_full_records: bool = True


app = FastAPI(
    title="Renassis Market API",
    version="1.0.0",
    description="HTTP API for market opportunities, built for agent wallet integration.",
)

_CACHE_LOCK = threading.Lock()
_SCAN_LOCK = threading.Lock()
_CACHE_FILE = os.getenv(
    "OPPORTUNITY_CACHE_FILE",
    os.path.join(os.path.dirname(__file__), "cache", "opportunities_latest.json"),
)
_CACHE_TTL_SECONDS = int(os.getenv("OPPORTUNITY_CACHE_TTL_SECONDS", "300"))
_AUTO_REFRESH_ENABLED = os.getenv("OPPORTUNITY_AUTO_REFRESH_ENABLED", "true").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
_AUTO_REFRESH_INTERVAL_SECONDS = int(os.getenv("OPPORTUNITY_AUTO_REFRESH_INTERVAL_SECONDS", "300"))


def _truthy_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def _scan_cache_key(
    *,
    scan_limit: int,
    keep_limit: int,
    threshold_percent: float,
    min_profit_usd: float,
    wallet_budget_usd: Optional[float],
    include_full_records: bool,
    only_actionable: bool,
) -> str:
    key_obj = {
        "scan_limit": scan_limit,
        "keep_limit": keep_limit,
        "threshold_percent": round(float(threshold_percent), 6),
        "min_profit_usd": round(float(min_profit_usd), 6),
        "wallet_budget_usd": None if wallet_budget_usd is None else round(float(wallet_budget_usd), 6),
        "include_full_records": bool(include_full_records),
        "only_actionable": bool(only_actionable),
    }
    return json.dumps(key_obj, sort_keys=True, separators=(",", ":"))


def _read_cache_store() -> Dict[str, Any]:
    if not os.path.exists(_CACHE_FILE):
        return {"entries": {}, "latest_key": None}
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"entries": {}, "latest_key": None}
        data.setdefault("entries", {})
        data.setdefault("latest_key", None)
        return data
    except Exception:
        return {"entries": {}, "latest_key": None}


def _write_cache_store(store: Dict[str, Any]) -> None:
    cache_dir = os.path.dirname(_CACHE_FILE)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False)


def _get_cached_scan_payload(cache_key: str, max_age_seconds: int) -> Optional[Dict[str, Any]]:
    with _CACHE_LOCK:
        store = _read_cache_store()
        entry = (store.get("entries") or {}).get(cache_key)
        if not entry:
            return None
        saved_at_unix = int(entry.get("saved_at_unix") or 0)
        age = int(time.time()) - saved_at_unix
        if max_age_seconds >= 0 and age > max_age_seconds:
            return None
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            return None
        result = dict(payload)
        result["cache"] = {
            "hit": True,
            "saved_at_unix": saved_at_unix,
            "saved_at_utc": datetime.fromtimestamp(saved_at_unix, tz=timezone.utc).isoformat()
            if saved_at_unix > 0
            else None,
            "age_seconds": max(age, 0),
            "ttl_seconds": max_age_seconds,
            "cache_key": cache_key,
        }
        return result


def _set_cached_scan_payload(cache_key: str, payload: Dict[str, Any]) -> None:
    with _CACHE_LOCK:
        store = _read_cache_store()
        entries = store.setdefault("entries", {})
        entries[cache_key] = {
            "saved_at_unix": int(time.time()),
            "payload": payload,
        }
        store["latest_key"] = cache_key
        _write_cache_store(store)


def _get_latest_cached_scan_payload() -> Optional[Dict[str, Any]]:
    with _CACHE_LOCK:
        store = _read_cache_store()
        latest_key = store.get("latest_key")
        if not latest_key:
            return None
        entry = (store.get("entries") or {}).get(latest_key)
        if not entry:
            return None
        saved_at_unix = int(entry.get("saved_at_unix") or 0)
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            return None
        result = dict(payload)
        result["cache"] = {
            "hit": True,
            "saved_at_unix": saved_at_unix,
            "saved_at_utc": datetime.fromtimestamp(saved_at_unix, tz=timezone.utc).isoformat()
            if saved_at_unix > 0
            else None,
            "age_seconds": max(int(time.time()) - saved_at_unix, 0),
            "cache_key": latest_key,
        }
        return result


def _build_scan_payload(req: ScanRequest) -> Dict[str, Any]:
    threshold_pct = float(req.threshold_percent)
    keep_limit = int(req.limit) if req.limit is not None else int(req.keep_limit)
    scan_limit = int(req.scan_limit)

    listings = _dedupe_cheapest(mm.fetch_market_data())
    selected = listings[:scan_limit]

    analyzed_items: List[Dict[str, Any]] = []
    for item in selected:
        analyzed = _analyze_listing(
            item,
            threshold_pct,
            include_full_records=req.include_full_records,
        )
        actionable = _wallet_actionable(
            analyzed=analyzed,
            min_profit_usd=req.min_profit_usd,
            wallet_budget_usd=req.wallet_budget_usd,
        )
        analyzed["actionable"] = actionable
        analyzed["action"] = "BUY_CANDIDATE" if actionable else "WATCH"
        analyzed_items.append(analyzed)

    if req.only_actionable:
        analyzed_items = [item for item in analyzed_items if item.get("actionable")]

    analyzed_items.sort(
        key=lambda item: (
            float(item.get("estimated_profit_usd") or -1e18),
            float(item.get("estimated_diff_pct") or -1e18),
        ),
        reverse=True,
    )
    kept_items = analyzed_items[:keep_limit]

    payload = {
        "time_utc": _utc_now_iso(),
        "reference_id": req.reference_id,
        "threshold_percent": threshold_pct,
        "min_profit_usd": req.min_profit_usd,
        "wallet_budget_usd": req.wallet_budget_usd,
        "scan_limit": scan_limit,
        "keep_limit": keep_limit,
        "total_scanned": len(selected),
        "total_after_filter": len(analyzed_items),
        "include_full_records": req.include_full_records,
        "count": len(kept_items),
        "opportunities": kept_items,
    }
    return payload


def _optional_float_env(name: str) -> Optional[float]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw)
    except Exception:
        return None


def _build_scan_request_from_env(
    prefix: str,
    include_full_records_default: str = "true",
    only_actionable_default: str = "true",
) -> ScanRequest:
    return ScanRequest(
        scan_limit=int(os.getenv(f"{prefix}_SCAN_LIMIT", "30")),
        keep_limit=int(os.getenv(f"{prefix}_KEEP_LIMIT", "10")),
        threshold_percent=float(
            os.getenv(f"{prefix}_THRESHOLD_PERCENT", os.getenv("PRICE_DIFF_PERCENT_THRESHOLD", "10"))
        ),
        min_profit_usd=float(os.getenv(f"{prefix}_MIN_PROFIT_USD", "0")),
        wallet_budget_usd=_optional_float_env(f"{prefix}_WALLET_BUDGET_USD"),
        include_full_records=_truthy_env(
            f"{prefix}_INCLUDE_FULL_RECORDS", include_full_records_default
        ),
        only_actionable=_truthy_env(
            f"{prefix}_ONLY_ACTIONABLE", only_actionable_default
        ),
        use_cache=False,
        force_refresh=True,
        cache_ttl_seconds=0,
    )


def _refresh_cache_with_request(req: ScanRequest, refresh_reason: str) -> Dict[str, Any]:
    keep_limit = int(req.limit) if req.limit is not None else int(req.keep_limit)
    scan_limit = int(req.scan_limit)
    threshold_pct = float(req.threshold_percent)
    cache_key = _scan_cache_key(
        scan_limit=scan_limit,
        keep_limit=keep_limit,
        threshold_percent=threshold_pct,
        min_profit_usd=req.min_profit_usd,
        wallet_budget_usd=req.wallet_budget_usd,
        include_full_records=req.include_full_records,
        only_actionable=req.only_actionable,
    )
    with _SCAN_LOCK:
        payload = _build_scan_payload(req)
        _set_cached_scan_payload(cache_key, payload)
    print(
        f"[market_api] cache refresh reason={refresh_reason} "
        f"count={payload.get('count')} scan_limit={scan_limit} keep_limit={keep_limit}"
    )
    return payload


def _warmup_cache_on_startup() -> None:
    try:
        req = _build_scan_request_from_env(
            prefix="OPPORTUNITY_WARMUP",
            include_full_records_default="true",
            only_actionable_default="true",
        )
        _refresh_cache_with_request(req, refresh_reason="startup_warmup")
    except Exception as exc:
        print(f"[market_api] warmup cache failed: {exc}")


def _auto_refresh_loop() -> None:
    interval = _AUTO_REFRESH_INTERVAL_SECONDS
    if interval < 1:
        interval = 1
    print(f"[market_api] auto refresh started interval={interval}s")
    while True:
        started = time.time()
        try:
            req = _build_scan_request_from_env(
                prefix="OPPORTUNITY_AUTO",
                include_full_records_default="true",
                only_actionable_default="true",
            )
            _refresh_cache_with_request(req, refresh_reason="auto_interval")
        except Exception as exc:
            print(f"[market_api] auto refresh failed: {exc}")
        elapsed = time.time() - started
        sleep_seconds = max(1.0, float(interval) - elapsed)
        time.sleep(sleep_seconds)


@app.on_event("startup")
def startup_event() -> None:
    warmup_enabled = _truthy_env("OPPORTUNITY_WARMUP_ON_STARTUP", "true")
    if _AUTO_REFRESH_ENABLED:
        threading.Thread(target=_auto_refresh_loop, daemon=True).start()
    elif warmup_enabled:
        threading.Thread(target=_warmup_cache_on_startup, daemon=True).start()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "time_utc": _utc_now_iso(),
        "default_threshold_percent": mm.PRICE_DIFF_PERCENT_THRESHOLD,
        "window_days": mm.WINDOW_DAYS,
        "cache_ttl_seconds": _CACHE_TTL_SECONDS,
        "auto_refresh_enabled": _AUTO_REFRESH_ENABLED,
        "auto_refresh_interval_seconds": _AUTO_REFRESH_INTERVAL_SECONDS if _AUTO_REFRESH_ENABLED else None,
    }


@app.get("/v1/listings/latest")
def list_latest(
    limit: int = 20,
    page: int = 1,
    pages: int = 1,
    step: int = 96,
    card_type: str = Query(default="Card", alias="cardType"),
    order_by: str = Query(default="listedDateDesc", alias="orderBy"),
    dedupe: bool = True,
    q: Optional[str] = None,
    min_ask: Optional[float] = Query(default=None, alias="minAsk"),
    max_ask: Optional[float] = Query(default=None, alias="maxAsk"),
) -> Dict[str, Any]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if pages < 1 or pages > 10:
        raise HTTPException(status_code=400, detail="pages must be between 1 and 10")
    if step < 1 or step > 200:
        raise HTTPException(status_code=400, detail="step must be between 1 and 200")
    if min_ask is not None and min_ask < 0:
        raise HTTPException(status_code=400, detail="min_ask must be >= 0")
    if max_ask is not None and max_ask < 0:
        raise HTTPException(status_code=400, detail="max_ask must be >= 0")
    if min_ask is not None and max_ask is not None and min_ask > max_ask:
        raise HTTPException(status_code=400, detail="min_ask cannot be greater than max_ask")

    listings: List[Dict[str, Any]] = []
    source_urls: List[str] = []
    for current_page in range(page, page + pages):
        fetched = mm.fetch_market_data(
            page=current_page,
            step=step,
            card_type=card_type,
            order_by=order_by,
        )
        listings.extend(fetched)
        source_urls.append(
            "https://www.renaiss.xyz/marketplace?"
            + urlencode(
                {
                    "page": current_page,
                    "step": step,
                    "cardType": card_type,
                    "orderBy": order_by,
                }
            )
        )

    before_dedupe_count = len(listings)
    if dedupe:
        listings = _dedupe_cheapest(listings)
    before_filter_count = len(listings)

    q_lower = (q or "").strip().lower()
    filtered: List[Dict[str, Any]] = []
    for item in listings:
        ask = float(item.get("ask_price") or 0.0)
        if q_lower and q_lower not in str(item.get("name") or "").lower():
            continue
        if min_ask is not None and ask < min_ask:
            continue
        if max_ask is not None and ask > max_ask:
            continue
        filtered.append(item)

    final_items = filtered[:limit]
    return {
        "time_utc": _utc_now_iso(),
        "count": len(final_items),
        "query": {
            "limit": limit,
            "page": page,
            "pages": pages,
            "step": step,
            "card_type": card_type,
            "order_by": order_by,
            "dedupe": dedupe,
            "q": q,
            "min_ask": min_ask,
            "max_ask": max_ask,
        },
        "stats": {
            "raw_total": before_dedupe_count,
            "after_dedupe": before_filter_count,
            "after_filter": len(filtered),
        },
        "source_urls": source_urls,
        "items": final_items,
    }


@app.post("/v1/analyze/item-id")
def analyze_by_item_id(req: AnalyzeByItemIdRequest) -> Dict[str, Any]:
    threshold_pct = float(req.threshold_percent)

    listings = _dedupe_cheapest(mm.fetch_market_data())
    matched = None
    for item in listings:
        if str(item.get("item_id")) == req.item_id:
            matched = item
            break
    if not matched:
        raise HTTPException(status_code=404, detail=f"item_id not found: {req.item_id}")

    analyzed = _analyze_listing(
        matched,
        threshold_pct,
        include_full_records=req.include_full_records,
    )
    analyzed["actionable"] = _wallet_actionable(
        analyzed=analyzed,
        min_profit_usd=req.min_profit_usd,
        wallet_budget_usd=req.wallet_budget_usd,
    )
    analyzed["action"] = "BUY_CANDIDATE" if analyzed["actionable"] else "WATCH"

    return {
        "time_utc": _utc_now_iso(),
        "threshold_percent": threshold_pct,
        "min_profit_usd": req.min_profit_usd,
        "wallet_budget_usd": req.wallet_budget_usd,
        "include_full_records": req.include_full_records,
        "result": analyzed,
    }


@app.post("/v1/opportunities/scan")
def scan_opportunities(req: ScanRequest) -> Dict[str, Any]:
    keep_limit = int(req.limit) if req.limit is not None else int(req.keep_limit)
    scan_limit = int(req.scan_limit)
    threshold_pct = float(req.threshold_percent)
    cache_key = _scan_cache_key(
        scan_limit=scan_limit,
        keep_limit=keep_limit,
        threshold_percent=threshold_pct,
        min_profit_usd=req.min_profit_usd,
        wallet_budget_usd=req.wallet_budget_usd,
        include_full_records=req.include_full_records,
        only_actionable=req.only_actionable,
    )
    ttl_seconds = _CACHE_TTL_SECONDS if req.cache_ttl_seconds is None else int(req.cache_ttl_seconds)

    if req.use_cache and not req.force_refresh:
        cached = _get_cached_scan_payload(cache_key=cache_key, max_age_seconds=ttl_seconds)
        if cached:
            cached["wallet_notify"] = {"sent": False, "reason": "served from cache"}
            return cached

    payload = _refresh_cache_with_request(req, refresh_reason="manual_scan")
    payload["cache"] = {
        "hit": False,
        "saved": True,
        "cache_key": cache_key,
        "ttl_seconds": ttl_seconds,
    }

    wallet_notify = {"sent": False, "reason": "notify_wallet is false"}
    if req.notify_wallet:
        wallet_notify = _post_wallet_signal(payload)
    payload["wallet_notify"] = wallet_notify
    return payload


@app.get("/v1/opportunities/latest")
def get_latest_opportunities_cache() -> Dict[str, Any]:
    cached = _get_latest_cached_scan_payload()
    if not cached:
        raise HTTPException(status_code=404, detail="no cached opportunities yet")
    cached["wallet_notify"] = {"sent": False, "reason": "cache snapshot endpoint"}
    return cached


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
