"""
simulator/main.py

Orchestrator mô phỏng realtime/batch.

Chạy realtime:
python -m simulator.main --mode realtime --stores 800 --daily-min 1000 --daily-max 5000 --interval 1 --sim-minutes-per-tick 1

Chạy batch:
python -m simulator.main --mode batch --date 2026-05-13 --days 1 --stores 800
"""

import argparse
import logging
import os
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg2
from faker import Faker

from simulator.config import (
    KAFKA_TOPICS,
    PG_CONFIG,
    LOAN_TYPE_WEIGHTS,
    POST_APPROVAL_BEHAVIOR,
    STAFF_COUNT,
    STAFF_ROLES,
    STORE_TIERS,
    ACTIVE_HOURS,
    DEFAULT_DAILY_MIN,
    DEFAULT_DAILY_MAX,
    DEFAULT_HOURLY_MIN,
    DEFAULT_HOURLY_MAX,
    DEFAULT_PAYMENT_RATIO,
)
from simulator.distributions import DistributionEngine
from simulator.generators import EventGenerator, ActiveLoan
from simulator.kafka_producer import EventProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("f88_simulator")
fake = Faker("vi_VN")

SIM_TZ = ZoneInfo(os.getenv("SIM_TZ", "Asia/Ho_Chi_Minh"))


def sim_now() -> datetime:
    """Wall clock hiện tại theo Asia/Ho_Chi_Minh (naive = giờ địa phương)."""
    return datetime.now(SIM_TZ).replace(tzinfo=None, microsecond=0)


def _parse_event_dt_hcm(s: str) -> datetime:
    """Parse event_time ISO, chuẩn hóa về giờ địa phương HCM (naive)."""
    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(SIM_TZ).replace(tzinfo=None)
    return dt.replace(microsecond=0)


class BusinessSimulator:
    def __init__(
        self,
        dist: DistributionEngine,
        gen: EventGenerator,
        producer: EventProducer,
        stores: list[dict],
        daily_min: int = DEFAULT_DAILY_MIN,
        daily_max: int = DEFAULT_DAILY_MAX,
        hourly_min: int = DEFAULT_HOURLY_MIN,
        hourly_max: int = DEFAULT_HOURLY_MAX,
        payment_ratio: float = DEFAULT_PAYMENT_RATIO,
        emit_cashflow_events: bool = False,
    ):
        self.dist = dist
        self.gen = gen
        self.producer = producer
        self.stores = stores
        self.daily_target = int(dist.rng.integers(daily_min, daily_max + 1))
        self.hourly_min = hourly_min
        self.hourly_max = hourly_max
        self.payment_ratio = payment_ratio
        self.emit_cashflow_events = emit_cashflow_events
        self.active_loans: list[ActiveLoan] = []
        self.weather_by_store: dict[str, dict] = {}
        self.event_buffer: list[dict] = []

    def _topic_key(self, event: dict) -> tuple[str, dict, str | None]:
        et = event.get("event_type")
        p = event.get("payload", {})
        if et == "customer_created":
            return KAFKA_TOPICS["customer"], event, p.get("CMND_CCCD")
        if et == "asset_appraised":
            return KAFKA_TOPICS["asset"], event, p.get("CMND_CCCD")
        if et == "loan_application_created":
            return KAFKA_TOPICS["loan_application"], event, p.get("SoHopDong")
        if et in ("loan_approved", "loan_rejected"):
            return KAFKA_TOPICS["loan_decision"], event, p.get("SoHopDong")
        if et == "loan_disbursed":
            return KAFKA_TOPICS["loan_disbursement"], event, p.get("SoHopDong")
        if et == "repayment_paid":
            return KAFKA_TOPICS["loan_repayment"], event, p.get("SoHopDong")
        if et == "loan_status_changed":
            return KAFKA_TOPICS["loan_status"], event, p.get("SoHopDong")
        if et == "cash_recorded":
            return KAFKA_TOPICS["cashflow"], event, p.get("SoHopDong") or p.get("MaCuaHang")
        if et == "weather_updated":
            return KAFKA_TOPICS["weather"], event, p.get("MaCuaHang") or p.get("ToaDo_Key")
        return KAFKA_TOPICS["loan_status"], event, p.get("SoHopDong")

    def _hourly_target(self, dt: datetime) -> int:
        if dt.hour not in ACTIVE_HOURS:
            return 0

        # Phân bổ daily target theo hour factor, nhưng clamp 50-300/h.
        from simulator.config import HOUR_FACTOR, WEEKDAY_FACTOR
        total_factor = sum(HOUR_FACTOR.get(h, 0.1) for h in ACTIVE_HOURS)
        base = self.daily_target * HOUR_FACTOR.get(dt.hour, 0.1) / total_factor
        base *= WEEKDAY_FACTOR.get(dt.weekday(), 1.0)
        noisy = int(max(0, round(base * float(self.dist.rng.uniform(0.75, 1.25)))))
        return int(max(self.hourly_min, min(self.hourly_max, noisy)))

    def _select_stores_for_hour(self, dt: datetime, count: int) -> list[dict]:
        if not self.stores or count <= 0:
            return []
        active_ratio = float(self.dist.rng.uniform(0.08, 0.35))
        active_n = max(1, min(len(self.stores), int(len(self.stores) * active_ratio)))
        weather_risk = "low"

        weights = []
        for store in self.stores:
            weather = self.weather_by_store.get(store.get("MaCuaHang")) or {"risk": "low"}
            weights.append(self.dist.calc_store_weight(store, dt, weather.get("risk", "low")))

        selected = self.dist.weighted_choices(self.stores, weights, active_n)
        # unique by MaCuaHang
        uniq = {}
        for s in selected:
            uniq[s["MaCuaHang"]] = s
        return list(uniq.values())

    def _allocate_counts_to_stores(self, dt: datetime, total_count: int, selected_stores: list[dict]) -> dict[str, int]:
        if not selected_stores:
            return {}
        weights = []
        for s in selected_stores:
            weather = self.weather_by_store.get(s.get("MaCuaHang")) or {"risk": "low"}
            weights.append(self.dist.calc_store_weight(s, dt, weather.get("risk", "low")))

        weights_sum = sum(weights)
        allocation = {}
        remain = total_count
        for s, w in zip(selected_stores[:-1], weights[:-1]):
            lam = max(0.1, total_count * w / weights_sum)
            n = min(remain, self.dist.poisson_count(lam))
            allocation[s["MaCuaHang"]] = n
            remain -= n
        allocation[selected_stores[-1]["MaCuaHang"]] = max(0, remain)

        # tránh trường hợp Poisson làm cửa hàng active vẫn toàn 0 ở đầu list
        if sum(allocation.values()) == 0 and total_count > 0:
            allocation[selected_stores[0]["MaCuaHang"]] = total_count
        return allocation

    def _refresh_weather(self, dt: datetime, sample_ratio: float = 0.08) -> list[dict]:
        events = []
        if not self.stores:
            return events
        n = max(1, int(len(self.stores) * sample_ratio))
        sample = self.dist.weighted_choices(self.stores, [1.0] * len(self.stores), n)
        seen = set()
        for store in sample:
            code = store.get("MaCuaHang")
            if code in seen:
                continue
            seen.add(code)
            weather = self.dist.gen_weather(store)
            self.weather_by_store[code] = weather
            events.append(self.gen.gen_weather_event(dt, store, weather))
        return events

    def generate_contract_chain(self, dt: datetime, store: dict) -> list[dict]:
        events = []
        weather = self.weather_by_store.get(store.get("MaCuaHang")) or {"risk": "low"}
        weather_risk = weather.get("risk", "low")

        customer_event = self.gen.gen_customer_event(dt, store, weather_risk)
        customer_event["payload"]["WeatherRisk"] = weather_risk
        events.append(customer_event)

        loan_types = list(LOAN_TYPE_WEIGHTS.keys())
        loan_weights = list(LOAN_TYPE_WEIGHTS.values())
        loan_type = self.dist.weighted_choice(loan_types, loan_weights)
        loan_amount = self.dist.gen_loan_amount(loan_type)

        asset_event = self.gen.gen_asset_event(dt, customer_event["payload"]["CMND_CCCD"], loan_type, loan_amount)
        events.append(asset_event)

        sale = self.gen.choose_employee(store, ("Giao dịch viên", "Nhân viên thẩm định", "Cửa hàng trưởng"))
        app_event = self.gen.gen_application_event(
            event_time=dt,
            customer_cmnd=customer_event["payload"]["CMND_CCCD"],
            store=store,
            employee_code=sale.get("MaNhanVien"),
            loan_type=loan_type,
            loan_amount_vnd=loan_amount,
        )
        events.append(app_event)

        approver = self.gen.choose_employee(store, ("Cửa hàng trưởng", "Nhân viên thẩm định"))
        decision_time = dt + timedelta(minutes=int(self.dist.rng.integers(5, 15)))
        decision_event = self.gen.gen_decision_event(
            event_time=decision_time,
            contract_no=app_event["payload"]["SoHopDong"],
            customer_payload=customer_event["payload"],
            loan_amount_vnd=loan_amount,
            asset_value_vnd=asset_event["payload"]["GiaTriDinhGia"],
            loan_type=loan_type,
            approver_code=approver.get("MaNhanVien"),
            weather_risk=weather_risk,
        )
        events.append(decision_event)

        if decision_event["event_type"] == "loan_approved":
            post_action = self.dist.weighted_choice(list(POST_APPROVAL_BEHAVIOR.keys()), list(POST_APPROVAL_BEHAVIOR.values()))
            if post_action == "same_day":
                dmin = int(os.getenv("DISBURSE_DELAY_MIN", "2"))
                dmax = int(os.getenv("DISBURSE_DELAY_MAX", "30"))
                if dmax < dmin:
                    dmin, dmax = dmax, dmin
                delay = int(self.dist.rng.integers(dmin, dmax + 1))
            elif post_action == "next_day":
                delay = int(self.dist.rng.integers(720, 1440))
            else:
                return events

            disb_time = decision_time + timedelta(minutes=delay)
            disb_event = self.gen.gen_disbursement_event(
                event_time=disb_time,
                contract_no=app_event["payload"]["SoHopDong"],
                store=store,
                approved_amount=decision_event["payload"]["SoTienDuyetVay"],
                term_months=decision_event["payload"]["ThoiHanVay_Thang"],
                employee_code=approver.get("MaNhanVien"),
            )
            events.append(disb_event)

            loan = self.gen.build_active_loan(app_event, decision_event, disb_event, customer_event)
            self.active_loans.append(loan)

            status_event = self.gen.gen_status_event(
                disb_time + timedelta(seconds=1),
                loan,
                old_status="Đã giải ngân",
                new_status="Đang lưu hành",
                employee_code=approver.get("MaNhanVien"),
                reason="Khoản vay đã giải ngân và bắt đầu lưu hành",
            )
            events.append(status_event)

            if self.emit_cashflow_events:
                loai = "Giải ngân tiền mặt" if "mặt" in disb_event["payload"].get("PhuongThuc", "").lower() else "Giải ngân chuyển khoản"
                events.append(self.gen.gen_cashflow_event(
                    event_time=disb_time,
                    store=store,
                    ten_loai_thu_chi=loai,
                    so_tien_chi=disb_event["payload"]["SoTienGiaiNgan"],
                    contract_no=loan.SoHopDong,
                    employee_code=approver.get("MaNhanVien"),
                    phuong_thuc=disb_event["payload"].get("PhuongThuc", "Tiền mặt"),
                    ghi_chu=f"Giải ngân HĐ {loan.SoHopDong}",
                ))

        return events

    def generate_repayment_chain(self, dt: datetime) -> list[dict]:
        if not self.active_loans:
            return []

        # ưu tiên hợp đồng đang lưu hành/có dư nợ.
        active = [l for l in self.active_loans if l.DuNoConLai > 0 and l.TrangThai != "Tất toán"]
        if not active:
            return []

        loan = self.dist.weighted_choice(active, [max(1.0, l.DuNoConLai / 1_000_000) for l in active])
        store = next((s for s in self.stores if s.get("MaCuaHang") == loan.MaCuaHang), None) or {
            "MaCuaHang": loan.MaCuaHang, "CuaHang_Key": loan.CuaHang_Key, "ToaDo_Key": loan.ToaDo_Key,
            "KhuVuc": loan.KhuVuc, "TenKhuVuc": loan.TenKhuVuc,
        }
        collector = self.gen.choose_employee(store, ("Nhân viên thu hồi nợ", "Giao dịch viên", "Cửa hàng trưởng"))
        weather = self.weather_by_store.get(loan.MaCuaHang) or {"risk": loan.WeatherRisk or "low"}
        old_status = loan.TrangThai

        repayment_event = self.gen.gen_repayment_event(dt, loan, store, collector.get("MaNhanVien"), weather.get("risk", "low"))
        events = [repayment_event]

        new_status = repayment_event["payload"]["TrangThaiSauThanhToan"]
        if new_status != old_status:
            events.append(self.gen.gen_status_event(
                dt + timedelta(seconds=1),
                loan,
                old_status=old_status,
                new_status=new_status,
                employee_code=collector.get("MaNhanVien"),
                reason=f"Thanh toán: {repayment_event['payload']['HanhViTraNo']}",
            ))

        if self.emit_cashflow_events:
            p = repayment_event["payload"]
            if p["SoTienGocDaTra"] > 0:
                events.append(self.gen.gen_cashflow_event(dt, store, "Thu nợ gốc", so_tien_thu=p["SoTienGocDaTra"], contract_no=loan.SoHopDong, employee_code=collector.get("MaNhanVien"), ghi_chu=f"Thu gốc HĐ {loan.SoHopDong}"))
            if p["SoTienLaiDaTra"] > 0:
                events.append(self.gen.gen_cashflow_event(dt, store, "Thu nợ lãi", so_tien_thu=p["SoTienLaiDaTra"], contract_no=loan.SoHopDong, employee_code=collector.get("MaNhanVien"), ghi_chu=f"Thu lãi HĐ {loan.SoHopDong}"))
            if p["PhiPhatTreHan"] > 0:
                events.append(self.gen.gen_cashflow_event(dt, store, "Thu phí phạt trễ hạn", so_tien_thu=p["PhiPhatTreHan"], contract_no=loan.SoHopDong, employee_code=collector.get("MaNhanVien"), ghi_chu=f"Thu phí phạt HĐ {loan.SoHopDong}"))

        # gỡ hợp đồng đã tất toán khỏi pool để pool không phình vô nghĩa
        if loan.DuNoConLai <= 0:
            loan.TrangThai = "Tất toán"

        return events

    def generate_for_minutes(self, start_dt: datetime, minutes: int = 1) -> list[dict]:
        all_events = []
        for i in range(minutes):
            dt = start_dt + timedelta(minutes=i)

            if dt.minute in (0, 20, 40):
                all_events.extend(self._refresh_weather(dt, sample_ratio=0.06))

            hourly = self._hourly_target(dt)
            per_minute_mean = hourly / 60.0
            contract_count = self.dist.poisson_count(per_minute_mean)

            selected = self._select_stores_for_hour(dt, contract_count)
            allocations = self._allocate_counts_to_stores(dt, contract_count, selected)

            stores_by_code = {s["MaCuaHang"]: s for s in self.stores}
            for code, n in allocations.items():
                store = stores_by_code.get(code)
                if not store:
                    continue
                for _ in range(n):
                    minute_dt = dt
                    all_events.extend(self.generate_contract_chain(minute_dt, store))

            repayment_count = self.dist.poisson_count(max(0.05, contract_count * self.payment_ratio))
            for _ in range(repayment_count):
                repay_dt = dt
                all_events.extend(self.generate_repayment_chain(repay_dt))

        # Phân loại: sự kiện tức thì gửi đi, sự kiện tương lai đưa vào buffer
        ready_events = []
        new_buffer = []
        for e in all_events:
            evt_time_str = e.get("event_time")
            if not evt_time_str:
                ready_events.append(e)
                continue
            try:
                evt_local = _parse_event_dt_hcm(evt_time_str)
                start_local = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
                if evt_local <= start_local:
                    ready_events.append(e)
                else:
                    new_buffer.append(e)
            except Exception:
                ready_events.append(e)

        self.event_buffer.extend(new_buffer)

        # Kiểm tra buffer xem có sự kiện nào đến hạn gửi chưa
        final_ready = []
        still_buffered = []
        start_local = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
        for e in self.event_buffer:
            try:
                evt_local = _parse_event_dt_hcm(e["event_time"])
                if evt_local <= start_local:
                    final_ready.append(e)
                else:
                    still_buffered.append(e)
            except Exception:
                final_ready.append(e)
        
        self.event_buffer = still_buffered
        return ready_events + final_ready

    def publish_events(self, events: list[dict]):
        if not events:
            return 0
        tuples = [self._topic_key(e) for e in events]
        self.producer.send_many(tuples, flush=True)
        max_buf = int(os.getenv("SIM_EVENT_BUFFER_MAX", "3000"))
        if len(self.event_buffer) > max_buf:
            self.event_buffer = self.event_buffer[-max_buf:]
        return len(events)


def clamp_future_event_time(events: list[dict], now_dt: datetime) -> None:
    now_local = now_dt.replace(tzinfo=None) if now_dt.tzinfo else now_dt
    for event in events:
        raw_time = event.get("event_time")
        if not raw_time:
            continue
        try:
            evt_local = _parse_event_dt_hcm(str(raw_time))
        except Exception:
            continue
        if evt_local > now_local:
            event["event_time"] = now_local.isoformat(timespec="seconds")


def classify_tier_from_index(idx: int) -> str:
    # Fallback deterministic tiers for mock store.
    r = idx % 100
    if r < 5:
        return "A+"
    if r < 20:
        return "A"
    if r < 55:
        return "B"
    if r < 90:
        return "C"
    return "D"


def build_mock_stores(dist: DistributionEngine, count: int = 100) -> list[dict]:
    regions = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bình Dương", "Đồng Nai", "Nha Trang", "Huế", "Thanh Hóa"]
    stores = []
    for i in range(count):
        code = f"CH{i+1:04d}"
        tier = classify_tier_from_index(i)
        region = regions[i % len(regions)]
        staff_min, staff_max = STAFF_COUNT[tier]
        n_staff = int(dist.rng.integers(staff_min, staff_max + 1))
        employees = []
        for j in range(n_staff):
            employees.append({
                "MaNhanVien": f"NV-{code}-{j+1:03d}",
                "TenNhanVien": fake.name(),
                "ChucVu": STAFF_ROLES[j % len(STAFF_ROLES)],
            })
        stores.append({
            "CuaHang_Key": i + 1,
            "MaCuaHang": code,
            "TenCuaHang": f"PGD {region} {i+1}",
            "KhuVuc": region,
            "TenKhuVuc": region,
            "DiaChi": fake.address(),
            "HangCuaHang": tier,
            "Tier": tier,
            "ToaDo_Key": i + 1,
            "lat": 21.02 if region == "Hà Nội" else (10.78 if region == "TP.HCM" else 16.05),
            "lng": 105.85 if region == "Hà Nội" else (106.70 if region == "TP.HCM" else 108.20),
            "TrafficHotness": float(dist.rng.lognormal(0, 0.45)),
            "employees": employees,
        })
    return stores


def load_stores_from_db(dist: DistributionEngine, count: int = 800) -> list[dict]:
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                ch.CuaHang_Key,
                ch.MaCuaHang,
                ch.TenCuaHang,
                ch.KhuVuc,
                ch.DiaChi,
                ch.ToaDo_Key,
                COALESCE(ch.HangCuaHang, '') AS HangCuaHang,
                td.Vido_Latitude,
                td.Kinhdo_Longitude,
                td.TenKhuVuc
            FROM Dim_CuaHang ch
            LEFT JOIN Dim_ToaDo td ON ch.ToaDo_Key = td.ToaDo_Key
            ORDER BY RANDOM()
            LIMIT %s
            """,
            (count,),
        )
        rows = cur.fetchall()

        # Load employees if table exists and has CuaHang_Key.
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'dim_nhanvien'
            )
            """
        )
        has_emp = bool(cur.fetchone()[0])
        emp_by_store = {}
        if has_emp:
            try:
                cur.execute(
                    """
                    SELECT MaNhanVien, TenNhanVien, ChucVu, CuaHang_Key
                    FROM Dim_NhanVien
                    WHERE CuaHang_Key IS NOT NULL
                    """
                )
                for ma, ten, role, ch_key in cur.fetchall():
                    emp_by_store.setdefault(ch_key, []).append({
                        "MaNhanVien": ma,
                        "TenNhanVien": ten,
                        "ChucVu": role or "Giao dịch viên",
                    })
            except Exception:
                emp_by_store = {}

        conn.close()
    except Exception as e:
        logger.warning("Cannot load stores from DB, fallback mock stores: %s", e)
        return []

    stores = []
    for idx, row in enumerate(rows):
        (
            key, ma, ten, kv, diachi, td_key, hang, lat, lng, ten_kv
        ) = row
        tier = hang or classify_tier_from_index(idx)
        employees = emp_by_store.get(key) or []
        if not employees:
            staff_min, staff_max = STAFF_COUNT.get(tier, (2, 4))
            n_staff = int(dist.rng.integers(staff_min, staff_max + 1))
            employees = [
                {
                    "MaNhanVien": f"NV-{ma}-{j+1:03d}",
                    "TenNhanVien": fake.name(),
                    "ChucVu": STAFF_ROLES[j % len(STAFF_ROLES)],
                }
                for j in range(n_staff)
            ]

        stores.append({
            "CuaHang_Key": key,
            "MaCuaHang": ma,
            "TenCuaHang": ten,
            "KhuVuc": kv or ten_kv,
            "TenKhuVuc": ten_kv or kv,
            "DiaChi": diachi,
            "HangCuaHang": tier,
            "Tier": tier,
            "ToaDo_Key": td_key,
            "lat": float(lat) if lat is not None else None,
            "lng": float(lng) if lng is not None else None,
            "TrafficHotness": float(dist.rng.lognormal(0, 0.50)),
            "employees": employees,
        })

    return stores


def run_realtime(args):
    dist = DistributionEngine(seed=args.seed)
    gen = EventGenerator(dist)
    producer = EventProducer(bootstrap_servers=args.kafka)
    producer.connect()

    stores = load_stores_from_db(dist, min(args.stores, 800))
    if not stores:
        stores = build_mock_stores(dist, min(args.stores, 800))
    logger.info("Loaded %s stores", len(stores))

    sim = BusinessSimulator(
        dist, gen, producer, stores,
        daily_min=args.daily_min,
        daily_max=args.daily_max,
        hourly_min=args.hourly_min,
        hourly_max=args.hourly_max,
        payment_ratio=args.payment_ratio,
        emit_cashflow_events=args.emit_cashflow_events,
    )
    logger.info("Realtime target daily contracts: %s", sim.daily_target)

    try:
        while True:
            current = sim_now()
            events = sim.generate_for_minutes(current, args.sim_minutes_per_tick)
            sent = sim.publish_events(events)
            logger.info("tick=%s events=%s active_loans=%s buffer=%s", current.strftime("%Y-%m-%d %H:%M"), sent, len(sim.active_loans), len(sim.event_buffer))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Simulator stopped")
    finally:
        producer.close()


def run_batch(args):
    dist = DistributionEngine(seed=args.seed)
    gen = EventGenerator(dist)
    producer = EventProducer(bootstrap_servers=args.kafka)
    producer.connect()

    stores = load_stores_from_db(dist, min(args.stores, 800))
    if not stores:
        stores = build_mock_stores(dist, min(args.stores, 800))
    logger.info("Loaded %s stores", len(stores))

    sim = BusinessSimulator(
        dist, gen, producer, stores,
        daily_min=args.daily_min,
        daily_max=args.daily_max,
        hourly_min=args.hourly_min,
        hourly_max=args.hourly_max,
        payment_ratio=args.payment_ratio,
        emit_cashflow_events=args.emit_cashflow_events,
    )

    start_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    grand_total = 0
    for d in range(args.days):
        day = start_date + timedelta(days=d)
        for h in ACTIVE_HOURS:
            dt = day.replace(hour=h, minute=0, second=0)
            # Sinh đủ một giờ nghiệp vụ.
            events = sim.generate_for_minutes(dt, 60)
            grand_total += sim.publish_events(events)
        logger.info("Batch day=%s sent_events=%s active_loans=%s", day.strftime("%Y-%m-%d"), grand_total, len(sim.active_loans))

    logger.info("DONE batch total events=%s", grand_total)
    producer.close()


def main():
    parser = argparse.ArgumentParser(description="F88 Kafka Business Simulator")
    parser.add_argument("--mode", choices=["realtime", "batch"], default="realtime")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--stores", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--kafka", type=str, default=None)

    parser.add_argument("--daily-min", type=int, default=DEFAULT_DAILY_MIN)
    parser.add_argument("--daily-max", type=int, default=DEFAULT_DAILY_MAX)
    parser.add_argument("--hourly-min", type=int, default=DEFAULT_HOURLY_MIN)
    parser.add_argument("--hourly-max", type=int, default=DEFAULT_HOURLY_MAX)
    parser.add_argument("--payment-ratio", type=float, default=DEFAULT_PAYMENT_RATIO)

    parser.add_argument("--interval", type=float, default=1.0, help="Số giây thật giữa mỗi tick realtime")
    parser.add_argument("--sim-minutes-per-tick", type=int, default=1, help="Số phút nghiệp vụ mỗi tick realtime")
    parser.add_argument("--emit-cashflow-events", action="store_true", help="Bật nếu muốn phát cashflow.events riêng. Mặc định tắt để tránh double count với FastAPI hiện tại.")

    args = parser.parse_args()

    if args.mode == "batch":
        run_batch(args)
    else:
        run_realtime(args)


if __name__ == "__main__":
    main()
