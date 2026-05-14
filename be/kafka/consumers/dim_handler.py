"""
consumers/dim_handler.py

Xử lý Dimension tables.
"""

import logging
from datetime import datetime

from consumers.db import execute_query, insert_returning_id, upsert_and_get_key

logger = logging.getLogger(__name__)


def _row_get(row: dict, key: str, default=None):
    if not row:
        return default
    return row.get(key) if key in row else row.get(key.lower(), default)


# ================================================================
# Dim_KhachHang — SCD Type 2 đơn giản
# ================================================================
def handle_customer(conn, payload: dict) -> int | None:
    cmnd = payload["CMND_CCCD"]

    cur = execute_query(
        conn,
        """
        SELECT KhachHang_Key, NgheNghiep, ThuNhapHangThang, DiemTinDung,
               SoNguoiPhuThuoc, DiaChi, Version
        FROM Dim_KhachHang
        WHERE CMND_CCCD = %s AND IsCurrent = TRUE
        """,
        (cmnd,),
    )
    existing = cur.fetchone()

    if existing is None:
        return insert_returning_id(
            conn,
            """
            INSERT INTO Dim_KhachHang
            (TenKhachHang, SoDienThoai, CMND_CCCD, NgheNghiep,
             ThuNhapHangThang, DiemTinDung, SoNguoiPhuThuoc, DiaChi,
             NgayHieuLuc, IsCurrent, Version)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_DATE,TRUE,1)
            RETURNING KhachHang_Key
            """,
            (
                payload.get("TenKhachHang"),
                payload.get("SoDienThoai"),
                cmnd,
                payload.get("NgheNghiep"),
                payload.get("ThuNhapHangThang"),
                payload.get("DiemTinDung"),
                payload.get("SoNguoiPhuThuoc"),
                payload.get("DiaChi"),
            ),
        )

    fields = ["NgheNghiep", "ThuNhapHangThang", "DiemTinDung", "SoNguoiPhuThuoc", "DiaChi"]
    changed = any(_row_get(existing, f) != payload.get(f) for f in fields)
    if not changed:
        return _row_get(existing, "KhachHang_Key")

    old_key = _row_get(existing, "KhachHang_Key")
    old_version = _row_get(existing, "Version", 1) or 1

    execute_query(
        conn,
        "UPDATE Dim_KhachHang SET NgayHetHieuLuc = CURRENT_DATE, IsCurrent = FALSE WHERE KhachHang_Key = %s",
        (old_key,),
    )

    return insert_returning_id(
        conn,
        """
        INSERT INTO Dim_KhachHang
        (TenKhachHang, SoDienThoai, CMND_CCCD, NgheNghiep,
         ThuNhapHangThang, DiemTinDung, SoNguoiPhuThuoc, DiaChi,
         NgayHieuLuc, IsCurrent, Version)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_DATE,TRUE,%s)
        RETURNING KhachHang_Key
        """,
        (
            payload.get("TenKhachHang"),
            payload.get("SoDienThoai"),
            cmnd,
            payload.get("NgheNghiep"),
            payload.get("ThuNhapHangThang"),
            payload.get("DiemTinDung"),
            payload.get("SoNguoiPhuThuoc"),
            payload.get("DiaChi"),
            old_version + 1,
        ),
    )


# ================================================================
# Dim_TaiSan
# ================================================================
def handle_asset(conn, payload: dict) -> int | None:
    return insert_returning_id(
        conn,
        """
        INSERT INTO Dim_TaiSan
        (LoaiTaiSan, MoTaChiTiet, GiaTriDinhGia, TinhTrangBanDau, DuongDanAnh)
        VALUES (%s,%s,%s,%s,%s)
        RETURNING TaiSan_Key
        """,
        (
            payload.get("LoaiTaiSan"),
            payload.get("MoTaChiTiet"),
            payload.get("GiaTriDinhGia"),
            payload.get("TinhTrangBanDau"),
            payload.get("DuongDanAnh"),
        ),
    )


# ================================================================
# Lookup helpers
# ================================================================
def lookup_cuahang_key(conn, ma_cua_hang: str, fallback_key: int | None = None) -> int | None:
    if fallback_key:
        return fallback_key
    if not ma_cua_hang:
        return None

    cur = execute_query(conn, "SELECT CuaHang_Key FROM Dim_CuaHang WHERE MaCuaHang = %s", (ma_cua_hang,))
    row = cur.fetchone()
    if row:
        return _row_get(row, "CuaHang_Key")

    # fallback suffix numeric
    digits = "".join(ch for ch in ma_cua_hang if ch.isdigit())
    if digits:
        suffix = digits[-3:]
        cur = execute_query(
            conn,
            """
            SELECT CuaHang_Key
            FROM Dim_CuaHang
            WHERE RIGHT(regexp_replace(MaCuaHang, '\\D', '', 'g'), 3) = %s
            LIMIT 1
            """,
            (suffix,),
        )
        row = cur.fetchone()
        if row:
            return _row_get(row, "CuaHang_Key")
    return None


def lookup_nhanvien_key(conn, ma_nhan_vien: str | None) -> int | None:
    if not ma_nhan_vien:
        return None
    cur = execute_query(conn, "SELECT NhanVien_Key FROM Dim_NhanVien WHERE MaNhanVien = %s", (ma_nhan_vien,))
    row = cur.fetchone()
    return _row_get(row, "NhanVien_Key") if row else None


def lookup_loaihinh_key(conn, ten_loai_hinh: str, hinh_thuc_tra_no: str | None = None) -> int | None:
    return upsert_and_get_key(
        conn,
        "SELECT LoaiHinh_Key FROM Dim_LoaiHinh WHERE TenLoaiHinh = %s",
        (ten_loai_hinh,),
        """
        INSERT INTO Dim_LoaiHinh (TenLoaiHinh, HinhThucTraNo)
        VALUES (%s,%s)
        RETURNING LoaiHinh_Key
        """,
        (ten_loai_hinh, hinh_thuc_tra_no),
    )


def lookup_trangthai_key(conn, trang_thai: str) -> int | None:
    return upsert_and_get_key(
        conn,
        "SELECT TrangThai_Key FROM Dim_TrangThai WHERE TrangThaiKhoanVay = %s",
        (trang_thai,),
        """
        INSERT INTO Dim_TrangThai (TrangThaiKhoanVay)
        VALUES (%s)
        RETURNING TrangThai_Key
        """,
        (trang_thai,),
    )


def lookup_loaithuci_key(conn, ten_loai: str, nhom: str) -> int | None:
    return upsert_and_get_key(
        conn,
        "SELECT LoaiThuChi_Key FROM Dim_LoaiThuChi WHERE TenLoaiThuChi = %s",
        (ten_loai,),
        """
        INSERT INTO Dim_LoaiThuChi (TenLoaiThuChi, NhomThuChi)
        VALUES (%s,%s)
        RETURNING LoaiThuChi_Key
        """,
        (ten_loai, nhom),
    )


def lookup_quytien_key(conn, phuong_thuc: str | None) -> int | None:
    phuong_thuc = phuong_thuc or "Tiền mặt"
    loai = "Tiền mặt" if "mặt" in phuong_thuc.lower() else "Bank"
    ten = f"Quỹ {loai}"
    return upsert_and_get_key(
        conn,
        "SELECT QuyTien_Key FROM Dim_QuyTien WHERE TenQuy = %s",
        (ten,),
        """
        INSERT INTO Dim_QuyTien (TenQuy, LoaiQuy)
        VALUES (%s,%s)
        RETURNING QuyTien_Key
        """,
        (ten, loai),
    )


def lookup_khoanmuc_key(conn, ten_khoan_muc: str, nhom_chi_phi: str = "Chi phí QLDN") -> int | None:
    return upsert_and_get_key(
        conn,
        "SELECT KhoanMuc_Key FROM Dim_KhoanMucChiPhi WHERE TenKhoanMuc = %s",
        (ten_khoan_muc,),
        """
        INSERT INTO Dim_KhoanMucChiPhi (NhomChiPhi, TenKhoanMuc)
        VALUES (%s,%s)
        RETURNING KhoanMuc_Key
        """,
        (nhom_chi_phi, ten_khoan_muc),
    )


def lookup_nhacungcap_key(conn, ten_ncc: str | None) -> int | None:
    if not ten_ncc:
        return None
    return upsert_and_get_key(
        conn,
        "SELECT NhaCungCap_Key FROM Dim_NhaCungCap WHERE TenNhaCungCap = %s",
        (ten_ncc,),
        "INSERT INTO Dim_NhaCungCap (TenNhaCungCap) VALUES (%s) RETURNING NhaCungCap_Key",
        (ten_ncc,),
    )


def lookup_mathoitiet_key(conn, weather_code: int | None, desc: str | None = None) -> int | None:
    if weather_code is None:
        return None
    try:
        return upsert_and_get_key(
            conn,
            "SELECT MaThoiTiet_Key FROM Dim_MaThoiTiet WHERE Weather_Code = %s",
            (weather_code,),
            """
            INSERT INTO Dim_MaThoiTiet (Weather_Code, MoTaThoiTiet_VN)
            VALUES (%s,%s)
            RETURNING MaThoiTiet_Key
            """,
            (weather_code, desc),
        )
    except Exception as exc:
        logger.warning("lookup_mathoitiet_key skipped: %s", exc)
        conn.rollback()
        return None


def ensure_date_key(conn, date_key: int) -> int:
    cur = execute_query(conn, "SELECT Date_Key FROM Dim_ThoiGian WHERE Date_Key = %s", (date_key,))
    if cur.fetchone():
        return date_key

    dt = datetime.strptime(str(date_key), "%Y%m%d")
    weekday_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    execute_query(
        conn,
        """
        INSERT INTO Dim_ThoiGian
        (Date_Key, FullDate, Nam, Quy, Thang, Tuan, Ngay, TenThu)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (Date_Key) DO NOTHING
        """,
        (date_key, dt.date(), dt.year, (dt.month - 1) // 3 + 1, dt.month, dt.isocalendar()[1], dt.day, weekday_names[dt.weekday()]),
    )
    return date_key
