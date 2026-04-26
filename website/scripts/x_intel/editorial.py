from __future__ import annotations

from . import bootstrap as _bootstrap

globals().update(vars(_bootstrap))

# Domain: SBT facts, universal digest, editorial/detail quality guards

def extract_sbt_threshold_facts(text: str) -> dict[str, Any]:
    src = clean_text(text)
    if not src:
        return {"tiers": [], "snapshot": "", "dynamic_hint": ""}

    tiers: list[str] = []
    seen_tiers: set[str] = set()
    for m in SBT_THRESHOLD_RE.finditer(src):
        percentile = str(m.group(1) or "").strip()
        points = str(m.group(2) or "").replace(",", "").strip()
        if not percentile or not points:
            continue
        line = f"前 {percentile}%：{points} 分"
        key = dedupe_key(line)
        if key and key in seen_tiers:
            continue
        if key:
            seen_tiers.add(key)
        tiers.append(line)
        if len(tiers) >= 4:
            break

    def _normalize_snapshot(raw: str) -> str:
        snap = clean_text(raw)
        if not snap:
            return ""
        snap = re.split(r"\b(?:keep\s+pushing|keep\s+climbing|join\s+us|thanks|see\s+you)\b", snap, maxsplit=1, flags=re.I)[0]
        tz_hit = re.search(r"(.+?\b(?:gmt|utc)\s*[+-]?\d{1,2}\)?)", snap, re.I)
        if tz_hit:
            snap = tz_hit.group(1)
        snap = snap.strip(" ，,;；。")
        return _clean_fact_value(snap, max_len=72)

    snapshot = ""
    snap_match = SBT_SNAPSHOT_RE.search(src)
    if snap_match:
        snapshot = _normalize_snapshot(snap_match.group(1))
    if not snapshot:
        schedule = extract_schedule_facts(src, limit=4)
        if schedule:
            snapshot = _normalize_snapshot("、".join(schedule[:3]))

    dynamic_hint = ""
    if re.search(r"live reference thresholds?|not fixed|keep climbing|bar can keep climbing|動態|浮動|非固定", src, re.I):
        dynamic_hint = "門檻為動態參考值，會隨參與人數與分數變化而上調。"

    return {"tiers": tiers, "snapshot": snapshot, "dynamic_hint": dynamic_hint}


def has_sbt_signal(text: str) -> bool:
    src = clean_text(text)
    if not src:
        return False
    return bool(
        re.search(
            r"\bsbt\b|soulbound|積分|积分|points?|snapshot|快照|threshold|門檻|top\s*\d+%|rank(?:ing)?",
            src,
            re.I,
        )
    )


def infer_sbt_acquisition_line(source: str, facts: dict[str, str] | None = None) -> str:
    src = clean_text(source)
    if not has_sbt_signal(src):
        return ""

    threshold = extract_sbt_threshold_facts(src)
    tiers = [clean_text(str(x)) for x in threshold.get("tiers", []) if clean_text(str(x))]
    snapshot = _clean_fact_value(str(threshold.get("snapshot") or ""), max_len=72)
    if tiers:
        tier_text = "、".join(tiers[:3])
        line = f"SBT 取得方式：快照時達到 {tier_text}"
        if snapshot:
            line += f"，快照時間 {snapshot}"
        return clean_text(line)

    pull_once = re.search(
        r"pull\s+([a-z0-9 +\-]{3,36})\s+once\s+before\s+([a-z0-9 ,:+\-]{2,28})\s+to\s+unlock",
        src,
        re.I,
    )
    if pull_once:
        pack = _clean_fact_value(pull_once.group(1), max_len=26)
        date_hint = _clean_fact_value(pull_once.group(2), max_len=24)
        return f"SBT 取得方式：在 {date_hint} 前完成 1 次「{pack}」抽卡以解鎖。"

    join_claim = re.search(
        r"(?:join|attend|participate|參加|参与|完成)\s+([^\n。；;]{4,42})\s*(?:to|即可|後|后).{0,18}(?:get|claim|receive|領取|领取|取得|獲得).{0,10}(?:sbt|soulbound)",
        src,
        re.I,
    )
    if join_claim:
        task = _clean_fact_value(join_claim.group(1), max_len=44)
        return f"SBT 取得方式：完成「{task}」後依規則領取。"

    lines = split_sentences(src)
    candidate = ""
    patt = re.compile(
        r"(pull|open|mint|claim|join|attend|share|hold|buy|參加|参与|完成|報名|报名|快照|排名).{0,56}(sbt|soulbound|認證|认证)|"
        r"(sbt|soulbound).{0,56}(unlock|claim|get|receive|領取|领取|取得|獲得|解鎖|解锁|發放|发放)",
        re.I,
    )
    for row in lines:
        if patt.search(row):
            candidate = _clean_fact_value(row, max_len=96)
            break
    if candidate:
        candidate = re.sub(
            r"(?i)^.*?(?=(pull|open|mint|claim|join|attend|share|hold|buy|參加|参与|完成|報名|报名|快照|排名|sbt|soulbound))",
            "",
            candidate,
        ).strip(" ，,;；。")
        return f"SBT 取得方式：{candidate}"

    facts_map = normalize_event_facts(facts or {})
    reward = clean_text(str(facts_map.get("reward") or ""))
    participation = clean_text(str(facts_map.get("participation") or ""))
    if re.search(r"\bsbt\b|soulbound", reward, re.I):
        if participation:
            return f"SBT 取得方式：完成「{participation}」並符合活動條件後領取。"
        return "SBT 取得方式：依官方貼文的參與條件完成任務後領取。"
    return "SBT 取得方式：依官方公布的快照、排名或任務條件取得。"


def infer_topic_phrase(text: str, card_type: str) -> str:
    t = strip_links_mentions(clean_text(text))
    keyword_topics = [
        (r"\bmfa\b|2fa|multi[-\s]*factor|authenticator|authentication|帳號安全|账号安全|setting page|設定頁|设置页", "帳號安全與 MFA"),
        (r"threshold update|thresholds?|snapshot|top\s*\d{1,3}\s*%|分位門檻|門檻更新", "SBT 快照門檻更新"),
        (r"web3\s*festival|hong\s*kong", "香港 Web3 Festival 行程"),
        (r"korea|community\s*gathering|gathering|meetup", "社群線下聚會"),
        (r"\bplaza\b|space|community\s*session|ama|discord|直播", "社群直播與互動"),
        (r"\btour\b|card\s*shop", "卡店巡迴與交流活動"),
        (r"ambassador|大使", "Ambassador 計畫進度"),
        (r"sbt|points|積分", "SBT 與積分機制"),
        (r"one\s*piece|luffy", "One Piece 卡牌動向"),
        (r"volume|成交|交易量|\$\d", "交易量與市場成長"),
        (r"pack|卡包|抽卡", "卡包與抽卡表現"),
        (r"reward|airdrop|獎勵", "獎勵與發放進度"),
        (r"update|公告|progress", "最新官方更新"),
    ]
    for pat, label in keyword_topics:
        if re.search(pat, t, re.I):
            return label
    t = re.sub(r"^[^\w\u4e00-\u9fff]+", "", t)
    t = re.sub(
        r"\b(we|we're|we are|join us|welcome|excited|progress|update|community|project|results?|announcement)\b",
        " ",
        t,
        flags=re.I,
    )
    t = re.sub(r"\s+", " ", t).strip(" ,.:;|-")
    if not t:
        return _headline_prefix(card_type)
    if _is_mostly_ascii(t):
        fallback = {
            "event": "社群活動更新",
            "market": "市場訊號更新",
            "announcement": "官方公告更新",
            "feature": "功能進度更新",
            "report": "分析整理更新",
            "insight": "社群互動更新",
        }
        return fallback.get(card_type, _headline_prefix(card_type))
    return compact_point(t, 46)


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(text or "")))


def _is_mostly_ascii(text: str) -> bool:
    src = str(text or "")
    ascii_count = len(re.findall(r"[A-Za-z0-9]", src))
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", src))
    if ascii_count < 12:
        return False
    return ascii_count >= max(18, cjk_count * 3)


def _abstract_focus_line(text: str, max_len: int = 84) -> str:
    src = strip_links_mentions(clean_text(text))
    if not src:
        return ""
    src = re.sub(r"^\d+\s*[/、.)\]]\s*", "", src)
    src = re.sub(
        r"(?i)\b("
        r"live from|join us|we(?:'re| are)? excited(?: to)?|looking ahead|"
        r"reminder|tonight(?:'s)?|we would like to|come find us(?: and let'?s)?|"
        r"thanks for|we're thrilled|we are thrilled"
        r")\b",
        " ",
        src,
    )
    src = re.sub(r"\s+", " ", src).strip(" ,.;:!?-")
    if not src:
        return ""

    clauses = re.split(r"[，,。；;:：|｜]", src)
    chosen: list[str] = []
    for clause in clauses:
        c = clean_text(clause)
        if not c:
            continue
        if len(strip_links_mentions(c)) < 6:
            continue
        if len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", c)) < 4:
            continue
        if c in chosen:
            continue
        chosen.append(c)
        if len(chosen) >= 2:
            break
    if not chosen:
        chosen = [src]
    return compact_point("；".join(chosen), max_len=max_len)


def _account_actor_label(account: str) -> str:
    handle = str(account or "").strip().lstrip("@").lower()
    if not handle:
        return "來源帳號"
    if handle.startswith("renaiss"):
        return "Renaiss 官方"
    return f"@{handle}"


def _infer_why_line(source: str, card_type: str) -> str:
    src = clean_text(source).lower()
    if card_type == "event":
        if re.search(r"sbt|reward|獎勵|积分|積分|merch|周邊|周边", src, re.I):
            return "這類活動有明確誘因，通常會提高參與率與社群擴散。"
        if re.search(r"join us|community|gathering|ama|session|discord|live|直播", src, re.I):
            return "這是社群動員型資訊，重點是把人導向直播或現場互動。"
        return "這則主要用來通知參與資訊，關鍵在時間、地點與參加方式。"
    if card_type in {"feature", "announcement"}:
        if re.search(r"\bmfa\b|2fa|multi[-\s]*factor|authenticator|authentication|security|帳號安全|账号安全|setting page|設定頁|设置页", src, re.I):
            return "這會直接改變登入流程並提升帳號安全門檻。"
        if re.search(r"(sbt|points?).{0,36}(threshold|top\s*\d+%|snapshot)|threshold update", src, re.I):
            return "這會直接影響 Beta 參與者在快照前的衝分策略與 SBT 等級判定。"
        if re.search(r"launch|release|coming|roadmap|progress|開放|上線|上线|更新", src, re.I):
            return "這代表產品進度往下一個節點前進，需留意正式開放時間與條件。"
        return "這則更新會影響後續使用流程，需追蹤官方下一則細節。"
    if card_type == "market":
        if re.search(r"record|成交|sold|price|交易量|volume|涨|漲|跌", src, re.I):
            return "這會把討論焦點集中在成交價、供需與估值區間。"
        return "這則訊息反映市場觀察點，適合與其他來源一起比對。"
    if card_type == "report":
        return "這份整理可直接拿來比較方案差異與執行成本。"
    return "這則貼文提供社群現場脈絡，可用來補齊討論背景。"


def build_fivew_brief(
    source: str,
    card_type: str,
    account: str,
    topic: str,
    lead_focus: str,
    event_facts: dict[str, str],
    schedule: list[str],
) -> dict[str, str]:
    who = _account_actor_label(account)
    what = _clean_fact_value(lead_focus or topic, max_len=96)
    when = _clean_fact_value(str(event_facts.get("schedule") or ""), max_len=56)
    where = _clean_fact_value(str(event_facts.get("location") or ""), max_len=56)
    if not when and schedule:
        schedule_joined = _clean_fact_value("、".join(schedule[:2]), max_len=56)
        if card_type in {"event", "feature", "announcement"}:
            when = schedule_joined
        elif card_type == "insight" and _contains_calendar_date(schedule_joined):
            when = schedule_joined
    if not where and card_type in {"event", "insight"}:
        if re.search(r"hong\s*kong|香港", source, re.I):
            where = "香港"
        elif re.search(r"discord|space|live|直播|線上|线上", source, re.I):
            where = "線上社群"
    why = _infer_why_line(source, card_type)
    return {
        "who": who,
        "what": what,
        "when": when,
        "where": where,
        "why": why,
    }


def build_universal_digest_frame(
    source: str,
    card_type: str,
    account: str,
    topic: str,
    lead_focus: str,
    fivew: dict[str, str],
    schedule: list[str],
    numbers: list[str],
    event_facts: dict[str, str] | None = None,
    report_digest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    who = str(fivew.get("who") or _account_actor_label(account)).strip() or _account_actor_label(account)
    what = _clean_fact_value(str(fivew.get("what") or lead_focus or topic), max_len=96) or _clean_fact_value(topic, max_len=96)
    when = _clean_fact_value(str(fivew.get("when") or ""), max_len=72)
    where = _clean_fact_value(str(fivew.get("where") or ""), max_len=72)
    why = _clean_fact_value(str(fivew.get("why") or _infer_why_line(source, card_type)), max_len=110)
    facts = normalize_event_facts(event_facts or {})
    if not facts and has_sbt_signal(source):
        facts = build_event_facts(source)
    sbt_how = infer_sbt_acquisition_line(source, facts=facts)
    digest = report_digest if isinstance(report_digest, dict) else {}

    if not when and schedule:
        when = _clean_fact_value("、".join(schedule[:2]), max_len=72)

    def _finish(summary: str, bullets: list[str], detail_summary: str, detail_lines: list[str]) -> dict[str, Any]:
        summary_clean = clean_text(summary)[:320]
        detail_summary_clean = clean_text(detail_summary)[:420]
        bullet_rows = [clean_text(str(x))[:120] for x in bullets if clean_text(str(x))][:3]
        if len(bullet_rows) < 3:
            for pad in detail_lines:
                if len(bullet_rows) >= 3:
                    break
                p = clean_text(str(pad))[:120]
                if not p:
                    continue
                if p in bullet_rows:
                    continue
                bullet_rows.append(p)
        detail_rows = normalize_detail_lines(detail_lines, limit=6)
        return {
            "summary": summary_clean,
            "bullets": bullet_rows[:3],
            "detail_summary": detail_summary_clean,
            "detail_lines": detail_rows[:6],
        }

    def _append_sentence(base: str, piece: str) -> str:
        head = clean_text(base)
        tail = clean_text(piece)
        if not tail:
            return head
        if head and not re.search(r"[。！？!?]$", head):
            head += "。"
        if tail and not re.search(r"[。！？!?]$", tail):
            tail += "。"
        return f"{head}{tail}"

    if card_type == "event":
        reward = _clean_fact_value(str(facts.get("reward") or ""), max_len=72)
        participation = _clean_fact_value(str(facts.get("participation") or ""), max_len=72)
        summary = f"{who}釋出「{topic}」活動資訊。"
        if when:
            summary += f"時間為 {when}。"
        if where:
            summary += f"地點在 {where}。"
        if reward:
            summary += f"主要誘因是 {reward}。"
        if sbt_how and re.search(r"\bsbt\b|soulbound", clean_text(reward), re.I):
            summary = _append_sentence(summary, sbt_how)
        summary = _append_sentence(summary, why)
        bullets = [
            f"活動重點：{what}",
            f"時間與地點：{when}{('／' + where) if where else ''}" if when or where else "時間與地點：請以原文公告為準",
            f"參與方式：{participation}" if participation else "參與方式：先看原文確認報名與參與門檻",
        ]
        if sbt_how:
            bullets = [f"SBT 取得方式：{sbt_how.replace('SBT 取得方式：', '').strip()}"] + bullets[:2]
        detail_summary = (
            f"{who} 這則活動主軸是「{what}」，"
            f"{('時間在 ' + when + '，') if when else ''}"
            f"{('地點在 ' + where + '，') if where else ''}"
            f"{('主要誘因是 ' + reward + '，') if reward else ''}"
            f"{('參與方式為 ' + participation + '。') if participation else '參與方式請以原文公告為準。'}"
            f"{why}"
        )
        detail_lines = [
            f"活動主軸：{what}",
            f"時間與地點：{when}{('／' + where) if where else ''}" if when or where else "時間與地點：待官方補充",
            f"獎勵重點：{reward}" if reward else "獎勵重點：請以原文獎勵說明為準",
            f"參與方式：{participation}" if participation else "參與方式：先確認報名方式、截止時間與名額。",
            f"影響：{why}",
        ]
        if sbt_how:
            detail_lines.insert(3, sbt_how)
        return _finish(summary, bullets, detail_summary, detail_lines)

    if card_type in {"feature", "announcement"}:
        threshold_facts = extract_sbt_threshold_facts(source)
        tiers = [str(x) for x in threshold_facts.get("tiers", []) if str(x).strip()]
        snapshot = _clean_fact_value(str(threshold_facts.get("snapshot") or ""), max_len=72)
        dynamic_hint = _clean_fact_value(str(threshold_facts.get("dynamic_hint") or ""), max_len=90)
        is_threshold_update = bool(
            tiers and re.search(r"(sbt|points?).{0,36}(threshold|top\s*\d+%|snapshot)|threshold update", source, re.I)
        )
        security_update = bool(
            re.search(
                r"\bmfa\b|2fa|multi[-\s]*factor|authenticator|authentication|security|帳號安全|账号安全|setting page|設定頁|设置页",
                source,
                re.I,
            )
        )
        if is_threshold_update:
            tier_text = "、".join(tiers[:3])
            summary = f"{who}更新了「{topic}」功能規則。門檻分數為 {tier_text}。"
            if snapshot:
                summary += f"快照時間：{snapshot}。"
            summary = _append_sentence(summary, dynamic_hint or "門檻屬動態參考值，會隨參與人數與分數分布調整")
            summary = _append_sentence(summary, why)
            detail_summary = f"{who} 這則是 SBT 門檻更新：{tier_text}。"
            if snapshot:
                detail_summary += f"快照時間為 {snapshot}。"
            detail_summary = _append_sentence(detail_summary, dynamic_hint or "分位門檻是動態參考值，會隨分數分布上修")
            detail_summary = _append_sentence(detail_summary, "重點是快照前的衝分策略與快照後的最終分位確認")
            bullets = [
                f"門檻分數：{tier_text}",
                f"快照時間：{snapshot}" if snapshot else "快照時間：請以官方公告時間為準",
                "你要做什麼：快照前持續拉分，快照後核對最終門檻與 SBT 等級。",
            ]
            if sbt_how:
                bullets[2] = sbt_how
            detail_lines = [
                f"更新主軸：{what}",
                f"本次門檻：{tier_text}",
                f"快照時間：{snapshot or '待官方補充'}",
                f"規則說明：{dynamic_hint or '門檻為參考值，會隨分布變動。'}",
                "影響對象：Beta 參與者（依分位對應等級）。",
                "下一步：快照前提升分數，快照後回看官方最終分位公告。",
            ]
            if sbt_how:
                detail_lines.insert(4, sbt_how)
            return _finish(summary, bullets, detail_summary, detail_lines)

        if security_update:
            summary = f"{who}發布「{topic}」功能更新。MFA 已可啟用，登入需驗證器動態碼。{why}"
            if sbt_how:
                summary = _append_sentence(summary, sbt_how)
            detail_summary = (
                f"{who} 這則更新重點是 MFA 登入保護。"
                "啟用後會在登入流程增加驗證器動態碼步驟，"
                "可降低帳號被盜風險，但使用流程會多一次驗證。"
            )
            bullets = [
                "更新重點：MFA（二階段驗證）已上線",
                "影響流程：登入需輸入驗證器 6 位數動態碼",
                "你要做什麼：到設定頁啟用 MFA，並準備備援登入方式",
            ]
            if sbt_how:
                bullets[2] = sbt_how
            detail_lines = [
                "更新主軸：帳號安全驗證升級",
                "機制重點：新增驗證器動態碼步驟",
                "適用對象：目前使用 Privy 登入的使用者",
                "影響：安全性提升，但登入流程增加一次驗證",
                "下一步：完成 MFA 設定並測試備援流程",
            ]
            if sbt_how:
                detail_lines.insert(3, sbt_how)
            return _finish(summary, bullets, detail_summary, detail_lines)

        summary = f"{who}發布「{topic}」{('官方公告' if card_type == 'announcement' else '功能更新')}。"
        summary += f"重點是 {what}。"
        if when:
            summary += f"時間節點：{when}。"
        summary += why
        detail_summary = (
            f"{who} 這則屬於{('官方公告' if card_type == 'announcement' else '功能更新')}，"
            f"核心為「{what}」。"
            f"{('主要時間節點在 ' + when + '。') if when else ''}"
            f"對使用者的直接影響是：{why}"
        )
        bullets = [
            f"更新重點：{what}",
            f"時間節點：{when}" if when else "時間節點：待官方公告",
            "你要做什麼：先確認生效時間與開放條件，再安排操作。",
        ]
        if sbt_how:
            bullets[2] = sbt_how
        detail_lines = [
            f"更新主軸：{what}",
            f"時間節點：{when or '待官方公告'}",
            f"影響：{why}",
            "下一步：追蹤官方下一則公告確認最終規則。",
        ]
        if sbt_how:
            detail_lines.insert(2, sbt_how)
        return _finish(summary, bullets, detail_summary, detail_lines)

    if card_type == "market":
        meanings = _market_number_meanings(source, numbers)
        meaning_line = "；".join([clean_text(x).rstrip("。；; ") for x in meanings[:2]]) if meanings else ""
        if not meaning_line and numbers:
            pretty = [_number_with_unit(x, _find_number_context(source, x)) for x in numbers[:2]]
            meaning_line = f"文中提到 { '、'.join(pretty) }。"
        summary = f"{who}發布「{topic}」市場訊號。重點是 {what}。"
        if meaning_line:
            summary += f"數字意義：{meaning_line}。"
        if sbt_how:
            summary = _append_sentence(summary, sbt_how)
        summary = _append_sentence(summary, _market_impact_line(source))
        detail_summary = f"{who} 這則市場更新主軸是「{what}」。"
        if meaning_line:
            detail_summary = _append_sentence(detail_summary, f"貼文數字代表：{meaning_line}")
        else:
            detail_summary = _append_sentence(detail_summary, "此則以市場風向觀測為主")
        detail_summary = _append_sentence(detail_summary, f"影響面：{_market_impact_line(source)}")
        bullets = [
            f"市場重點：{what}",
            f"數字解讀：{meanings[0]}" if meanings else (f"數字脈絡：{_number_with_unit(numbers[0], _find_number_context(source, numbers[0]))}" if numbers else "數字脈絡：此貼文以市場觀察為主"),
            f"可能影響：{_market_impact_line(source)}",
        ]
        if sbt_how:
            bullets = [sbt_how, bullets[0], bullets[2]]
        detail_lines = [
            f"市場主軸：{what}",
            f"數字解讀：{meanings[0]}" if meanings else "數字解讀：請搭配原文上下文理解數字用途。",
            f"補充：{meanings[1]}" if len(meanings) > 1 else "補充：留意是否有後續供給、價格或成交更新。",
            f"影響：{_market_impact_line(source)}",
            "下一步：比對至少兩個來源後再做判斷。",
        ]
        if sbt_how:
            detail_lines.insert(3, sbt_how)
        return _finish(summary, bullets, detail_summary, detail_lines)

    if card_type == "report":
        digest_summary = clean_text(str(digest.get("summary") or ""))
        digest_bullets = [clean_text(str(x))[:120] for x in (digest.get("bullets") or []) if clean_text(str(x))][:3]
        summary = digest_summary or f"{who}整理了「{topic}」攻略重點。重點是 {what}。{why}"
        detail_summary = summary
        if digest_summary:
            detail_summary = f"{digest_summary} 可直接拿來做方案比較與執行規劃。"
        bullets = digest_bullets or [
            f"整理主軸：{what}",
            f"時間參考：{when}" if when else "時間參考：近期整理內容",
            "使用方式：先對照需求與成本，再選方案。",
        ]
        detail_lines = digest_bullets[:]
        if not detail_lines:
            detail_lines = [
                f"重點主題：{what}",
                f"補充：{why}",
                "下一步：依預算與時程篩選可執行方案。",
            ]
        return _finish(summary, bullets, detail_summary, detail_lines)

    summary = f"{who}分享了「{topic}」社群近況，重點是 {what}。"
    if when:
        summary += f"時間參考：{when}。"
    if where:
        summary += f"場景：{where}。"
    summary = _append_sentence(summary, why)
    if sbt_how:
        summary = _append_sentence(summary, sbt_how)
    detail_summary = (
        f"{who} 這則社群內容的核心是「{what}」。"
        f"{('時間參考為 ' + when + '。') if when else ''}"
        f"{('主要場景在 ' + where + '。') if where else ''}"
        f"判讀建議：{why}"
    )
    bullets = [
        f"貼文重點：{what}",
        f"時間/場景：{when}{('／' + where) if where else ''}" if when or where else "時間/場景：原文未提供明確時間地點",
        "下一步：看原文與同帳號續篇，確認是否有規則或活動補充。",
    ]
    if sbt_how:
        bullets = [sbt_how, bullets[0], bullets[1]]
    detail_lines = [
        f"社群主軸：{what}",
        f"時間參考：{when}" if when else "時間參考：以原文更新為準",
        f"場景：{where}" if where else "場景：線上社群討論",
        f"影響：{why}",
        "下一步：持續追蹤官方或同帳號後續補充。",
    ]
    if sbt_how:
        detail_lines.insert(3, sbt_how)
    return _finish(summary, bullets, detail_summary, detail_lines)


def _english_focus_hint(text: str, card_type: str, topic: str) -> str:
    src = strip_links_mentions(clean_text(text)).lower()
    hints = [
        (r"(?:sbt|points?).{0,36}(?:threshold|top\s*\d+%|snapshot)|threshold update", "SBT 分位門檻與快照時間更新"),
        (r"\bmfa\b|multi[-\s]*factor|authenticator|setting page|secure your account", "MFA 帳號安全驗證已上線"),
        (r"first card shop.*hong kong tcg tour|hong kong tcg tour.*first card shop", "香港 TCG Tour 首站卡店現場更新"),
        (r"community gathering.*korea|korea.*community gathering", "韓國社群聚會活動公告"),
        (r"rip packs together|take photos|chat about tcg", "現場一起開包、拍照並交流卡市觀點"),
        (r"line(?:d|s)? up for packs|reacting to pulls|collecting stories", "玩家現場交流抽卡成果，社群互動熱度提升"),
        (r"entertainment rwa night|kicking off", "Entertainment RWA Night 現場活動進行中"),
        (r"record breaker|sold for", "高價成交案例釋出"),
        (r"pokemon[^$]*\$857\s*million|\$857\s*million[^$]*pokemon", "官方引用研究指出寶可夢單一市場營收達 8.57 億美元"),
        (r"market size[^$]*\$11\.8\s*billion|\$11\.8\s*billion[^$]*market size", "研究預估全球 TCG 市場規模可達 118 億美元"),
        (r"beta\s*2\.0.*ending|points will be reset", "Beta 2.0 即將結束，積分將重置"),
        (r"one piece.*infinite gacha|moving deeper into one piece", "One Piece Infinite Gacha 進度更新"),
        (r"legacy pack", "Legacy Pack 卡包上新與價格區間更新"),
        (r"ama|community session|plaza", "社群直播與互動預告"),
        (r"web3 festival", "Web3 Festival 社群行程更新"),
    ]
    for pat, label in hints:
        if re.search(pat, src, re.I):
            return _clean_fact_value(label, max_len=84)
    if card_type == "market":
        return _clean_fact_value(f"{topic}（英文原文）", max_len=84)
    if card_type in {"feature", "announcement"}:
        return _clean_fact_value("功能規則已更新，請依貼文列出的時間與條件操作", max_len=84)
    if card_type == "event":
        return _clean_fact_value("活動資訊已釋出，請先確認時間地點", max_len=84)
    if card_type == "insight":
        return _clean_fact_value("社群互動更新", max_len=84)
    return _clean_fact_value(topic, max_len=84)


def _find_number_context(source: str, token: str) -> str:
    src = clean_text(source)
    low = src.lower()
    token_l = str(token or "").lower()
    idx = low.find(token_l)
    if idx < 0 and token_l.startswith("$"):
        idx = low.find(token_l[1:])
    if idx < 0:
        return src[:140]
    return src[max(0, idx - 70): min(len(src), idx + 100)]


def _expand_dollar_suffix(raw: str) -> str:
    compact = clean_text(raw).replace(",", "").replace(" ", "")
    m = re.fullmatch(r"\$?(\d+(?:\.\d+)?)([kmb])", compact, re.I)
    if not m:
        return ""
    try:
        base = float(m.group(1))
    except Exception:
        return ""
    suffix = m.group(2).lower()
    multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}.get(suffix)
    if not multiplier:
        return ""
    value = base * multiplier
    if abs(value - round(value)) < 0.001:
        value_text = f"{int(round(value)):,}"
    else:
        value_text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{raw}（約 {value_text} 美元）"


def _expand_dollar_by_context(raw: str, context: str) -> str:
    token = clean_text(raw)
    if not token or not token.startswith("$"):
        return ""
    m = re.match(r"^\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)$", token)
    if not m:
        return ""
    try:
        base = float(m.group(1).replace(",", ""))
    except Exception:
        return ""

    ctx = clean_text(context)
    num_raw = m.group(1)
    num_alt = num_raw.replace(",", "")
    num_pat = f"(?:{re.escape(num_raw)}|{re.escape(num_alt)})"

    scale_hit = re.search(
        rf"\$?\s*{num_pat}\s*(billion|bn|million|mn|thousand|十億|十亿|百萬|百万|千)(?:\b)?",
        ctx,
        re.I,
    )
    if not scale_hit:
        scale_hit = re.search(
            rf"(billion|bn|million|mn|thousand|十億|十亿|百萬|百万|千)\s*\$?\s*{num_pat}(?:\b)?",
            ctx,
            re.I,
        )

    if not scale_hit:
        return ""

    scale_word = str(scale_hit.group(1) or "").lower()
    multiplier = 0.0
    label = ""
    if scale_word in {"billion", "bn", "十億", "十亿"}:
        multiplier = 1_000_000_000.0
        label = "billion"
    elif scale_word in {"million", "mn", "百萬", "百万"}:
        multiplier = 1_000_000.0
        label = "million"
    elif scale_word in {"thousand", "千"}:
        multiplier = 1_000.0
        label = "thousand"

    if not multiplier:
        return ""

    value = base * multiplier
    if abs(value - round(value)) < 0.001:
        value_text = f"{int(round(value)):,}"
    else:
        value_text = f"{value:,.2f}".rstrip("0").rstrip(".")

    return f"{token} {label}（約 {value_text} 美元）"


def _number_with_unit(token: str, context: str) -> str:
    raw = clean_text(token)
    if not raw:
        return raw
    ctx = clean_text(context).lower()
    plain = re.sub(r"[^0-9.]", "", raw)
    if "%" in raw:
        return raw
    if raw.startswith("$"):
        expanded = _expand_dollar_suffix(raw)
        if expanded:
            return expanded
        contextual = _expand_dollar_by_context(raw, ctx)
        if contextual:
            return contextual
        return f"{raw}（美元）"
    if re.search(r"(legacy\s*pack|pack\s*\d+\.\d+|版本|version|series)", ctx, re.I) and re.fullmatch(r"\d+(?:\.\d+)?", plain):
        return f"{raw}（版本）"
    if re.fullmatch(r"(19|20)\d{2}", plain) and re.search(r"年|year|timeline|roadmap|forecast|預估", ctx, re.I):
        return f"{raw}（年份）"
    if re.search(r"serialized|限量|編號|编号|/\s*\d+", ctx, re.I) and re.fullmatch(r"\d+(?:\.\d+)?", plain):
        return f"{raw}（序號）"
    if re.search(r"\bntd\b|台幣|新台幣", ctx, re.I):
        return f"{raw}（NTD）"
    if re.search(r"\busdt\b", ctx, re.I):
        return f"{raw}（USDT）"
    if re.search(r"\busd\b|美元", ctx, re.I):
        return f"{raw}（美元）"
    if re.search(r"\bpoints?\b|積分|分位|threshold|門檻", ctx, re.I):
        return f"{raw}（積分）"
    if re.search(r"physical cards|cards?|張卡|卡片總量|發行總量", ctx, re.I):
        if re.search(r"\bbillion\b|十億|亿", ctx, re.I):
            return f"{raw}（十億張卡）"
        if re.search(r"\bmillion\b|百萬", ctx, re.I):
            return f"{raw}（百萬張卡）"
        return f"{raw}（張卡）"
    if re.search(r"per\s*(pack|pull)|每包|每抽|單包", ctx, re.I):
        return f"{raw}（每抽/每包）"
    return raw


def _market_number_meanings(source: str, numbers: list[str]) -> list[str]:
    src = clean_text(source)
    low = src.lower()
    out: list[str] = []
    seen: set[str] = set()
    for n in numbers[:4]:
        token = str(n)
        display_n = _number_with_unit(token, _find_number_context(src, token))
        token_l = token.lower()
        is_money = "$" in token_l
        idx = low.find(token_l)
        if idx < 0 and token_l.startswith("$"):
            idx = low.find(token_l[1:])
        context = src[max(0, idx - 64): min(len(src), idx + 96)] if idx >= 0 else src[:120]
        line = ""
        plain_num = re.sub(r"[^0-9.]", "", token_l)
        if re.search(r"(legacy\s*pack|pack\s*\d+\.\d+|版本|version|series)", context, re.I) and re.fullmatch(r"\d+\.\d+", plain_num):
            line = f"{display_n} 在這裡是版本編號，不是價格。"
        elif not is_money and re.search(r"serialized|限量|編號|编号|/\s*\d+", context, re.I):
            line = f"{display_n} 代表限量編號或稀有度門檻。"
        elif (not is_money) and re.search(r"produced|累計|累计|cumulatively|physical cards|卡片總量|發行總量", context, re.I):
            line = f"{display_n} 代表已發行實體卡數量規模。"
        elif re.search(r"revenue|營收|收入|generated", context, re.I):
            line = f"{display_n} 在這則貼文裡代表營收規模。"
        elif re.search(r"flipping|flip|profit|收益|利潤|赚", context, re.I):
            line = f"{display_n} 代表單筆交易收益或利潤規模。"
        elif re.search(r"market size|市場規模|forecast|預估|by\s*2030|2030", context, re.I):
            line = f"{display_n} 代表市場規模的預估值。"
        elif re.search(r"sold|sale|成交|售出|拍出|record|acquired|deal|交易", context, re.I):
            line = f"{display_n} 代表成交金額或價格里程碑。"
        elif re.search(r"per\s*(pack|pull)|每包|每抽|單包|售價|price|top value|最高價值", context, re.I):
            line = f"{display_n} 代表產品售價或價值區間。"
        elif re.fullmatch(r"\d+(?:\.\d+)?", str(n)) and re.search(r"pack|版本|series|legacy|卡包", low, re.I):
            line = f"{display_n} 多半是版本或批次編號。"
        else:
            line = f"{display_n} 是貼文提到的市場參考數據。"
        key = dedupe_key(line)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(line)
        if len(out) >= 3:
            break
    return out


def _market_impact_line(source: str) -> str:
    src = clean_text(source)
    if re.search(r"one piece|black label|champion prize|high-end move|top collectors", src, re.I):
        return "這會強化高端收藏市場信心，並提高 One Piece 相關標的的關注度。"
    if re.search(r"market size|forecast|預估|成長|growth", src, re.I):
        return "這則內容會提高社群對市場成長議題的關注度。"
    if re.search(r"sold|成交|拍出|record", src, re.I):
        return "這則內容會把討論焦點拉到高價成交與估值區間。"
    if re.search(r"pack|卡包|launch|上新|release", src, re.I):
        return "這則內容直接影響玩家對入場時機與開包策略的判斷。"
    return "這則內容反映當前市場討論方向，建議搭配原文脈絡判讀。"


def _market_is_number_dump(summary: str, bullets: list[str]) -> bool:
    text = clean_text(" ".join([summary] + bullets))
    if not text:
        return True
    has_number = bool(re.search(r"\$?\d[\d,]*(?:\.\d+)?%?", text))
    has_meaning = bool(
        re.search(
            r"代表|意指|用來|售價|成交|營收|市場規模|版本|單位|區間|預估|預測|影響|帶動|反映|說明",
            text,
            re.I,
        )
    )
    has_template = bool(re.search(r"(提到的數據包含|數據[:：])", text))
    return has_number and (not has_meaning or has_template)


def build_editorial_copy(text: str, card_type: str, account: str) -> dict[str, Any]:
    source = clean_text(text)
    lines = pick_signal_lines(source, limit=5)
    lead = lines[0] if lines else source
    second_line = lines[1] if len(lines) > 1 else ""
    schedule = extract_schedule_facts(source, limit=3)
    numbers = extract_numeric_facts(source, limit=3)
    event_facts = build_event_facts(source) if card_type == "event" else {}
    report_digest = build_report_digest(source) if card_type == "report" else {}
    prefix = _headline_prefix(card_type)
    topic = infer_topic_phrase(lead, card_type)
    lead_focus = _abstract_focus_line(lead, max_len=84) or compact_point(lead, 84)
    second_focus = _abstract_focus_line(second_line, max_len=72) if second_line else ""
    lead_focus_cn = "" if _is_mostly_ascii(lead_focus) else lead_focus
    second_focus_cn = "" if _is_mostly_ascii(second_focus) else second_focus
    if not lead_focus_cn and lead_focus:
        lead_focus_cn = _english_focus_hint(source, card_type, topic)
    if not second_focus_cn and second_focus:
        second_focus_cn = _english_focus_hint(second_line or source, card_type, topic)
    if card_type == "insight" and dedupe_key(lead_focus_cn) in {"社群互動更新", "社群互動貼文重點在現場動態與回饋"}:
        fallback_focus = _abstract_focus_line(source, max_len=88) or compact_point(strip_links_mentions(source), 88)
        if fallback_focus:
            lead_focus_cn = fallback_focus
    if second_focus_cn and lead_focus_cn and similarity_ratio(second_focus_cn, lead_focus_cn) >= 0.66:
        second_focus_cn = ""

    title_seed = _abstract_focus_line(lead, max_len=72) or compact_point(source, 72) or f"@{account} update"
    title_body = topic if _is_mostly_ascii(title_seed) else title_seed
    title = f"{prefix}｜{title_body}"
    fivew = build_fivew_brief(
        source=source,
        card_type=card_type,
        account=account,
        topic=topic,
        lead_focus=(lead_focus_cn or lead_focus or topic),
        event_facts=event_facts,
        schedule=schedule,
    )
    frame = build_universal_digest_frame(
        source=source,
        card_type=card_type,
        account=account,
        topic=topic,
        lead_focus=(lead_focus_cn or lead_focus or topic),
        fivew=fivew,
        schedule=schedule,
        numbers=numbers,
        event_facts=event_facts,
        report_digest=report_digest,
    )

    summary = clean_text(str(frame.get("summary") or ""))
    bullets_seed = frame.get("bullets") if isinstance(frame.get("bullets"), list) else []
    bullets = _unique_non_empty([clean_text(str(x)) for x in bullets_seed], limit=3)
    fallback_by_type = {
        "event": ["建議動作：先看原文確認時間、地點與參與方式。"],
        "market": ["影響：這則內容會影響社群對市場價格與熱度的判讀。"],
        "announcement": ["下一步：留意官方後續公告。"],
        "feature": ["下一步：確認正式開放條件與時間。"],
        "report": ["使用建議：先比較方案差異再採用。"],
        "insight": ["延伸追蹤：觀察後續是否出現明確規則。"],
    }
    for pad in fallback_by_type.get(card_type, []):
        if len(bullets) >= 3:
            break
        bullets.append(pad)

    if not summary:
        summary = clean_text(f"{prefix}已完成重整，主軸為「{topic}」，可查看下方重點與原文連結。")
    if similarity_ratio(summary, source) > 0.82 or not _contains_cjk(summary):
        summary = clean_text(f"{prefix}已完成重整，主軸為「{topic}」，可查看下方重點與原文連結。")
    return {
        "title": title,
        "summary": summary[:280],
        "bullets": bullets[:3],
    }


def normalize_detail_lines(lines: Any, limit: int = 6) -> list[str]:
    if not isinstance(lines, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        text = clean_text(str(raw))
        if not text:
            continue
        sig = dedupe_key(text)
        if sig and sig in seen:
            continue
        if sig:
            seen.add(sig)
        out.append(text[:180])
        if len(out) >= limit:
            break
    return out


def build_detail_copy(
    text: str,
    card_type: str,
    account: str,
    event_facts_override: dict[str, str] | None = None,
) -> dict[str, Any]:
    source = clean_text(text)
    if not source:
        return {"detail_summary": "", "detail_lines": []}

    lines = pick_signal_lines(source, limit=8)
    lead = lines[0] if lines else source
    second = lines[1] if len(lines) > 1 else ""
    topic = infer_topic_phrase(lead, card_type)
    lead_focus = _abstract_focus_line(lead, max_len=90) or compact_point(lead, 90)
    second_focus = _abstract_focus_line(second, max_len=80) if second else ""
    if _is_mostly_ascii(lead_focus):
        lead_focus = _english_focus_hint(source, card_type, topic)
    if _is_mostly_ascii(second_focus):
        second_focus = _english_focus_hint(second or source, card_type, topic)
    if second_focus and similarity_ratio(second_focus, lead_focus) >= 0.7:
        second_focus = ""

    schedule = extract_schedule_facts(source, limit=4)
    numbers = extract_numeric_facts(source, limit=4)
    event_facts = normalize_event_facts(event_facts_override or {})
    if card_type == "event":
        inferred = build_event_facts(source)
        merged = inferred.copy()
        merged.update(event_facts)
        event_facts = merged

    fivew = build_fivew_brief(
        source=source,
        card_type=card_type,
        account=account,
        topic=topic,
        lead_focus=lead_focus or topic,
        event_facts=event_facts,
        schedule=schedule,
    )
    report_digest = build_report_digest(source) if card_type == "report" else {}
    frame = build_universal_digest_frame(
        source=source,
        card_type=card_type,
        account=account,
        topic=topic,
        lead_focus=(lead_focus or topic),
        fivew=fivew,
        schedule=schedule,
        numbers=numbers,
        event_facts=event_facts,
        report_digest=report_digest,
    )

    detail_summary = clean_text(str(frame.get("detail_summary") or frame.get("summary") or ""))
    detail_lines = normalize_detail_lines(frame.get("detail_lines"), limit=6)
    if not detail_lines:
        detail_lines = normalize_detail_lines(frame.get("bullets"), limit=6)

    if second_focus:
        second_line = f"補充脈絡：{second_focus}"
        if not any(dedupe_key(second_line) == dedupe_key(row) for row in detail_lines):
            detail_lines.append(second_line)
    detail_lines = normalize_detail_lines(detail_lines, limit=6)

    who = fivew.get("who") or f"@{account}"
    if not detail_summary:
        detail_summary = clean_text(f"{who} 這篇內容主軸是「{topic}」，建議搭配原文查看完整脈絡。")[:420]
    elif len(strip_links_mentions(detail_summary)) < 36 and detail_lines:
        pad = "；".join(detail_lines[:2])
        detail_summary = clean_text(f"{detail_summary} 重點補充：{pad}")[:420]
    return {
        "detail_summary": detail_summary,
        "detail_lines": detail_lines[:6],
    }


def enrich_detail_view(card: StoryCard) -> None:
    base_text = clean_text(card.raw_text or card.summary or card.title)
    if not base_text:
        return
    built = build_detail_copy(
        base_text,
        card.card_type,
        card.account,
        event_facts_override=normalize_event_facts(card.event_facts),
    )
    built_summary = clean_text(str(built.get("detail_summary") or ""))
    built_lines = normalize_detail_lines(built.get("detail_lines"), limit=6)

    existing_summary = clean_text(str(card.detail_summary or ""))
    existing_lines = normalize_detail_lines(card.detail_lines, limit=6)
    generic_line_hits = sum(1 for x in existing_lines if GENERIC_DETAIL_RE.search(clean_text(x)))
    has_generic_detail = bool(GENERIC_DETAIL_RE.search(existing_summary)) or generic_line_hits > 0
    weak_summary = (
        not existing_summary
        or len(strip_links_mentions(existing_summary)) < 36
        or similarity_ratio(existing_summary, clean_text(card.summary or "")) >= 0.92
        or bool(GENERIC_DETAIL_RE.search(existing_summary))
    )
    weak_lines = len(existing_lines) < 3 or generic_line_hits >= max(1, len(existing_lines) - 1)
    if card.card_type in {"event", "insight", "feature", "announcement"} and has_generic_detail:
        weak_summary = True
        weak_lines = True
    if card.card_type in {"feature", "announcement"}:
        leaked_event_frame = any(
            re.search(r"(活動主軸|時間與地點|獎勵重點|參與方式)", clean_text(x), re.I)
            for x in existing_lines
        )
        if leaked_event_frame:
            weak_summary = True
            weak_lines = True

    if card.card_type == "market":
        card.detail_summary = built_summary or existing_summary[:420]
        card.detail_lines = built_lines[:6]
        return

    if weak_summary and built_summary:
        card.detail_summary = built_summary
    elif existing_summary:
        card.detail_summary = existing_summary[:420]
    elif built_summary:
        card.detail_summary = built_summary

    if weak_lines and built_lines:
        card.detail_lines = built_lines
    else:
        card.detail_lines = existing_lines[:6]

def build_glance_line(card: StoryCard) -> str:
    raw = card.raw_text or card.title
    schedule = extract_schedule_facts(raw, limit=2)
    numbers = extract_numeric_facts(raw, limit=2)
    topic = infer_topic_phrase(card.title or raw, card.card_type)
    if card.card_type == "event":
        facts = card.event_facts or build_event_facts(raw)
        if facts.get("schedule") and facts.get("reward"):
            return f"活動 {topic}，時間 {facts['schedule']}，重點獎勵 {facts['reward']}。"
        if facts.get("schedule"):
            return f"活動 {topic}，時間 {facts['schedule']}，建議提前安排參與。"
        if schedule and facts.get("reward"):
            return f"活動 {topic}，時間 {schedule[0]}，重點獎勵 {facts['reward']}。"
        if schedule:
            return f"活動 {topic}，時間 {schedule[0]}，建議提前安排參與。"
        return f"活動 {topic}，建議追蹤報名與地點資訊。"
    if card.card_type == "feature":
        threshold = extract_sbt_threshold_facts(raw)
        tiers = [str(x) for x in threshold.get("tiers", []) if str(x).strip()]
        snapshot = str(threshold.get("snapshot") or "").strip()
        if tiers:
            tier_text = "、".join(tiers[:3])
            if snapshot:
                return f"功能更新 {topic}，門檻 {tier_text}，快照 {snapshot}。"
            return f"功能更新 {topic}，門檻 {tier_text}，需留意快照時間。"
        if schedule:
            return f"功能進度 {topic}，時間節點 {schedule[0]}，留意開放條件。"
        return f"功能進度 {topic}，留意下一則官方公告。"
    if card.card_type == "announcement":
        return f"官方公告 {topic}，請以原文作為最終版本。"
    if card.card_type == "market":
        meanings = _market_number_meanings(raw, numbers)
        if meanings:
            return f"市場重點：{topic}。{meanings[0]}"
        if numbers:
            return f"市場重點：{topic}。貼文提到 {numbers[0]}，請搭配原文判讀。"
        return f"這則在談 {topic}，可作為市場熱度與價格走勢的觀測參考。"
    bullets = [clean_text(str(x)) for x in (card.bullets or []) if str(x).strip()]
    for b in bullets:
        stripped = re.sub(r"^(核心重點|提及數字|補充內容|追蹤方向)[:：]\s*", "", b).strip()
        if stripped:
            return compact_point(stripped, 88)
    if numbers:
        return f"社群焦點 {topic}，提及數字 {numbers[0]}。"
    return f"社群焦點 {topic}。"


def infer_topic_labels(card: StoryCard) -> list[str]:
    # 分類信號只看原文/標題/結構化事實，避免被 AI 摘要文案反向污染。
    source = clean_text(" ".join(
        [
            str(card.raw_text or ""),
            str(card.title or ""),
            " ".join(str(x) for x in (normalize_event_facts(card.event_facts).values())),
        ]
    ))
    labels: list[str] = []

    def add(label: str) -> None:
        if label not in labels and label in ALLOWED_TOPIC_LABELS:
            labels.append(label)

    account = str(card.account or "").strip().lower().lstrip("@")
    if account.startswith("renaiss"):
        add("official")

    strict_event_call = bool(STRICT_EVENT_CALL_RE.search(source))
    has_threshold_notice = bool(SBT_THRESHOLD_NOTICE_RE.search(source))
    has_event_signal = card.card_type == "event" or _has_event_evidence(source, timeline_iso=str(card.timeline_date or ""))
    facts = normalize_event_facts(card.event_facts)
    if card.card_type == "event" and (facts.get("schedule") or facts.get("participation") or facts.get("location")):
        has_event_signal = True
    if has_threshold_notice and not strict_event_call:
        # 門檻/快照資訊本身不等於活動；除非同文具備明確參與語意。
        has_event_signal = _has_event_evidence(source, timeline_iso=str(card.timeline_date or ""))
    if has_event_signal:
        add("events")

    def _has_sbt_evidence(text: str, card_type: str, facts_map: dict[str, str]) -> bool:
        src = clean_text(text)
        if not src:
            return False
        reward_txt = clean_text(" ".join(str(v) for v in facts_map.values()))
        if re.search(r"\bsbt\b|soulbound", src, re.I):
            return True
        if reward_txt and re.search(r"\bsbt\b|soulbound|積分|积分|points?|reward|獎勵|奖励|airdrop|snapshot|快照|threshold|門檻", reward_txt, re.I):
            return True
        if re.search(r"(threshold|snapshot|top\s*\d+%|快照|門檻).{0,28}(points?|積分|分)", src, re.I):
            return True
        if re.search(r"(points?|積分|分).{0,28}(threshold|snapshot|top\s*\d+%|快照|門檻)", src, re.I):
            return True
        if card_type in {"event", "feature", "announcement"}:
            if re.search(r"(reward|rewards|獎勵|奖励|airdrop|merch|周邊|周边).{0,24}(sbt|積分|积分|points?)", src, re.I):
                return True
            if re.search(r"(sbt|積分|积分|points?).{0,24}(reward|rewards|獎勵|奖励|airdrop|merch|周邊|周边)", src, re.I):
                return True
        return False

    if _has_sbt_evidence(source, card.card_type, facts):
        add("sbt")

    if re.search(
        r"pokemon|寶可夢|宝可梦|one\s*piece|tcg|卡牌|卡片|pack|luffy|psa|snkrdunk|pricecharting|collectr|op\d{1,2}",
        source,
        re.I,
    ):
        add("pokemon")

    if card.card_type in {"feature", "announcement"} or re.search(
        r"coming|upcoming|roadmap|launch|release|版本|上線|上线|開放|开放|即將|预告|progress",
        source,
        re.I,
    ):
        add("alpha")

    if card.card_type == "report" or (
        GUIDE_SIGNAL_RE.search(source) and not account.startswith("renaiss")
    ):
        add("tools")

    if not labels:
        add("other")
    return labels


def assign_topic_labels(card: StoryCard, keep_existing: bool = True) -> None:
    existing = normalize_topic_labels(card.topic_labels)
    inferred = infer_topic_labels(card)
    if keep_existing and existing:
        merged = existing + [x for x in inferred if x not in existing]
    else:
        merged = inferred if inferred else existing
    source = clean_text(" ".join(
        [
            str(card.raw_text or ""),
            str(card.title or ""),
            " ".join(str(x) for x in (normalize_event_facts(card.event_facts).values())),
        ]
    ))
    account = str(card.account or "").strip().lower().lstrip("@")

    if "events" in merged:
        strict_event_call = bool(STRICT_EVENT_CALL_RE.search(source))
        has_threshold_notice = bool(SBT_THRESHOLD_NOTICE_RE.search(source))
        if card.card_type in {"feature", "announcement"} and not _has_event_evidence(source, timeline_iso=str(card.timeline_date or "")):
            merged = [x for x in merged if x != "events"]
        if has_threshold_notice and not strict_event_call and not _has_event_evidence(source, timeline_iso=str(card.timeline_date or "")):
            merged = [x for x in merged if x != "events"]

    if "tools" in merged:
        allow_tools = card.card_type == "report" or (bool(GUIDE_SIGNAL_RE.search(source)) and not account.startswith("renaiss"))
        if not allow_tools:
            merged = [x for x in merged if x != "tools"]

    if "sbt" in merged:
        facts = normalize_event_facts(card.event_facts)
        sbt_ok = False
        if re.search(r"\bsbt\b|soulbound", source, re.I):
            sbt_ok = True
        elif re.search(r"(threshold|snapshot|top\s*\d+%|快照|門檻).{0,28}(points?|積分|分)", source, re.I):
            sbt_ok = True
        elif re.search(r"(points?|積分|分).{0,28}(threshold|snapshot|top\s*\d+%|快照|門檻)", source, re.I):
            sbt_ok = True
        else:
            reward_txt = clean_text(" ".join(str(v) for v in facts.values()))
            if reward_txt and re.search(r"\bsbt\b|soulbound|snapshot|快照|threshold|門檻", reward_txt, re.I):
                sbt_ok = True
        if not sbt_ok:
            merged = [x for x in merged if x != "sbt"]

    if account.startswith("renaiss") and "official" not in merged:
        merged.append("official")

    card.topic_labels = merged if merged else ["other"]


def enrich_card_metadata(card: StoryCard) -> None:
    base_dt = _parse_iso_safe(card.published_at) or datetime.now(timezone.utc)
    timeline_iso, _timeline_label = extract_timeline_date(card.raw_text or card.title, base_dt=base_dt)
    card.template_id = choose_template_id(card.card_type)
    card.timeline_date = timeline_iso
    card.event_facts = build_event_facts(card.raw_text or card.title) if card.card_type == "event" else {}
    card.glance = compact_point(build_glance_line(card), 120)
    card.urgency = compute_urgency(card.card_type, card.importance, timeline_iso)
    assign_topic_labels(card, keep_existing=True)


def normalize_card_semantics(card: StoryCard, preserve_type: bool = False) -> None:
    source = card.raw_text or card.summary or card.title
    base_dt = _parse_iso_safe(card.published_at) or datetime.now(timezone.utc)
    timeline_iso, _ = extract_timeline_date(source, base_dt=base_dt)
    inferred_type, inferred_layout, inferred_tags = classify_story(source)

    if not preserve_type or card.card_type not in ALLOWED_CARD_TYPES:
        card.card_type = inferred_type
    elif card.card_type in {"event", "insight"} and inferred_type != card.card_type:
        # 允許用語意規則修正 AI 在 event/insight 之間的誤分，避免「活動被判成觀點」或反向誤判。
        card.card_type = inferred_type
    if not str(card.layout or "").strip() or str(card.layout).lower() not in {"poster", "brief", "data", "timeline"}:
        card.layout = inferred_layout
    if not card.tags or card.tags == ["觀點"]:
        card.tags = inferred_tags[:]
    if timeline_iso:
        card.timeline_date = timeline_iso
    elif not card.timeline_date:
        card.timeline_date = ""

    card.template_id = choose_template_id(card.card_type)
    if card.card_type == "event":
        inferred_facts = build_event_facts(source)
        existing_facts = normalize_event_facts(card.event_facts)
        merged_facts = inferred_facts.copy()
        merged_facts.update(existing_facts)
        card.event_facts = merged_facts
    else:
        card.event_facts = {}
    card.glance = compact_point(build_glance_line(card), 120)
    card.urgency = compute_urgency(card.card_type, card.importance, card.timeline_date)
    assign_topic_labels(card, keep_existing=True)


def normalize_cards_semantics(cards: list[StoryCard], preserve_type: bool = False) -> None:
    for card in cards:
        normalize_card_semantics(card, preserve_type=preserve_type)


GENERIC_SUMMARY_RE = re.compile(
    r"^這則內容(?:屬於|偏向)|^重點摘要[:：]|主題脈絡[:：]|內容屬社群互動貼文|可作為討論基礎|適合當作趨勢參考|建議關注後續公告|需與其他來源交叉驗證|核心事件[:：]|關鍵數字[:：]|判讀建議[:：]|市場訊號[:：]|貼文提到的數據包含|這類資訊通常會直接影響市場預期與討論熱度|可先視為社群風向參考|官方更新方向已釋出，細節待後續公告|重點在(?:提升|同步|擴大|釋出|補充|反映)|若後續出現規則、獎勵或價格條件",
    re.I,
)
GENERIC_BULLET_RE = re.compile(
    r"^(分析主題|文中數據|使用方式|活動主軸|行動建議|觀點定位|追蹤方式|訊號定位|判讀建議|核心訊號|關鍵數字|決策建議|核心事件|提及數字|可見數字)[:：]",
    re.I,
)
LOW_VALUE_BULLET_RE = re.compile(
    r"(可持續追蹤後續官方或社群回應|作為社群趨勢參考|持續追蹤|可作為研究線索，不直接當結論)",
    re.I,
)
BAD_MONEY_UNIT_RE = re.compile(r"\$\s*\d[\d,]*(?:\.\d+)?[kmb]?\s*（(?:版本|序號|張卡|年份)）", re.I)
GENERIC_DETAIL_RE = re.compile(
    r"(分享了社群現場觀察|可當風向參考|風向參考|若涉及規則、獎勵或價格|有機會延伸成後續活動或功能公告|現場重點[:：]|補充觀察[:：]|可能影響[:：]|下一步[:：]留意官方是否補充具體規則|先記錄生效時間，並追蹤下一則官方公告確認規則|重點在(?:提升|同步|擴大|釋出|補充|反映))",
    re.I,
)


def _summary_needs_rewrite(summary: str, source: str) -> bool:
    s = clean_text(summary)
    if not s:
        return True
    if BAD_MONEY_UNIT_RE.search(s):
        return True
    if GENERIC_SUMMARY_RE.search(s):
        return True
    if len(strip_links_mentions(s)) < 14:
        return True
    if similarity_ratio(s, source) >= 0.72:
        return True
    if not _contains_cjk(s):
        return True
    return False


def _bullets_need_rewrite(bullets: list[str], source: str) -> bool:
    if not bullets:
        return True
    generic = 0
    low_value = 0
    copied = 0
    bad_money_unit = 0
    for raw in bullets:
        b = clean_text(raw)
        if not b:
            generic += 1
            continue
        if BAD_MONEY_UNIT_RE.search(b):
            bad_money_unit += 1
        if GENERIC_BULLET_RE.search(b):
            generic += 1
        if LOW_VALUE_BULLET_RE.search(b):
            low_value += 1
        if similarity_ratio(b, source) >= 0.8:
            copied += 1
    if bad_money_unit >= 1:
        return True
    if generic >= max(1, len(bullets) - 1):
        return True
    if low_value >= 1:
        return True
    if copied >= max(1, len(bullets) - 1):
        return True
    return False


def denoise_editorial_text(card: StoryCard) -> None:
    source = card.raw_text or card.summary or card.title
    if not source:
        return
    shaped = build_editorial_copy(source, card.card_type, card.account)
    shaped_summary = str(shaped.get("summary") or "").strip()
    shaped_bullets = shaped.get("bullets") if isinstance(shaped.get("bullets"), list) else []

    if card.card_type == "market":
        summary = clean_text(card.summary or "")
        bullets = [clean_text(str(x))[:120] for x in (card.bullets or []) if str(x).strip()]
        needs_rewrite = (
            _summary_needs_rewrite(summary, source)
            or _bullets_need_rewrite(bullets, source)
            or _market_is_number_dump(summary, bullets)
        )
        if needs_rewrite:
            if shaped_summary:
                card.summary = shaped_summary[:320]
            if shaped_bullets:
                card.bullets = [clean_text(str(x))[:120] for x in shaped_bullets if str(x).strip()][:3]
        else:
            card.summary = summary[:320]
            card.bullets = bullets[:3]
        return

    summary = clean_text(card.summary or "")
    if _summary_needs_rewrite(summary, source) and shaped_summary:
        card.summary = shaped_summary[:320]

    bullets = [clean_text(str(x))[:120] for x in (card.bullets or []) if str(x).strip()]
    if _bullets_need_rewrite(bullets, source):
        card.bullets = [clean_text(str(x))[:120] for x in shaped_bullets if str(x).strip()][:3]
    elif card.card_type == "report":
        # 報告類固定用方案重點，避免退回模板句。
        card.bullets = [clean_text(str(x))[:120] for x in shaped_bullets if str(x).strip()][:3]
        if shaped_summary:
            card.summary = shaped_summary[:320]


def apply_editorial_fallback(cards: list[StoryCard]) -> None:
    for card in cards:
        text = card.raw_text or card.summary or card.title
        if not text:
            continue
        shaped = build_editorial_copy(text, card.card_type, card.account)
        new_title = str(shaped.get("title") or "").strip()
        new_summary = str(shaped.get("summary") or "").strip()
        new_bullets = shaped.get("bullets") if isinstance(shaped.get("bullets"), list) else []

        if new_title:
            card.title = new_title[:120]
        if new_summary:
            card.summary = new_summary[:320]
        if new_bullets:
            card.bullets = [clean_text(str(x))[:120] for x in new_bullets if str(x).strip()][:3]
        enrich_card_metadata(card)
        normalize_card_semantics(card)
        enrich_detail_view(card)


def _detail_needs_rewrite(card: StoryCard) -> bool:
    source = clean_text(card.raw_text or card.summary or card.title)
    summary = clean_text(card.detail_summary or "")
    lines = normalize_detail_lines(card.detail_lines, limit=6)
    if not summary or len(strip_links_mentions(summary)) < 36:
        return True
    if similarity_ratio(summary, clean_text(card.summary or "")) >= 0.92:
        return True
    if GENERIC_DETAIL_RE.search(summary):
        return True
    if not lines or len(lines) < 3:
        return True
    generic_hits = sum(1 for x in lines if GENERIC_DETAIL_RE.search(clean_text(x)))
    if generic_hits >= max(1, len(lines) - 1):
        return True
    if source and all(similarity_ratio(clean_text(x), source) >= 0.94 for x in lines):
        return True
    return False


def _threshold_update_needs_rewrite(card: StoryCard) -> bool:
    source = clean_text(card.raw_text or card.summary or card.title)
    if not re.search(r"(sbt|points?).{0,36}(threshold|top\s*\d+%|snapshot)|threshold update", source, re.I):
        return False
    facts = extract_sbt_threshold_facts(source)
    tiers = [str(x) for x in facts.get("tiers", []) if str(x).strip()]
    snapshot = str(facts.get("snapshot") or "").strip()
    if not tiers:
        return False
    merged_text = clean_text(" ".join(
        [
            str(card.summary or ""),
            " ".join(str(x) for x in (card.bullets or [])),
            str(card.detail_summary or ""),
            " ".join(str(x) for x in (card.detail_lines or [])),
        ]
    ))
    tier_hit = any(tier in merged_text for tier in tiers[:2])
    snapshot_hit = (not snapshot) or (snapshot in merged_text) or bool(re.search(r"(snapshot|快照)", merged_text, re.I))
    return not (tier_hit and snapshot_hit)


def _sbt_acquisition_missing(card: StoryCard) -> bool:
    labels = normalize_topic_labels(card.topic_labels)
    source = clean_text(card.raw_text or card.summary or card.title)
    if "sbt" not in labels and not has_sbt_signal(source):
        return False
    merged = clean_text(
        " ".join(
            [
                str(card.summary or ""),
                " ".join(str(x) for x in (card.bullets or [])),
                str(card.detail_summary or ""),
                " ".join(str(x) for x in (card.detail_lines or [])),
            ]
        )
    )
    if re.search(r"SBT\s*取得方式", merged, re.I):
        return False
    return True


def apply_quality_guard(card: StoryCard) -> None:
    source = clean_text(card.raw_text or card.summary or card.title)
    if not source:
        return

    shaped = build_editorial_copy(source, card.card_type, card.account)
    fallback_summary = clean_text(str(shaped.get("summary") or ""))
    fallback_bullets = [clean_text(str(x))[:120] for x in (shaped.get("bullets") or []) if str(x).strip()][:3]

    summary_now = clean_text(card.summary or "")
    bullets_now = [clean_text(str(x))[:120] for x in (card.bullets or []) if str(x).strip()]

    if card.card_type == "market":
        if _summary_needs_rewrite(summary_now, source) or _market_is_number_dump(summary_now, bullets_now):
            if fallback_summary:
                card.summary = fallback_summary[:320]
        if _bullets_need_rewrite(bullets_now, source) or _market_is_number_dump(summary_now, bullets_now):
            if fallback_bullets:
                card.bullets = fallback_bullets[:3]
    else:
        if _summary_needs_rewrite(summary_now, source):
            if fallback_summary:
                card.summary = fallback_summary[:320]
        if _bullets_need_rewrite(bullets_now, source):
            if fallback_bullets:
                card.bullets = fallback_bullets[:3]
        if card.card_type == "report" and fallback_bullets:
            if len(card.bullets or []) < 3:
                card.bullets = fallback_bullets[:3]

    if _detail_needs_rewrite(card):
        rebuilt = build_detail_copy(
            source,
            card.card_type,
            card.account,
            event_facts_override=normalize_event_facts(card.event_facts),
        )
        rebuilt_summary = clean_text(str(rebuilt.get("detail_summary") or ""))
        rebuilt_lines = normalize_detail_lines(rebuilt.get("detail_lines"), limit=6)
        if rebuilt_summary:
            card.detail_summary = rebuilt_summary[:420]
        if rebuilt_lines:
            card.detail_lines = rebuilt_lines[:6]

    if _threshold_update_needs_rewrite(card):
        rebuilt = build_editorial_copy(source, card.card_type, card.account)
        rebuilt_summary = clean_text(str(rebuilt.get("summary") or ""))
        rebuilt_bullets = [clean_text(str(x))[:120] for x in (rebuilt.get("bullets") or []) if str(x).strip()][:3]
        if rebuilt_summary:
            card.summary = rebuilt_summary[:320]
        if rebuilt_bullets:
            card.bullets = rebuilt_bullets
        rebuilt_detail = build_detail_copy(
            source,
            card.card_type,
            card.account,
            event_facts_override=normalize_event_facts(card.event_facts),
        )
        rd_summary = clean_text(str(rebuilt_detail.get("detail_summary") or ""))
        rd_lines = normalize_detail_lines(rebuilt_detail.get("detail_lines"), limit=6)
        if rd_summary:
            card.detail_summary = rd_summary[:420]
        if rd_lines:
            card.detail_lines = rd_lines[:6]

    if _sbt_acquisition_missing(card):
        rebuilt = build_editorial_copy(source, card.card_type, card.account)
        rebuilt_summary = clean_text(str(rebuilt.get("summary") or ""))
        rebuilt_bullets = [clean_text(str(x))[:120] for x in (rebuilt.get("bullets") or []) if str(x).strip()][:3]
        if rebuilt_summary:
            card.summary = rebuilt_summary[:320]
        if rebuilt_bullets:
            card.bullets = rebuilt_bullets
        rebuilt_detail = build_detail_copy(
            source,
            card.card_type,
            card.account,
            event_facts_override=normalize_event_facts(card.event_facts),
        )
        rd_summary = clean_text(str(rebuilt_detail.get("detail_summary") or ""))
        rd_lines = normalize_detail_lines(rebuilt_detail.get("detail_lines"), limit=6)
        if rd_summary:
            card.detail_summary = rd_summary[:420]
        if rd_lines:
            card.detail_lines = rd_lines[:6]

