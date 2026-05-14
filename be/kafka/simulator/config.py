"""
simulator/config.py

Cấu hình nghiệp vụ cho luồng mô phỏng F88 realtime:

Fake Data Simulator -> Kafka -> Consumer -> PostgreSQL + Redis -> FastAPI -> WebSocket -> Dashboard

Nguyên tắc:
- Hợp đồng phát sinh khi khách thỏa thuận vay/cầm đồ.
- Khách trả tiền phát sinh event repayment riêng từ danh sách hợp đồng đang lưu hành.
- Không chia đều cứng cho mọi chi nhánh. Chi nhánh được chọn theo trọng số khu vực, hạng cửa hàng,
  độ nóng ngẫu nhiên và thời tiết.
- Volume mục tiêu mặc định: 1.000 - 5.000 hợp đồng/ngày, 50 - 300 hợp đồng/giờ.
"""

import os

# ============================================================
# KAFKA
# ============================================================
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

KAFKA_TOPICS = {
    "customer": "customer.events",
    "asset": "asset.events",
    "loan_application": "loan.application.events",
    "loan_decision": "loan.decision.events",
    "loan_disbursement": "loan.disbursement.events",
    "loan_repayment": "loan.repayment.events",
    "loan_status": "loan.status.events",
    "cashflow": "cashflow.events",
    "weather": "weather.events",
    "opex": "opex.events",
    "payroll": "payroll.events",
    "depreciation": "depreciation.events",
}

# Topic tổng hợp optional để debug/replay.
BUSINESS_TOPIC = os.getenv("BUSINESS_TOPIC", "f88.business.events")
PUBLISH_BUSINESS_TOPIC = os.getenv("PUBLISH_BUSINESS_TOPIC", "0") == "1"

# ============================================================
# POSTGRESQL
# ============================================================
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "dbname": os.getenv("PG_DB", "credit_control"),
    "user": os.getenv("PG_USER", "admin"),
    "password": os.getenv("PG_PASSWORD", "123456"),
}

# ============================================================
# VOLUME BUSINESS
# ============================================================
DEFAULT_DAILY_MIN = int(os.getenv("DAILY_MIN", "1000"))
DEFAULT_DAILY_MAX = int(os.getenv("DAILY_MAX", "3000"))
DEFAULT_HOURLY_MIN = int(os.getenv("HOURLY_MIN", "20"))
DEFAULT_HOURLY_MAX = int(os.getenv("HOURLY_MAX", "120"))

ACTIVE_HOURS = list(range(8, 22))

# ============================================================
# PHÂN HẠNG CỬA HÀNG
# ============================================================
STORE_TIERS = {
    "A+": {"ratio": 0.05, "count": 40},
    "A": {"ratio": 0.15, "count": 120},
    "B": {"ratio": 0.35, "count": 280},
    "C": {"ratio": 0.35, "count": 280},
    "D": {"ratio": 0.10, "count": 80},
}

TIER_WEIGHT = {
    "A+": 8.0,
    "A": 5.0,
    "B": 2.6,
    "C": 1.2,
    "D": 0.35,
}

AREA_WEIGHT = {
    "Hà Nội": 1.45,
    "TP.HCM": 1.55,
    "TP. Hồ Chí Minh": 1.55,
    "Đà Nẵng": 1.18,
    "Hải Phòng": 1.08,
    "Cần Thơ": 1.08,
    "Biên Hòa": 1.05,
    "Bình Dương": 1.10,
    "Đồng Nai": 1.05,
    "Nha Trang": 0.95,
    "Huế": 0.90,
    "Vũng Tàu": 0.95,
    "default": 0.72,
}

# Hệ số theo giờ. Cao điểm sáng/chiều.
HOUR_FACTOR = {
    8: 0.75,
    9: 1.05,
    10: 1.15,
    11: 1.05,
    12: 0.70,
    13: 0.85,
    14: 1.20,
    15: 1.25,
    16: 1.25,
    17: 1.20,
    18: 1.05,
    19: 0.85,
    20: 0.65,
    21: 0.45,
}

WEEKDAY_FACTOR = {
    0: 1.10,
    1: 1.00,
    2: 1.00,
    3: 1.05,
    4: 1.15,
    5: 1.18,
    6: 0.65,
}

# ============================================================
# LOẠI HÌNH VAY - dùng tên đã chuẩn hóa để khớp Dim_LoaiHinh seed
# ============================================================
LOAN_TYPE_WEIGHTS = {
    "Cầm đồ Xe máy (Giữ Cà vẹt)": 0.36,
    "Cầm đồ Xe máy (Giữ xe)": 0.22,
    "Cầm đồ Điện thoại/Laptop": 0.14,
    "Cầm đồ Ô tô (Giữ đăng ký)": 0.06,
    "Cầm đồ Ô tô (Giữ xe)": 0.04,
    "Vay tín chấp (Theo lương)": 0.10,
    "Vay tín chấp (Hộ kinh doanh)": 0.06,
    "Cầm đồ Bất động sản/Sổ đỏ": 0.02,
}

LOAN_TYPE_REPAYMENT = {
    "Cầm đồ Xe máy (Giữ Cà vẹt)": "Gốc lãi trả đều",
    "Cầm đồ Xe máy (Giữ xe)": "Gốc cuối kỳ, lãi hàng tháng",
    "Cầm đồ Điện thoại/Laptop": "Gốc cuối kỳ, lãi hàng tháng",
    "Cầm đồ Ô tô (Giữ đăng ký)": "Gốc lãi trả đều",
    "Cầm đồ Ô tô (Giữ xe)": "Gốc cuối kỳ, lãi hàng tháng",
    "Vay tín chấp (Theo lương)": "Gốc lãi trả đều",
    "Vay tín chấp (Hộ kinh doanh)": "Trả góp linh hoạt",
    "Cầm đồ Bất động sản/Sổ đỏ": "Gốc cuối kỳ, lãi hàng tháng",
}

# Đơn vị triệu VND.
LOAN_AMOUNT_RANGE = {
    "Cầm đồ Xe máy (Giữ Cà vẹt)": (8, 70),
    "Cầm đồ Xe máy (Giữ xe)": (5, 50),
    "Cầm đồ Điện thoại/Laptop": (2, 20),
    "Cầm đồ Ô tô (Giữ đăng ký)": (100, 900),
    "Cầm đồ Ô tô (Giữ xe)": (80, 700),
    "Vay tín chấp (Theo lương)": (5, 80),
    "Vay tín chấp (Hộ kinh doanh)": (10, 150),
    "Cầm đồ Bất động sản/Sổ đỏ": (200, 2000),
}

INTEREST_RATE_RANGE = {
    "Cầm đồ Xe máy (Giữ Cà vẹt)": (1.5, 3.0),
    "Cầm đồ Xe máy (Giữ xe)": (2.0, 4.0),
    "Cầm đồ Điện thoại/Laptop": (2.5, 5.0),
    "Cầm đồ Ô tô (Giữ đăng ký)": (1.2, 2.5),
    "Cầm đồ Ô tô (Giữ xe)": (1.5, 3.0),
    "Vay tín chấp (Theo lương)": (2.0, 4.5),
    "Vay tín chấp (Hộ kinh doanh)": (2.5, 5.0),
    "Cầm đồ Bất động sản/Sổ đỏ": (1.0, 2.0),
}

LOAN_TERM_OPTIONS = {
    "Cầm đồ Xe máy (Giữ Cà vẹt)": [3, 6, 9, 12],
    "Cầm đồ Xe máy (Giữ xe)": [1, 2, 3, 6],
    "Cầm đồ Điện thoại/Laptop": [1, 2, 3],
    "Cầm đồ Ô tô (Giữ đăng ký)": [6, 12, 18, 24],
    "Cầm đồ Ô tô (Giữ xe)": [1, 3, 6, 12],
    "Vay tín chấp (Theo lương)": [6, 12, 18, 24],
    "Vay tín chấp (Hộ kinh doanh)": [6, 12, 18],
    "Cầm đồ Bất động sản/Sổ đỏ": [6, 12, 24, 36],
}

# ============================================================
# KHÁCH HÀNG / SHIPPER
# ============================================================
OCCUPATIONS = [
    "Tài xế công nghệ/shipper",
    "Công nhân",
    "Nhân viên văn phòng",
    "Kinh doanh tự do",
    "Hộ kinh doanh",
    "Nội trợ",
    "Sinh viên",
    "Giáo viên",
    "Bác sĩ/Y tá",
]

OCCUPATION_WEIGHTS = {
    "Tài xế công nghệ/shipper": 0.38,
    "Công nhân": 0.16,
    "Nhân viên văn phòng": 0.12,
    "Kinh doanh tự do": 0.12,
    "Hộ kinh doanh": 0.08,
    "Nội trợ": 0.04,
    "Sinh viên": 0.06,
    "Giáo viên": 0.02,
    "Bác sĩ/Y tá": 0.02,
}

INCOME_BY_OCCUPATION = {
    "Tài xế công nghệ/shipper": (7, 18),
    "Công nhân": (5, 12),
    "Nhân viên văn phòng": (8, 25),
    "Kinh doanh tự do": (5, 50),
    "Hộ kinh doanh": (10, 80),
    "Nội trợ": (0, 5),
    "Sinh viên": (0, 5),
    "Giáo viên": (6, 15),
    "Bác sĩ/Y tá": (10, 35),
}

CUSTOMER_TYPE_WEIGHTS = {
    "new": 0.60,
    "returning": 0.29,
    "referred": 0.08,
    "prev_overdue": 0.03,
}

POST_APPROVAL_BEHAVIOR = {
    "same_day": 0.76,
    "next_day": 0.12,
    "cancelled": 0.08,
    "suspended": 0.04,
}

REPAYMENT_BEHAVIOR = {
    "on_time": (0.70, 0.82),
    "early": (0.04, 0.09),
    "partial": (0.04, 0.09),
    "late_1_10": (0.06, 0.13),
    "late_11_30": (0.02, 0.06),
    "late_30_plus": (0.01, 0.03),
    "bad_debt": (0.002, 0.012),
}

# Tần suất thanh toán so với hợp đồng phát sinh.
DEFAULT_PAYMENT_RATIO = float(os.getenv("PAYMENT_RATIO", "0.55"))

# ============================================================
# DIM TRẠNG THÁI / LOẠI THU CHI
# ============================================================
LOAN_STATUSES = [
    {"TrangThaiKhoanVay": "Chờ tiếp nhận", "NhomNo": None},
    {"TrangThaiKhoanVay": "Chờ định giá", "NhomNo": None},
    {"TrangThaiKhoanVay": "Đang thẩm định", "NhomNo": None},
    {"TrangThaiKhoanVay": "Chờ duyệt", "NhomNo": None},
    {"TrangThaiKhoanVay": "Đã duyệt", "NhomNo": None},
    {"TrangThaiKhoanVay": "Từ chối", "NhomNo": None},
    {"TrangThaiKhoanVay": "Khách hủy", "NhomNo": None},
    {"TrangThaiKhoanVay": "Đã giải ngân", "NhomNo": None},
    {"TrangThaiKhoanVay": "Đang lưu hành", "NhomNo": "Nợ tiêu chuẩn"},
    {"TrangThaiKhoanVay": "Quá hạn nhẹ", "NhomNo": "Nợ cần chú ý"},
    {"TrangThaiKhoanVay": "Quá hạn", "NhomNo": "Nợ cần chú ý"},
    {"TrangThaiKhoanVay": "Nợ nghi ngờ", "NhomNo": "Nợ nghi ngờ"},
    {"TrangThaiKhoanVay": "Nợ xấu", "NhomNo": "Nợ xấu"},
    {"TrangThaiKhoanVay": "Thanh lý tài sản", "NhomNo": "Xử lý nợ"},
    {"TrangThaiKhoanVay": "Tất toán", "NhomNo": None},
    {"TrangThaiKhoanVay": "Tất toán trước hạn", "NhomNo": None},
]

CASHFLOW_TYPES = [
    {"TenLoaiThuChi": "Giải ngân tiền mặt", "NhomThuChi": "Chi"},
    {"TenLoaiThuChi": "Giải ngân chuyển khoản", "NhomThuChi": "Chi"},
    {"TenLoaiThuChi": "Thu nợ gốc", "NhomThuChi": "Thu"},
    {"TenLoaiThuChi": "Thu nợ lãi", "NhomThuChi": "Thu"},
    {"TenLoaiThuChi": "Thu phí phạt trễ hạn", "NhomThuChi": "Thu"},
]

STAFF_COUNT = {
    "A+": (8, 15),
    "A": (5, 10),
    "B": (3, 6),
    "C": (2, 4),
    "D": (1, 3),
}

STAFF_ROLES = [
    "Cửa hàng trưởng",
    "Giao dịch viên",
    "Nhân viên thẩm định",
    "Nhân viên thu hồi nợ",
    "Nhân viên kho/tài sản",
    "Nhân viên kế toán/quỹ",
]

WEATHER_CODES = [
    {"code": 0, "desc": "Nắng", "risk": "low"},
    {"code": 1, "desc": "Ít mây", "risk": "low"},
    {"code": 2, "desc": "Nhiều mây", "risk": "low"},
    {"code": 61, "desc": "Mưa nhẹ", "risk": "medium"},
    {"code": 63, "desc": "Mưa vừa", "risk": "medium"},
    {"code": 65, "desc": "Mưa to", "risk": "high"},
    {"code": 95, "desc": "Dông", "risk": "high"},
]
