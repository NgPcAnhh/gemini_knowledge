import logging
import asyncio
import json
import os
import psycopg2.extras
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

from database import db_conn
from state import empty_snapshot, state
from utils import (
    safe_float, safe_int,
    collateral_mix_index, compute_risk_radar_metrics,
    event_datetime, format_event_for_ui, update_hourly
)

logger = logging.getLogger("f88-realtime-services")

FEED_MAX = 50

LATE_HANHVI = ("late_1_10", "late_11_30", "late_30_plus", "bad_debt")


def _risk_level_from_late_count(late_ct: int) -> str:
    if late_ct > 5:
        return "high"
    if late_ct >= 1:
        return "medium"
    return "low"


def _prepend_feed(data: Dict[str, Any], item: Dict[str, Any]) -> None:
    feed = list(data.get("feed") or [])
    eid = item.get("event_id")
    if eid:
        feed = [x for x in feed if x.get("event_id") != eid]
    feed.insert(0, item)
    data["feed"] = feed[:FEED_MAX]


def _refresh_risk_radar_state(data: Dict[str, Any]) -> None:
    rc = data.get("radar_counts") or {}
    rs = data.get("risk_static") or {}
    risk_metrics = compute_risk_radar_metrics(
        weather_high_store_count=sum(1 for x in data.get("map", []) if x.get("weather_risk") == "high"),
        weather_medium_store_count=sum(1 for x in data.get("map", []) if x.get("weather_risk") == "medium"),
        weather_total_store_count=len(data.get("map", [])),
        par_overdue_count=safe_int(rs.get("par_overdue_count")),
        par_active_count=safe_int(rs.get("par_active_count")),
        par1_pct=safe_float(data.get("stats", {}).get("par1")),
        repayment_late_count=safe_int(rc.get("repayment_late")),
        repayment_total_count=safe_int(rc.get("repayment_total")),
        rejection_total_count=safe_int(rc.get("reject_total")),
        rejection_dti_count=safe_int(rc.get("reject_dti")),
        rejection_ltv_count=safe_int(rc.get("reject_ltv")),
        rejection_fraud_count=safe_int(rc.get("reject_fraud")),
    )
    data["risk_radar"] = risk_metrics["values"]
    data["risk_radar_metrics"] = risk_metrics


def _update_map_weather(data: Dict[str, Any], payload: dict) -> None:
    risk_raw = (payload.get("risk") or "low").lower()
    w = "high" if risk_raw == "high" else ("medium" if risk_raw == "medium" else "low")
    key = payload.get("MaCuaHang") or payload.get("CuaHang_Key")
    if not key:
        return
    for item in data.get("map", []):
        if str(item.get("key")) == str(key):
            item["weather_risk"] = w
            return


def _increment_reject_radar(rc: Dict[str, Any], payload: dict) -> None:
    reason = payload.get("LyDoTuChoi") or ""
    ru = reason.upper()
    rc["reject_total"] = rc.get("reject_total", 0) + 1
    if "DTI" in ru:
        rc["reject_dti"] = rc.get("reject_dti", 0) + 1
    if "LTV" in ru:
        rc["reject_ltv"] = rc.get("reject_ltv", 0) + 1
    if "GIAN LẬN" in ru or "GIAN LAN" in ru or "FRAUD" in ru:
        rc["reject_fraud"] = rc.get("reject_fraud", 0) + 1


def compute_realtime_snapshot() -> Dict[str, Any]:
    tz = ZoneInfo(os.getenv("REALTIME_TZ", "Asia/Ho_Chi_Minh"))
    calendar_today = datetime.now(tz).date()
    snap = empty_snapshot()
    bad_debt_count = 0
    total_active = 0
    target_date = calendar_today
    target_date_str = target_date.strftime("%Y-%m-%d")

    try:
        conn = db_conn()
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        dict_cur.execute("SELECT MAX(COALESCE(event_time, ingestion_time)::date) AS max_d FROM Raw_Staging_Events")
        latest_date = (dict_cur.fetchone() or {}).get("max_d")
        use_cal = os.getenv("SNAPSHOT_USE_CALENDAR_TODAY", "1") == "1"
        if use_cal:
            dict_cur.execute(
                """
                SELECT COUNT(*) AS c FROM Raw_Staging_Events
                WHERE COALESCE(event_time, ingestion_time)::date = %s
                """,
                (calendar_today,),
            )
            has_today = safe_int((dict_cur.fetchone() or {}).get("c")) > 0
            target_date = calendar_today if has_today else (latest_date or calendar_today)
        else:
            target_date = latest_date if latest_date else calendar_today
        target_date_str = target_date.strftime("%Y-%m-%d")

        # 2. Stats Query: Pure Staging for Today
        dict_cur.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN event_type = 'loan_disbursed' THEN COALESCE(NULLIF(payload->>'SoTienGiaiNgan','')::numeric, 0) ELSE 0 END), 0) AS disb,
                COALESCE(SUM(CASE WHEN event_type = 'repayment_paid' THEN 
                    COALESCE(NULLIF(payload->>'SoTienGocDaTra','')::numeric, 0) + 
                    COALESCE(NULLIF(payload->>'SoTienLaiDaTra','')::numeric, 0) + 
                    COALESCE(NULLIF(payload->>'PhiPhatTreHan','')::numeric, 0) 
                ELSE 0 END), 0) AS coll,
                COALESCE(SUM(CASE WHEN event_type = 'cash_recorded' AND payload->>'SoTienChi' IS NOT NULL THEN COALESCE(NULLIF(payload->>'SoTienChi','')::numeric, 0) ELSE 0 END), 0) AS other_chi
            FROM Raw_Staging_Events
            WHERE COALESCE(event_time, ingestion_time)::date = %s
              AND event_type IN ('loan_disbursed', 'repayment_paid', 'cash_recorded')
            """,
            (target_date,)
        )
        row = dict_cur.fetchone() or {}
        snap["stats"]["disbursement"] = safe_float(row.get("disb"))
        snap["stats"]["collection"] = safe_float(row.get("coll"))
        snap["stats"]["net_cashflow"] = snap["stats"]["collection"] - snap["stats"]["disbursement"] - safe_float(row.get("other_chi"))

        # 3. Overdue/Risk stats
        dict_cur.execute(
            """
            SELECT COUNT(*) FILTER (WHERE dt.TrangThaiKhoanVay IN ('Quá hạn','Nợ nghi ngờ','Nợ xấu')) AS bad_debt_count,
                   COUNT(*) FILTER (WHERE dt.TrangThaiKhoanVay IN ('Đang lưu hành','Đã giải ngân','Quá hạn nhẹ','Quá hạn','Nợ nghi ngờ','Nợ xấu')) AS total_active
            FROM Fact_GiaoDich fg JOIN Dim_TrangThai dt ON fg.TrangThai_Key = dt.TrangThai_Key
            """
        )
        par = dict_cur.fetchone() or {}
        total_active = safe_float(par.get("total_active"))
        bad_debt_count = safe_float(par.get("bad_debt_count"))
        snap["stats"]["par1"] = round(bad_debt_count / total_active * 100, 2) if total_active > 0 else 0

        # 4. Map Query: staging + HĐ trả chậm theo chi nhánh (màu node theo late; weather_risk cho radar)
        dict_cur.execute(
            """
            WITH today_metrics AS (
                SELECT
                    payload->>'MaCuaHang' AS MaCuaHang,
                    CASE WHEN event_type = 'loan_disbursed' THEN 'disb' ELSE 'coll' END AS type,
                    COALESCE(NULLIF(payload->>'SoTienGiaiNgan','')::numeric, 0) +
                    COALESCE(NULLIF(payload->>'SoTienGocDaTra','')::numeric, 0) +
                    COALESCE(NULLIF(payload->>'SoTienLaiDaTra','')::numeric, 0) +
                    COALESCE(NULLIF(payload->>'PhiPhatTreHan','')::numeric, 0) AS amt
                FROM Raw_Staging_Events
                WHERE COALESCE(event_time, ingestion_time)::date = %s
                  AND event_type IN ('loan_disbursed', 'repayment_paid')
            ),
            aggregated_metrics AS (
                SELECT
                    MaCuaHang,
                    COUNT(*) FILTER (WHERE type = 'disb') AS loans_count,
                    SUM(CASE WHEN type = 'disb' THEN amt ELSE 0 END) AS disb_amt,
                    SUM(CASE WHEN type = 'coll' THEN amt ELSE 0 END) AS coll_amt
                FROM today_metrics
                GROUP BY 1
            ),
            late_contracts AS (
                SELECT
                    payload->>'MaCuaHang' AS MaCuaHang,
                    COUNT(DISTINCT payload->>'SoHopDong') AS late_ct
                FROM Raw_Staging_Events
                WHERE COALESCE(event_time, ingestion_time)::date = %s
                  AND event_type = 'repayment_paid'
                  AND COALESCE(payload->>'HanhViTraNo', '') IN ('late_1_10', 'late_11_30', 'late_30_plus', 'bad_debt')
                  AND payload->>'MaCuaHang' IS NOT NULL
                  AND payload->>'SoHopDong' IS NOT NULL
                GROUP BY 1
            )
            SELECT
                ch.MaCuaHang, ch.TenCuaHang, COALESCE(ch.KhuVuc, td.TenKhuVuc) AS area,
                td.Vido_Latitude AS lat, td.Kinhdo_Longitude AS lng,
                COALESCE(am.loans_count, 0) AS loans_today,
                COALESCE(am.disb_amt, 0) AS disb_today,
                COALESCE(am.coll_amt, 0) AS coll_today,
                COALESCE(lc.late_ct, 0) AS late_contracts_today
            FROM Dim_CuaHang ch
            LEFT JOIN Dim_ToaDo td ON ch.ToaDo_Key = td.ToaDo_Key
            LEFT JOIN aggregated_metrics am ON am.MaCuaHang = ch.MaCuaHang
            LEFT JOIN late_contracts lc ON lc.MaCuaHang = ch.MaCuaHang
            WHERE td.Vido_Latitude IS NOT NULL AND td.Kinhdo_Longitude IS NOT NULL
            """,
            (target_date, target_date),
        )
        map_rows = []
        for r in dict_cur.fetchall():
            late_ct = safe_int(r.get("late_contracts_today"))
            map_rows.append({
                "key": r.get("MaCuaHang"),
                "name": r.get("TenCuaHang"),
                "area": r.get("area") or "",
                "lat": safe_float(r.get("lat")),
                "lng": safe_float(r.get("lng")),
                "loans": safe_int(r.get("loans_today")),
                "disb_amt": safe_float(r.get("disb_today")),
                "coll_amt": safe_float(r.get("coll_today")),
                "late_contracts_today": late_ct,
                "weather_risk": "low",
                "risk_level": _risk_level_from_late_count(late_ct),
            })
        snap["map"] = map_rows

        # 5. Live Feed (newest first; event_id for dedupe with Redis stream)
        dict_cur.execute(
            """
            SELECT event_id, event_type, payload, COALESCE(event_time, ingestion_time) AS time
            FROM Raw_Staging_Events
            WHERE COALESCE(event_time, ingestion_time)::date = %s
              AND event_type IN ('loan_disbursed', 'repayment_paid', 'loan_application_created', 'loan_approved', 'loan_rejected')
            ORDER BY time DESC
            LIMIT 40
            """,
            (target_date,),
        )
        feed = []
        for r in dict_cur.fetchall():
            evt_data = {
                "event_id": r.get("event_id"),
                "event_type": r["event_type"],
                "payload": r["payload"],
                "event_time": r["time"].isoformat() if r["time"] else None,
            }
            item = format_event_for_ui(evt_data)
            if item:
                feed.append(item)
        snap["feed"] = feed

        # 6. Hourly Data: Pure Staging
        dict_cur.execute(
            """
            WITH hours AS (SELECT generate_series(8, 21) AS h),
            staging_hourly AS (
                SELECT
                    EXTRACT(HOUR FROM COALESCE(event_time, ingestion_time))::int AS h,
                    CASE WHEN event_type = 'loan_disbursed' THEN COALESCE(NULLIF(payload->>'SoTienGiaiNgan','')::numeric, 0) ELSE 0 END AS disb,
                    CASE WHEN event_type = 'repayment_paid' THEN 
                        COALESCE(NULLIF(payload->>'SoTienGocDaTra','')::numeric, 0) + 
                        COALESCE(NULLIF(payload->>'SoTienLaiDaTra','')::numeric, 0) + 
                        COALESCE(NULLIF(payload->>'PhiPhatTreHan','')::numeric, 0) 
                    ELSE 0 END AS coll
                FROM Raw_Staging_Events
                WHERE COALESCE(event_time, ingestion_time)::date = %s
                  AND event_type IN ('loan_disbursed', 'repayment_paid')
            )
            SELECT hours.h, COALESCE(SUM(disb), 0) AS disbursed, COALESCE(SUM(coll), 0) AS collected
            FROM hours LEFT JOIN staging_hourly ON hours.h = staging_hourly.h
            GROUP BY 1 ORDER BY 1
            """,
            (target_date,)
        )
        h_labels, h_disb, h_coll = [], [], []
        for r in dict_cur.fetchall():
            h_labels.append(f"{safe_int(r.get('h')):02d}:00")
            h_disb.append(round(safe_float(r.get("disbursed")) / 1_000_000, 2))
            h_coll.append(round(safe_float(r.get("collected")) / 1_000_000, 2))
        snap["hourly"] = {"labels": h_labels, "disbursement": h_disb, "collection": h_coll}

        # 6a. Product Mix (donut) = khoản phê duyệt theo loại TSĐB
        dict_cur.execute(
            """
            SELECT
                COALESCE(NULLIF(payload->>'TenLoaiTaiSan',''), NULLIF(payload->>'LoaiTaiSan',''), NULLIF(payload->>'TenLoaiHinh','')) AS asset
            FROM Raw_Staging_Events
            WHERE COALESCE(event_time, ingestion_time)::date = %s
              AND event_type = 'loan_approved'
            """,
            (target_date,),
        )
        for r in dict_cur.fetchall():
            asset_type = r.get("asset")
            if asset_type:
                idx = collateral_mix_index(asset_type)
                snap["product_mix"][idx] += 1

        # 6b. Approval Bar
        dict_cur.execute(
            """
            SELECT 
                COUNT(*) FILTER (WHERE event_type = 'repayment_paid' AND payload->>'HanhViTraNo' IN ('late_1_10', 'late_11_30', 'late_30_plus', 'bad_debt')) AS late_count,
                COUNT(*) FILTER (WHERE event_type = 'loan_approved') AS approved_count,
                COUNT(*) FILTER (WHERE event_type = 'loan_rejected') AS rejected_count
            FROM Raw_Staging_Events
            WHERE COALESCE(event_time, ingestion_time)::date = %s
              AND event_type IN ('repayment_paid', 'loan_approved', 'loan_rejected')
            """,
            (target_date,)
        )
        app_bar_row = dict_cur.fetchone() or {}
        snap["approval_bar"][0] = safe_int(app_bar_row.get("late_count"))
        snap["approval_bar"][1] = safe_int(app_bar_row.get("approved_count"))
        snap["approval_bar"][2] = safe_int(app_bar_row.get("rejected_count"))

        # 7. Risk Radar Metrics
        dict_cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'repayment_paid') AS repayment_total,
                COUNT(*) FILTER (WHERE event_type = 'repayment_paid' AND COALESCE(payload->>'HanhViTraNo', '') IN ('late_1_10', 'late_11_30', 'late_30_plus', 'bad_debt')) AS repayment_late,
                COUNT(*) FILTER (WHERE event_type = 'loan_rejected') AS reject_total,
                COUNT(*) FILTER (WHERE event_type = 'loan_rejected' AND COALESCE(payload->>'LyDoTuChoi', '') ILIKE '%%DTI%%') AS reject_dti,
                COUNT(*) FILTER (WHERE event_type = 'loan_rejected' AND COALESCE(payload->>'LyDoTuChoi', '') ILIKE '%%LTV%%') AS reject_ltv,
                COUNT(*) FILTER (WHERE event_type = 'loan_rejected' AND (payload->>'LyDoTuChoi' ILIKE '%%gian lận%%' OR payload->>'LyDoTuChoi' ILIKE '%%fraud%%')) AS reject_fraud
            FROM Raw_Staging_Events
            WHERE COALESCE(event_time, ingestion_time)::date = %s
            """,
            (target_date,)
        )
        ratios = dict_cur.fetchone() or {}
        risk_metrics = compute_risk_radar_metrics(
            weather_high_store_count=sum(1 for x in snap["map"] if x.get("weather_risk") == "high"),
            weather_medium_store_count=sum(1 for x in snap["map"] if x.get("weather_risk") == "medium"),
            weather_total_store_count=len(snap["map"]),
            par_overdue_count=safe_int(bad_debt_count),
            par_active_count=safe_int(total_active),
            par1_pct=snap["stats"]["par1"],
            repayment_late_count=safe_int(ratios.get("repayment_late")),
            repayment_total_count=safe_int(ratios.get("repayment_total")),
            rejection_total_count=safe_int(ratios.get("reject_total")),
            rejection_dti_count=safe_int(ratios.get("reject_dti")),
            rejection_ltv_count=safe_int(ratios.get("reject_ltv")),
            rejection_fraud_count=safe_int(ratios.get("reject_fraud")),
        )
        snap["risk_radar"] = risk_metrics["values"]
        snap["risk_radar_metrics"] = risk_metrics
        snap["radar_counts"] = {
            "repayment_total": safe_int(ratios.get("repayment_total")),
            "repayment_late": safe_int(ratios.get("repayment_late")),
            "reject_total": safe_int(ratios.get("reject_total")),
            "reject_dti": safe_int(ratios.get("reject_dti")),
            "reject_ltv": safe_int(ratios.get("reject_ltv")),
            "reject_fraud": safe_int(ratios.get("reject_fraud")),
        }
        snap["risk_static"] = {
            "par_overdue_count": safe_int(bad_debt_count),
            "par_active_count": safe_int(total_active),
        }

        conn.close()
    except Exception as exc:
        logger.exception("Failed to compute snapshot: %s", exc)

    snap["active_date"] = target_date_str
    snap["timestamp"] = datetime.now().isoformat()
    return snap

async def process_event_update(event_raw: Any) -> Dict[str, Any]:
    try:
        event = json.loads(event_raw) if isinstance(event_raw, str) else event_raw
    except Exception:
        return state.data

    event_type = event.get("event_type")
    event_id = event.get("event_id")
    payload = event.get("payload") or {}
    evt_dt = event_datetime(event.get("event_time"))

    async with state.lock:
        if "active_date" not in state.data or event_type == "system_reset":
            state.data = await asyncio.to_thread(compute_realtime_snapshot)
            state.reset_seen_events()
            return state.data

        if not state.is_new_event(event_id):
            return state.data

        active_date = datetime.fromisoformat(state.data["active_date"]).date()
        if evt_dt.date() > active_date:
            state.data = await asyncio.to_thread(compute_realtime_snapshot)
            state.reset_seen_events()
            return state.data
        if evt_dt.date() < active_date:
            return state.data

        did_update = False
        rc = state.data.setdefault(
            "radar_counts",
            {
                "repayment_total": 0,
                "repayment_late": 0,
                "reject_total": 0,
                "reject_dti": 0,
                "reject_ltv": 0,
                "reject_fraud": 0,
            },
        )

        if event_type == "loan_approved":
            state.data["approval_bar"][1] += 1
            asset_type = payload.get("TenLoaiTaiSan") or payload.get("LoaiTaiSan") or payload.get("TenLoaiHinh")
            if asset_type:
                idx = collateral_mix_index(asset_type)
                state.data["product_mix"][idx] += 1
            did_update = True

        elif event_type == "loan_application_created":
            did_update = True

        elif event_type == "loan_rejected":
            state.data["approval_bar"][2] += 1
            _increment_reject_radar(rc, payload)
            did_update = True

        elif event_type == "loan_disbursed":
            amount = safe_float(payload.get("SoTienGiaiNgan"))
            state.data["stats"]["disbursement"] += amount
            state.data["stats"]["net_cashflow"] -= amount
            update_hourly(state.data["hourly"], event.get("event_time"), disb_vnd=amount)
            _update_map_node(payload, disb_amount=amount)
            did_update = True

        elif event_type == "repayment_paid":
            amount = (
                safe_float(payload.get("SoTienGocDaTra"))
                + safe_float(payload.get("SoTienLaiDaTra"))
                + safe_float(payload.get("PhiPhatTreHan"))
            )
            state.data["stats"]["collection"] += amount
            state.data["stats"]["net_cashflow"] += amount
            update_hourly(state.data["hourly"], event.get("event_time"), coll_vnd=amount)
            is_late = payload.get("HanhViTraNo") in LATE_HANHVI
            _update_map_node(payload, coll_amount=amount, late_increment=1 if is_late else 0)
            if is_late:
                state.data["approval_bar"][0] += 1
            rc["repayment_total"] = rc.get("repayment_total", 0) + 1
            if is_late:
                rc["repayment_late"] = rc.get("repayment_late", 0) + 1
            did_update = True

        elif event_type == "weather_updated":
            _update_map_weather(state.data, payload)
            did_update = True

        item = format_event_for_ui(event)
        if item:
            _prepend_feed(state.data, item)
            did_update = True

        if did_update:
            _refresh_risk_radar_state(state.data)

        state.data["timestamp"] = datetime.now().isoformat()

    return state.data

def _update_map_node(payload: dict, disb_amount=0.0, coll_amount=0.0, late_increment: int = 0):
    key = payload.get("MaCuaHang") or payload.get("CuaHang_Key")
    if not key:
        return
    for item in state.data.get("map", []):
        if str(item.get("key")) == str(key):
            if disb_amount > 0:
                item["loans"] = safe_int(item.get("loans")) + 1
                item["disb_amt"] = safe_float(item.get("disb_amt")) + disb_amount
            if coll_amount > 0:
                item["coll_amt"] = safe_float(item.get("coll_amt")) + coll_amount
            if late_increment:
                item["late_contracts_today"] = safe_int(item.get("late_contracts_today")) + late_increment
            item["risk_level"] = _risk_level_from_late_count(safe_int(item.get("late_contracts_today")))
            if "weather_risk" not in item:
                item["weather_risk"] = "low"
            return
