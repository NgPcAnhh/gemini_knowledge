"""
simulator/generators.py

Sinh event nghiệp vụ theo cấu trúc thống nhất:
{
  event_id, event_type, event_time, payload
}
"""

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from faker import Faker

from simulator.config import (
    LOAN_TYPE_REPAYMENT,
    CUSTOMER_TYPE_WEIGHTS,
    OCCUPATIONS,
    OCCUPATION_WEIGHTS,
    INCOME_BY_OCCUPATION,
    POST_APPROVAL_BEHAVIOR,
)
from simulator.distributions import DistributionEngine

fake = Faker("vi_VN")


@dataclass
class ActiveLoan:
    SoHopDong: str
    CMND_CCCD: str
    MaCuaHang: str
    CuaHang_Key: int | None
    ToaDo_Key: int | None
    KhuVuc: str
    TenKhuVuc: str | None
    MaNhanVien: str | None
    TenLoaiHinh: str
    HinhThucTraNo: str
    SoTienGiaiNgan: float
    DuNoConLai: float
    LaiSuat: float
    ThoiHanVay_Thang: int
    KyTraNo_Thang: int
    SoTienTraMoiKy: float
    DiemTinDung: int
    ThuNhapHangThang: float
    IsShipper: bool
    WeatherRisk: str
    NgayGiaiNgan: str
    NgayDaoHan: str
    KyThanhToanHienTai: int = 0
    TrangThai: str = "Đang lưu hành"


class EventGenerator:
    def __init__(self, dist_engine: DistributionEngine):
        self.dist = dist_engine
        self._contract_counter = 0

    def _event_id(self) -> str:
        return str(uuid.uuid4())

    def _base_event(self, event_type: str, event_time: datetime, payload: dict) -> dict:
        return {
            "event_id": self._event_id(),
            "event_type": event_type,
            "event_time": event_time.isoformat(),
            "payload": payload,
        }

    def _contract_no(self, store_code: str, event_time: datetime) -> str:
        self._contract_counter += 1
        rand = uuid.uuid4().hex[:4].upper()
        return f"HD-{store_code}-{event_time.strftime('%Y%m%d')}-{self._contract_counter:07d}-{rand}"

    def choose_employee(self, store: dict, roles: tuple[str, ...] | None = None) -> dict:
        employees = store.get("employees") or []
        if roles:
            filtered = [e for e in employees if e.get("ChucVu") in roles]
            if filtered:
                return self.dist.weighted_choice(filtered, [1.0] * len(filtered))
        if employees:
            return self.dist.weighted_choice(employees, [1.0] * len(employees))
        code = store.get("MaCuaHang", "CH0000")
        return {"MaNhanVien": f"NV-{code}-001", "TenNhanVien": "Nhân viên hệ thống", "ChucVu": "Giao dịch viên"}

    def gen_customer_event(self, event_time: datetime, store: dict, weather_risk: str = "low") -> dict:
        occupations = list(OCCUPATION_WEIGHTS.keys())
        weights = list(OCCUPATION_WEIGHTS.values())

        # Khi mưa, nhóm shipper có xác suất phát sinh nhu cầu cao hơn.
        if weather_risk in ("medium", "high"):
            weights = [w * (1.25 if occ == "Tài xế công nghệ/shipper" else 1.0) for occ, w in zip(occupations, weights)]

        occupation = self.dist.weighted_choice(occupations, weights)
        income = self.dist.gen_income(*INCOME_BY_OCCUPATION[occupation])
        credit_score = self.dist.gen_credit_score()
        dependents = int(self.dist.rng.choice([0, 0, 0, 1, 1, 2, 2, 3, 4]))
        customer_type = self.dist.weighted_choice(list(CUSTOMER_TYPE_WEIGHTS.keys()), list(CUSTOMER_TYPE_WEIGHTS.values()))
        is_shipper = occupation == "Tài xế công nghệ/shipper"

        return self._base_event("customer_created", event_time, {
            "TenKhachHang": fake.name(),
            "SoDienThoai": fake.phone_number(),
            "CMND_CCCD": fake.ssn()[:12],
            "NgheNghiep": occupation,
            "PhanKhuc": "App Driver" if is_shipper else "Mass",
            "IsShipper": is_shipper,
            "CustomerType": customer_type,
            "ThuNhapHangThang": income,
            "DiemTinDung": credit_score,
            "SoNguoiPhuThuoc": dependents,
            "DiaChi": f"{fake.street_address()}, {store.get('KhuVuc', '')}",
            "MaCuaHangGanNhat": store.get("MaCuaHang"),
            "CuaHang_Key": store.get("CuaHang_Key"),
            "ToaDo_Key": store.get("ToaDo_Key"),
        })

    def gen_asset_event(self, event_time: datetime, customer_cmnd: str, loan_type: str, loan_amount_vnd: float) -> dict:
        asset_value = self.dist.gen_asset_value(loan_amount_vnd, loan_type)
        asset_type_map = {
            "Cầm đồ Xe máy (Giữ Cà vẹt)": "Xe máy",
            "Cầm đồ Xe máy (Giữ xe)": "Xe máy",
            "Cầm đồ Điện thoại/Laptop": "Điện thoại/Laptop",
            "Cầm đồ Ô tô (Giữ đăng ký)": "Ô tô",
            "Cầm đồ Ô tô (Giữ xe)": "Ô tô",
            "Vay tín chấp (Theo lương)": "Không có tài sản đảm bảo",
            "Vay tín chấp (Hộ kinh doanh)": "Không có tài sản đảm bảo",
            "Cầm đồ Bất động sản/Sổ đỏ": "Bất động sản",
        }
        asset_type = asset_type_map.get(loan_type, "Khác")
        condition = self.dist.weighted_choice(["Tốt", "Khá", "Trung bình", "Cũ", "Cần kiểm tra"], [0.32, 0.30, 0.22, 0.12, 0.04])

        return self._base_event("asset_appraised", event_time, {
            "CMND_CCCD": customer_cmnd,
            "LoaiTaiSan": asset_type,
            "MoTaChiTiet": f"{asset_type} - {fake.text(max_nb_chars=48)}",
            "GiaTriDinhGia": asset_value,
            "TinhTrangBanDau": condition,
            "DuongDanAnh": f"/images/assets/{uuid.uuid4().hex[:10]}.jpg",
        })

    def gen_application_event(
        self,
        event_time: datetime,
        customer_cmnd: str,
        store: dict,
        employee_code: str,
        loan_type: str,
        loan_amount_vnd: float,
    ) -> dict:
        contract_no = self._contract_no(store.get("MaCuaHang", "CH0000"), event_time)
        return self._base_event("loan_application_created", event_time, {
            "SoHopDong": contract_no,
            "CMND_CCCD": customer_cmnd,
            "MaCuaHang": store.get("MaCuaHang"),
            "CuaHang_Key": store.get("CuaHang_Key"),
            "ToaDo_Key": store.get("ToaDo_Key"),
            "KhuVuc": store.get("KhuVuc"),
            "TenKhuVuc": store.get("TenKhuVuc"),
            "MaNhanVienSale": employee_code,
            "TenLoaiHinh": loan_type,
            "HinhThucTraNo": LOAN_TYPE_REPAYMENT[loan_type],
            "SoTienMongMuon": loan_amount_vnd,
            "TrangThai": "Chờ tiếp nhận",
        })

    def gen_decision_event(
        self,
        event_time: datetime,
        contract_no: str,
        customer_payload: dict,
        loan_amount_vnd: float,
        asset_value_vnd: float,
        loan_type: str,
        approver_code: str,
        weather_risk: str = "low",
    ) -> dict:
        credit_score = int(customer_payload.get("DiemTinDung", 600))
        income = float(customer_payload.get("ThuNhapHangThang", 10_000_000))
        is_returning = customer_payload.get("CustomerType") == "returning"
        is_shipper = bool(customer_payload.get("IsShipper"))

        term = self.dist.gen_loan_term(loan_type)
        interest_rate = self.dist.gen_interest_rate(loan_type)
        estimated_monthly = loan_amount_vnd / max(term, 1) + loan_amount_vnd * (interest_rate / 100)
        dti = estimated_monthly / max(income, 1)
        ltv = loan_amount_vnd / max(asset_value_vnd, 1) if asset_value_vnd > 0 else 0.0

        approval_prob = self.dist.calc_approval_probability(
            credit_score=credit_score,
            dti=dti,
            ltv=ltv,
            loan_type=loan_type,
            is_returning_customer=is_returning,
            weather_risk=weather_risk,
            is_shipper=is_shipper,
        )
        approved = self.dist.decide_approval(approval_prob)

        if not approved:
            reason = self.dist.weighted_choice(
                ["DTI quá cao", "LTV vượt ngưỡng", "Điểm tín dụng thấp", "Tài sản không đủ điều kiện", "Thiếu giấy tờ", "Thu nhập không ổn định"],
                [0.25, 0.20, 0.20, 0.12, 0.10, 0.13],
            )
            return self._base_event("loan_rejected", event_time, {
                "SoHopDong": contract_no,
                "LyDoTuChoi": reason,
                "ApprovalProbability": round(approval_prob, 4),
                "TrangThai": "Từ chối",
            })

        adjust_factor = float(self.dist.rng.uniform(0.84, 1.00))
        approved_amount = round(loan_amount_vnd * adjust_factor, -3)

        monthly_rate = interest_rate / 100
        repayment_type = LOAN_TYPE_REPAYMENT[loan_type]
        if repayment_type == "Gốc lãi trả đều" and monthly_rate > 0:
            payment = approved_amount * monthly_rate * (1 + monthly_rate) ** term / ((1 + monthly_rate) ** term - 1)
        elif repayment_type == "Trả góp linh hoạt":
            payment = approved_amount / max(term, 1) + approved_amount * monthly_rate
        else:
            payment = approved_amount * monthly_rate

        return self._base_event("loan_approved", event_time, {
            "SoHopDong": contract_no,
            "MaNguoiDuyet": approver_code,
            "NgayDuyet": event_time.strftime("%Y%m%d"),
            "SoTienDuyetVay": approved_amount,
            "TenLoaiTaiSan": loan_type,
            "LoaiTaiSan": loan_type,
            "TenLoaiHinh": loan_type,
            "LaiSuat": interest_rate,
            "PhiPhatTraTruoc": round(approved_amount * 0.01, 0),
            "ThoiHanVay_Thang": term,
            "KyTraNo_Thang": 1,
            "SoTienTraMoiKy": round(payment, 0),
            "ApprovalProbability": round(approval_prob, 4),
            "TrangThai": "Đã duyệt",
        })

    def gen_disbursement_event(
        self,
        event_time: datetime,
        contract_no: str,
        store: dict,
        approved_amount: float,
        term_months: int,
        employee_code: str,
        loan_type: str = "",
    ) -> dict:
        method = self.dist.weighted_choice(["Tiền mặt", "Chuyển khoản"], [0.52, 0.48])
        maturity_date = event_time + timedelta(days=term_months * 30)
        return self._base_event("loan_disbursed", event_time, {
            "SoHopDong": contract_no,
            "MaCuaHang": store.get("MaCuaHang"),
            "CuaHang_Key": store.get("CuaHang_Key"),
            "ToaDo_Key": store.get("ToaDo_Key"),
            "KhuVuc": store.get("KhuVuc"),
            "TenKhuVuc": store.get("TenKhuVuc"),
            "MaNhanVien": employee_code,
            "SoTienGiaiNgan": approved_amount,
            "DuNoGocBanDau": approved_amount,
            "DuNoConLai": approved_amount,
            "TenLoaiHinh": loan_type,
            "NgayGiaiNgan": event_time.strftime("%Y%m%d"),
            "NgayDaoHan": maturity_date.strftime("%Y%m%d"),
            "PhuongThuc": method,
            "ChungTuGoc": f"GN-{contract_no}",
            "TrangThai": "Đã giải ngân",
        })

    def gen_cashflow_event(
        self,
        event_time: datetime,
        store: dict,
        ten_loai_thu_chi: str,
        so_tien_thu: float = 0,
        so_tien_chi: float = 0,
        contract_no: str | None = None,
        employee_code: str | None = None,
        phuong_thuc: str = "Tiền mặt",
        ghi_chu: str = "",
    ) -> dict:
        return self._base_event("cash_recorded", event_time, {
            "MaCuaHang": store.get("MaCuaHang"),
            "CuaHang_Key": store.get("CuaHang_Key"),
            "ToaDo_Key": store.get("ToaDo_Key"),
            "TenLoaiThuChi": ten_loai_thu_chi,
            "SoTienThu": so_tien_thu,
            "SoTienChi": so_tien_chi,
            "SoHopDong": contract_no,
            "PhuongThuc": phuong_thuc,
            "NguoiThucHien": employee_code,
            "ChungTuGoc": f"CT-{uuid.uuid4().hex[:8].upper()}",
            "GhiChu": ghi_chu,
        })

    def build_active_loan(
        self,
        app_event: dict,
        decision_event: dict,
        disb_event: dict,
        customer_event: dict,
    ) -> ActiveLoan:
        p_app = app_event["payload"]
        p_dec = decision_event["payload"]
        p_disb = disb_event["payload"]
        return ActiveLoan(
            SoHopDong=p_app["SoHopDong"],
            CMND_CCCD=p_app["CMND_CCCD"],
            MaCuaHang=p_app["MaCuaHang"],
            CuaHang_Key=p_app.get("CuaHang_Key"),
            ToaDo_Key=p_app.get("ToaDo_Key"),
            KhuVuc=p_app.get("KhuVuc"),
            TenKhuVuc=p_app.get("TenKhuVuc"),
            MaNhanVien=p_disb.get("MaNhanVien"),
            TenLoaiHinh=p_app["TenLoaiHinh"],
            HinhThucTraNo=p_app["HinhThucTraNo"],
            SoTienGiaiNgan=float(p_disb["SoTienGiaiNgan"]),
            DuNoConLai=float(p_disb["DuNoConLai"]),
            LaiSuat=float(p_dec["LaiSuat"]),
            ThoiHanVay_Thang=int(p_dec["ThoiHanVay_Thang"]),
            KyTraNo_Thang=int(p_dec.get("KyTraNo_Thang", 1)),
            SoTienTraMoiKy=float(p_dec["SoTienTraMoiKy"]),
            DiemTinDung=int(customer_event["payload"].get("DiemTinDung", 600)),
            ThuNhapHangThang=float(customer_event["payload"].get("ThuNhapHangThang", 10_000_000)),
            IsShipper=bool(customer_event["payload"].get("IsShipper")),
            WeatherRisk=customer_event["payload"].get("WeatherRisk", "low"),
            NgayGiaiNgan=p_disb["NgayGiaiNgan"],
            NgayDaoHan=p_disb["NgayDaoHan"],
        )

    def gen_repayment_event(self, event_time: datetime, loan: ActiveLoan, store: dict, collector_code: str, weather_risk: str = "low") -> dict:
        loan.KyThanhToanHienTai += 1
        principal_due = min(loan.DuNoConLai, max(0, loan.SoTienGiaiNgan / max(loan.ThoiHanVay_Thang, 1)))
        interest_due = round(loan.DuNoConLai * (loan.LaiSuat / 100), 0)
        dti = (principal_due + interest_due) / max(loan.ThuNhapHangThang, 1)

        behavior = self.dist.gen_repayment_behavior(
            credit_score=loan.DiemTinDung,
            dti=dti,
            is_shipper=loan.IsShipper,
            weather_risk=weather_risk,
        )

        actual_principal = principal_due
        actual_interest = interest_due
        late_fee = 0.0

        if behavior == "partial":
            actual_principal = round(principal_due * float(self.dist.rng.uniform(0.25, 0.72)), 0)
        elif behavior in ("late_1_10", "late_11_30", "late_30_plus"):
            late_days = {"late_1_10": 5, "late_11_30": 20, "late_30_plus": 45}[behavior]
            late_fee = round(max(loan.DuNoConLai, 0) * 0.0006 * late_days, 0)
        elif behavior == "bad_debt":
            actual_principal = 0.0
            actual_interest = 0.0

        before = loan.DuNoConLai
        after = max(0.0, before - actual_principal)
        loan.DuNoConLai = after

        if behavior in ("late_1_10", "partial"):
            new_status = "Quá hạn nhẹ"
        elif behavior in ("late_11_30", "late_30_plus"):
            new_status = "Quá hạn"
        elif behavior == "bad_debt":
            new_status = "Nợ xấu"
        elif after <= 0:
            new_status = "Tất toán"
        else:
            new_status = "Đang lưu hành"
        loan.TrangThai = new_status

        return self._base_event("repayment_paid", event_time, {
            "SoHopDong": loan.SoHopDong,
            "MaCuaHang": loan.MaCuaHang,
            "CuaHang_Key": loan.CuaHang_Key,
            "ToaDo_Key": loan.ToaDo_Key,
            "KhuVuc": loan.KhuVuc,
            "TenKhuVuc": loan.TenKhuVuc,
            "CMND_CCCD": loan.CMND_CCCD,
            "MaNhanVien": collector_code,
            "NgayThanhToan": event_time.strftime("%Y%m%d"),
            "SoTienGocDaTra": round(actual_principal, 0),
            "SoTienLaiDaTra": round(actual_interest, 0),
            "PhiPhatTreHan": round(late_fee, 0),
            "TenLoaiHinh": loan.TenLoaiHinh,
            "SoDuGocTruocThanhToan": round(before, 0),
            "SoDuGocSauThanhToan": round(after, 0),
            "DuNoConLai": round(after, 0),
            "KyThanhToan": loan.KyThanhToanHienTai,
            "HinhThucTraNo": loan.HinhThucTraNo,
            "HanhViTraNo": behavior,
            "TrangThaiSauThanhToan": new_status,
            "ChungTuGoc": f"PT-{uuid.uuid4().hex[:8].upper()}",
            "GhiChu": f"Thanh toán kỳ {loan.KyThanhToanHienTai} - {behavior}",
        })

    def gen_status_event(self, event_time: datetime, loan: ActiveLoan, old_status: str, new_status: str, employee_code: str, reason: str) -> dict:
        return self._base_event("loan_status_changed", event_time, {
            "SoHopDong": loan.SoHopDong,
            "TrangThaiCu": old_status,
            "TrangThaiMoi": new_status,
            "LyDo": reason,
            "MaNhanVien": employee_code,
            "NgayThayDoi": event_time.strftime("%Y%m%d"),
            "TenLoaiHinh": loan.TenLoaiHinh,
            "DuNoConLai": round(loan.DuNoConLai, 0),
        })

    def gen_weather_event(self, event_time: datetime, store: dict, weather: dict) -> dict:
        return self._base_event("weather_updated", event_time, {
            "MaCuaHang": store.get("MaCuaHang"),
            "CuaHang_Key": store.get("CuaHang_Key"),
            "ToaDo_Key": store.get("ToaDo_Key"),
            "TenKhuVuc": store.get("TenKhuVuc") or store.get("KhuVuc"),
            "KhuVuc": store.get("KhuVuc"),
            "lat": store.get("lat"),
            "lng": store.get("lng"),
            **weather,
        })
