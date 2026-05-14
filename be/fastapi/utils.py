import logging
import os
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger("f88-realtime-utils")

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default

def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default

def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))

def event_datetime(event_time: Optional[str]) -> datetime:
    tz = ZoneInfo(os.getenv("REALTIME_TZ", "Asia/Ho_Chi_Minh"))
    if not event_time:
        return datetime.now(tz)
    try:
        dt = datetime.fromisoformat(str(event_time).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        return dt.astimezone(tz)
    except Exception:
        return datetime.now(tz)

def collateral_mix_index(asset_name: str) -> int:
    name = (asset_name or "").lower()
    if "xe máy" in name or "xe may" in name:
        return 0
    if "ô tô" in name or "oto" in name:
        return 1
    if "điện thoại" in name or "laptop" in name or "dien thoai" in name:
        return 2
    if "bất động sản" in name or "bat dong san" in name or "sổ đỏ" in name or "so do" in name:
        return 3
    return 4

def compute_risk_radar_metrics(**kwargs):
    # Logic từ app.py cũ
    weather_high = kwargs.get("weather_high_store_count", 0)
    weather_total = kwargs.get("weather_total_store_count", 0)
    weather_ratio = (weather_high / weather_total * 100) if weather_total > 0 else 0
    
    par1_pct = kwargs.get("par1_pct", 0)
    
    repayment_late = kwargs.get("repayment_late_count", 0)
    repayment_total = kwargs.get("repayment_total_count", 0)
    repayment_ratio = (repayment_late / repayment_total * 100) if repayment_total > 0 else 0
    
    rej_total = kwargs.get("rejection_total_count", 0)
    rej_dti = kwargs.get("rejection_dti_count", 0)
    rej_ltv = kwargs.get("rejection_ltv_count", 0)
    rej_fraud = kwargs.get("rejection_fraud_count", 0)
    
    dti_ratio = (rej_dti / rej_total * 100) if rej_total > 0 else 0
    ltv_ratio = (rej_ltv / rej_total * 100) if rej_total > 0 else 0
    fraud_ratio = (rej_fraud / rej_total * 100) if rej_total > 0 else 0
    
    return {
        "values": [
            round(weather_ratio, 1),
            round(kwargs.get("par_overdue_count", 0) / 10, 1), # Mock scale
            round(repayment_ratio, 1),
            round(dti_ratio, 1),
            round(ltv_ratio, 1),
            round(fraud_ratio, 1)
        ],
        "details": {
            **kwargs,
            "weather_alert_ratio_pct": round(weather_ratio, 1),
            "repayment_late_ratio_pct": round(repayment_ratio, 1),
            "rejection_dti_ratio_pct": round(dti_ratio, 1),
            "rejection_ltv_ratio_pct": round(ltv_ratio, 1),
            "rejection_fraud_ratio_pct": round(fraud_ratio, 1),
        }
    }

def _feed_item(
    *,
    time_str: str,
    title: str,
    detail: str,
    badge: str,
    feed_type: str,
    event_id: Optional[str] = None,
) -> dict:
    row = {
        "time": time_str,
        "title": title,
        "detail": detail,
        "badge": badge,
        "type": feed_type,
        "msg": detail,
    }
    if event_id:
        row["event_id"] = event_id
    return row


def format_event_for_ui(event: dict) -> Optional[dict]:
    event_type = event.get("event_type")
    payload = event.get("payload") or {}
    event_time = event.get("event_time")
    event_id = event.get("event_id")

    if event_time:
        try:
            dt = event_datetime(event_time)
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            time_str = datetime.now(ZoneInfo(os.getenv("REALTIME_TZ", "Asia/Ho_Chi_Minh"))).strftime("%H:%M:%S")
    else:
        time_str = datetime.now(ZoneInfo(os.getenv("REALTIME_TZ", "Asia/Ho_Chi_Minh"))).strftime("%H:%M:%S")

    if event_type == "loan_disbursed":
        amt = safe_float(payload.get("SoTienGiaiNgan")) / 1_000_000
        contract = payload.get("SoHopDong") or ""
        return _feed_item(
            time_str=time_str,
            title="GIẢI NGÂN",
            detail=f"{contract} — {amt:.1f}M",
            badge="success",
            feed_type="info",
            event_id=event_id,
        )

    if event_type == "repayment_paid":
        total_pay = (
            safe_float(payload.get("SoTienGocDaTra"))
            + safe_float(payload.get("SoTienLaiDaTra"))
            + safe_float(payload.get("PhiPhatTreHan"))
        )
        amt = total_pay / 1_000_000
        contract = payload.get("SoHopDong") or ""
        late = payload.get("HanhViTraNo") in ("late_1_10", "late_11_30", "late_30_plus", "bad_debt")
        return _feed_item(
            time_str=time_str,
            title="THU NỢ" if not late else "THU NỢ (TRỄ)",
            detail=f"{contract} — {amt:.1f}M",
            badge="warning" if late else "success",
            feed_type="alert",
            event_id=event_id,
        )

    if event_type == "loan_application_created":
        return _feed_item(
            time_str=time_str,
            title="HỒ SƠ MỚI",
            detail=f"{payload.get('SoHopDong') or ''} — {payload.get('TenKhachHang') or ''}".strip(" —"),
            badge="warning",
            feed_type="txn",
            event_id=event_id,
        )

    if event_type == "loan_approved":
        amt = safe_float(payload.get("SoTienDuyetVay")) / 1_000_000
        return _feed_item(
            time_str=time_str,
            title="PHÊ DUYỆT",
            detail=f"{payload.get('SoHopDong') or ''} — {amt:.1f}M",
            badge="success",
            feed_type="info",
            event_id=event_id,
        )

    if event_type == "loan_rejected":
        return _feed_item(
            time_str=time_str,
            title="TỪ CHỐI",
            detail=f"{payload.get('SoHopDong') or ''} — {payload.get('LyDoTuChoi') or ''}".strip(" —"),
            badge="danger",
            feed_type="alert",
            event_id=event_id,
        )

    if event_type == "weather_updated":
        risk = (payload.get("risk") or "low").lower()
        loc = payload.get("TenKhuVuc") or payload.get("KhuVuc") or payload.get("MaCuaHang") or ""
        desc = payload.get("MoTaThoiTiet_VN") or ""
        rain = payload.get("LuongMua")
        wind = payload.get("TocDoGio_10m")
        extra = []
        if rain is not None:
            extra.append(f"Mưa {rain}mm")
        if wind is not None:
            extra.append(f"Gió {wind}km/h")
        tail = ", ".join(extra)
        detail = f"{loc}: {desc}" + (f" ({tail})" if tail else "")
        title = "THỜI TIẾT"
        badge = "danger" if risk == "high" else ("warning" if risk == "medium" else "success")
        return _feed_item(
            time_str=time_str,
            title=title,
            detail=detail,
            badge=badge,
            feed_type="weather",
            event_id=event_id,
        )

    if event_type == "loan_status_changed":
        new_st = (payload.get("TrangThaiMoi") or "")
        bad = any(x in new_st for x in ("Quá hạn", "Nợ xấu", "Nợ nghi ngờ"))
        return _feed_item(
            time_str=time_str,
            title="TRẠNG THÁI KHOẢN VAY",
            detail=f"{payload.get('SoHopDong') or ''}: {payload.get('TrangThaiCu') or '?'} → {new_st or '?'}",
            badge="danger" if bad else "warning",
            feed_type="alert" if bad else "info",
            event_id=event_id,
        )

    if event_type == "customer_created":
        return _feed_item(
            time_str=time_str,
            title="KHÁCH MỚI",
            detail=payload.get("TenKhachHang") or payload.get("MaKhachHang") or "",
            badge="success",
            feed_type="info",
            event_id=event_id,
        )

    return None

def update_hourly(hourly_data: dict, event_time: Any, disb_vnd: float = 0.0, coll_vnd: float = 0.0):
    dt = event_datetime(event_time)
    hour = dt.hour
    hour_label = f"{hour:02d}:00"
    if hour_label in hourly_data["labels"]:
        idx = hourly_data["labels"].index(hour_label)
        hourly_data["disbursement"][idx] = round(hourly_data["disbursement"][idx] + disb_vnd / 1_000_000, 2)
        hourly_data["collection"][idx] = round(hourly_data["collection"][idx] + coll_vnd / 1_000_000, 2)
