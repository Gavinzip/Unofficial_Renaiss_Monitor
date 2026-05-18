import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
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


def _analyze_listing(item: Dict[str, Any], threshold_pct: float) -> Dict[str, Any]:
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
    )
    pc_avg, pc_count, pc_url = pc_info
    snkr_avg, snkr_count, snkr_url = snkr_info

    pc_diff_pct = _safe_pct(pc_avg, ask)
    snkr_diff_pct = _safe_pct(snkr_avg, ask)

    meets_pc = pc_diff_pct is not None and pc_diff_pct >= threshold_pct
    meets_snkr = snkr_diff_pct is not None and snkr_diff_pct >= threshold_pct

    best = _pick_best_market(ask, pc_avg, snkr_avg)
    estimated_profit_usd = best["profit_usd"]

    return {
        "item_id": item_id,
        "name": full_name,
        "grade": item.get("grade"),
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
            },
            "snkrdunk": {
                "avg_price_usd": snkr_avg,
                "sample_count": snkr_count,
                "diff_pct": snkr_diff_pct,
                "url": snkr_url,
                "meets_threshold": meets_snkr,
            },
        },
        "best_market": best["market"],
        "estimated_profit_usd": estimated_profit_usd,
        "estimated_diff_pct": best["diff_pct"],
        "is_opportunity": bool(meets_pc or meets_snkr),
    }


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
    limit: int = Field(default=5, ge=1, le=30)
    threshold_percent: Optional[float] = None
    min_profit_usd: float = Field(default=0.0, ge=0.0)
    wallet_budget_usd: Optional[float] = Field(default=None, ge=0.0)
    only_actionable: bool = True
    notify_wallet: bool = False
    reference_id: Optional[str] = None


class AnalyzeByItemIdRequest(BaseModel):
    item_id: str = Field(min_length=1)
    threshold_percent: Optional[float] = None
    min_profit_usd: float = Field(default=0.0, ge=0.0)
    wallet_budget_usd: Optional[float] = Field(default=None, ge=0.0)


app = FastAPI(
    title="Renassis Market API",
    version="1.0.0",
    description="HTTP API for market opportunities, built for agent wallet integration.",
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "time_utc": _utc_now_iso(),
        "default_threshold_percent": mm.PRICE_DIFF_PERCENT_THRESHOLD,
        "window_days": mm.WINDOW_DAYS,
    }


@app.get("/v1/listings/latest")
def list_latest(limit: int = 20) -> Dict[str, Any]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    listings = _dedupe_cheapest(mm.fetch_market_data())
    return {
        "time_utc": _utc_now_iso(),
        "count": min(limit, len(listings)),
        "items": listings[:limit],
    }


@app.post("/v1/analyze/item-id")
def analyze_by_item_id(req: AnalyzeByItemIdRequest) -> Dict[str, Any]:
    threshold_pct = req.threshold_percent
    if threshold_pct is None:
        threshold_pct = mm.PRICE_DIFF_PERCENT_THRESHOLD

    listings = _dedupe_cheapest(mm.fetch_market_data())
    matched = None
    for item in listings:
        if str(item.get("item_id")) == req.item_id:
            matched = item
            break
    if not matched:
        raise HTTPException(status_code=404, detail=f"item_id not found: {req.item_id}")

    analyzed = _analyze_listing(matched, threshold_pct)
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
        "result": analyzed,
    }


@app.post("/v1/opportunities/scan")
def scan_opportunities(req: ScanRequest) -> Dict[str, Any]:
    threshold_pct = req.threshold_percent
    if threshold_pct is None:
        threshold_pct = mm.PRICE_DIFF_PERCENT_THRESHOLD

    listings = _dedupe_cheapest(mm.fetch_market_data())
    selected = listings[: req.limit]

    analyzed_items: List[Dict[str, Any]] = []
    for item in selected:
        analyzed = _analyze_listing(item, threshold_pct)
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

    payload = {
        "time_utc": _utc_now_iso(),
        "reference_id": req.reference_id,
        "threshold_percent": threshold_pct,
        "min_profit_usd": req.min_profit_usd,
        "wallet_budget_usd": req.wallet_budget_usd,
        "count": len(analyzed_items),
        "opportunities": analyzed_items,
    }

    wallet_notify = {"sent": False, "reason": "notify_wallet is false"}
    if req.notify_wallet:
        wallet_notify = _post_wallet_signal(payload)
    payload["wallet_notify"] = wallet_notify
    return payload


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
