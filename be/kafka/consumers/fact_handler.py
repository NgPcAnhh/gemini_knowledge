"""
consumers/fact_handler.py

Xử lý Fact tables.

Thiết kế cho dashboard realtime:
- loan_application_created -> Fact_GiaoDich + Fact_LichSuTrangThai
- loan_approved/rejected -> update Fact_GiaoDich + history
- loan_disbursed -> update Fact_GiaoDich + history + Fact_ThuChi chi giải ngân
- repayment_paid -> Fact_LichSuTraNo + Fact_ThuChi thu gốc/lãi/phí + update dư nợ còn lại
- loan_status_changed -> update trạng thái + history
- weather_updated -> best-effort insert weather fact
"""

import logging
from datetime import datetime

from consumers.db import execute_query, insert_returning_id, column_exists
from consumers.dim_handler import (
    lookup_cuahang_key,
    lookup_nhanvien_key,
    lookup_loaihinh_key,
    lookup_trangthai_key,
    lookup_loaithuci_key,
    lookup_quytien_key,
    lookup_khoanmuc_key,
    lookup_nhacungcap_key,
    lookup_mathoitiet_key,
    ensure_date_key,
)

logger = logging.getLogger(__name__)


def _date_key(event_time_str: str | None = None, date_str: str | None = None) -> int:
    if date_str:
        return int(str(date_str).replace("-", "")[:8])
    try:
        return int(datetime.fromisoformat(event_time_str).strftime("%Y%m%d"))
    except Exception:
        return int(datetime.now().strftime("%Y%m%d"))


def _row_get(row: dict, key: str, default=None):
    if not row:
        return default
    return row.get(key) if key in row else row.get(key.lower(), default)


def _find_giaodich(conn, contract_no: str) -> dict | None:
    cur = execute_query(conn, "SELECT * FROM Fact_GiaoDich WHERE SoHopDong = %s", (contract_no,))
    return cur.fetchone()


def _insert_status_history(conn, giaodich_key: int, trangthai_key: int, date_key: int, nv_key: int | None, note: str):
    execute_query(
        conn,
        """
        UPDATE Fact_LichSuTrangThai
        SET DenNgay_Key = %s
        WHERE GiaoDich_Key = %s AND DenNgay_Key IS NULL
        """,
        (date_key, giaodich_key),
    )
    execute_query(
        conn,
        """
        INSERT INTO Fact_LichSuTrangThai
        (GiaoDich_Key, TrangThai_Key, TuNgay_Key, NhanVien_ThucHien_Key, GhiChu)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (giaodich_key, trangthai_key, date_key, nv_key, note),
    )


def handle_loan_application(conn, payload: dict, khachhang_key: int | None, taisan_key: int | None):
    cuahang_key = lookup_cuahang_key(conn, payload.get("MaCuaHang"), payload.get("CuaHang_Key"))
    nv_sale_key = lookup_nhanvien_key(conn, payload.get("MaNhanVienSale"))
    loaihinh_key = lookup_loaihinh_key(conn, payload.get("TenLoaiHinh"), payload.get("HinhThucTraNo"))
    trangthai_key = lookup_trangthai_key(conn, payload.get("TrangThai", "Chờ tiếp nhận"))

    giaodich_key = insert_returning_id(
        conn,
        """
        INSERT INTO Fact_GiaoDich
        (KhachHang_Key, TaiSan_Key, LoaiHinh_Key, TrangThai_Key,
         CuaHang_Key, NhanVien_Sale_Key, SoHopDong, SoTienMongMuon)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (SoHopDong) DO NOTHING
        RETURNING GiaoDich_Key
        """,
        (
            khachhang_key,
            taisan_key,
            loaihinh_key,
            trangthai_key,
            cuahang_key,
            nv_sale_key,
            payload["SoHopDong"],
            payload.get("SoTienMongMuon", 0),
        ),
    )

    if not giaodich_key:
        row = _find_giaodich(conn, payload["SoHopDong"])
        return _row_get(row, "GiaoDich_Key") if row else None

    dk = _date_key(payload.get("_event_time"))
    ensure_date_key(conn, dk)
    execute_query(
        conn,
        """
        INSERT INTO Fact_LichSuTrangThai
        (GiaoDich_Key, TrangThai_Key, TuNgay_Key, NhanVien_ThucHien_Key, GhiChu)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (giaodich_key, trangthai_key, dk, nv_sale_key, "Tạo hồ sơ mới"),
    )
    return giaodich_key


def handle_loan_approved(conn, payload: dict, event_time_str: str):
    contract_no = payload["SoHopDong"]
    row = _find_giaodich(conn, contract_no)
    if not row:
        logger.warning("Approved before application, skip: %s", contract_no)
        return

    giaodich_key = _row_get(row, "GiaoDich_Key")
    trangthai_key = lookup_trangthai_key(conn, "Đã duyệt")
    nguoiduyet_key = lookup_nhanvien_key(conn, payload.get("MaNguoiDuyet"))
    dk = _date_key(date_str=payload.get("NgayDuyet")) or _date_key(event_time_str)
    ensure_date_key(conn, dk)

    execute_query(
        conn,
        """
        UPDATE Fact_GiaoDich SET
          NguoiDuyet_Key = %s,
          NgayDuyet_Key = %s,
          SoTienDuyetVay = %s,
          LaiSuat = %s,
          PhiPhatTraTruoc = %s,
          ThoiHanVay_Thang = %s,
          KyTraNo_Thang = %s,
          SoTienTraMoiKy = %s,
          TrangThai_Key = %s
        WHERE GiaoDich_Key = %s
        """,
        (
            nguoiduyet_key,
            dk,
            payload.get("SoTienDuyetVay"),
            payload.get("LaiSuat"),
            payload.get("PhiPhatTraTruoc", 0),
            payload.get("ThoiHanVay_Thang"),
            payload.get("KyTraNo_Thang", 1),
            payload.get("SoTienTraMoiKy"),
            trangthai_key,
            giaodich_key,
        ),
    )
    _insert_status_history(conn, giaodich_key, trangthai_key, dk, nguoiduyet_key, "Hồ sơ được duyệt")


def handle_loan_rejected(conn, payload: dict, event_time_str: str):
    contract_no = payload["SoHopDong"]
    row = _find_giaodich(conn, contract_no)
    if not row:
        logger.warning("Rejected before application, skip: %s", contract_no)
        return

    giaodich_key = _row_get(row, "GiaoDich_Key")
    trangthai_key = lookup_trangthai_key(conn, "Từ chối")
    dk = _date_key(event_time_str)
    ensure_date_key(conn, dk)

    execute_query(
        conn,
        "UPDATE Fact_GiaoDich SET TrangThai_Key = %s, LyDoTuChoi = %s WHERE GiaoDich_Key = %s",
        (trangthai_key, payload.get("LyDoTuChoi"), giaodich_key),
    )
    _insert_status_history(conn, giaodich_key, trangthai_key, dk, None, f"Từ chối: {payload.get('LyDoTuChoi','')}")


def handle_loan_disbursed(conn, payload: dict, event_time_str: str):
    contract_no = payload["SoHopDong"]
    row = _find_giaodich(conn, contract_no)
    if not row:
        logger.warning("Disbursed before application, skip: %s", contract_no)
        return

    giaodich_key = _row_get(row, "GiaoDich_Key")
    cuahang_key = lookup_cuahang_key(conn, payload.get("MaCuaHang"), payload.get("CuaHang_Key"))
    nv_key = lookup_nhanvien_key(conn, payload.get("MaNhanVien"))
    giai_ngan_key = _date_key(date_str=payload.get("NgayGiaiNgan"))
    dao_han_key = _date_key(date_str=payload.get("NgayDaoHan"))
    ensure_date_key(conn, giai_ngan_key)
    ensure_date_key(conn, dao_han_key)

    trangthai_key = lookup_trangthai_key(conn, "Đang lưu hành")

    execute_query(
        conn,
        """
        UPDATE Fact_GiaoDich SET
          NgayGiaiNgan_Key = %s,
          NgayDaoHan_Key = %s,
          TrangThai_Key = %s,
          CuaHang_Key = COALESCE(CuaHang_Key, %s)
        WHERE GiaoDich_Key = %s
        """,
        (giai_ngan_key, dao_han_key, trangthai_key, cuahang_key, giaodich_key),
    )

    # Nếu schema có cột dư nợ thì cập nhật; nếu không có thì bỏ qua.
    for col, val in [
        ("DuNoGocBanDau", payload.get("DuNoGocBanDau", payload.get("SoTienGiaiNgan"))),
        ("DuNoConLai", payload.get("DuNoConLai", payload.get("SoTienGiaiNgan"))),
    ]:
        if val is not None and column_exists(conn, "Fact_GiaoDich", col):
            execute_query(conn, f"UPDATE Fact_GiaoDich SET {col} = %s WHERE GiaoDich_Key = %s", (val, giaodich_key))

    _insert_status_history(conn, giaodich_key, trangthai_key, giai_ngan_key, nv_key, "Đã giải ngân - Đang lưu hành")

    # Dòng tiền chi giải ngân: giữ ở đây để FastAPI hiện tại không bị double count từ cash_recorded.
    phuong_thuc = payload.get("PhuongThuc", "Tiền mặt")
    loai_chi = "Giải ngân tiền mặt" if "mặt" in phuong_thuc.lower() else "Giải ngân chuyển khoản"
    loaithuci_key = lookup_loaithuci_key(conn, loai_chi, "Chi")
    quytien_key = lookup_quytien_key(conn, phuong_thuc)
    execute_query(
        conn,
        """
        INSERT INTO Fact_ThuChi
        (NgayThucHien_Key, QuyTien_Key, LoaiThuChi_Key, GiaoDich_Key,
         CuaHang_Key, SoTienThu, SoTienChi, NguoiThucHien, ChungTuGoc, GhiChu)
        VALUES (%s,%s,%s,%s,%s,0,%s,%s,%s,%s)
        """,
        (
            giai_ngan_key,
            quytien_key,
            loaithuci_key,
            giaodich_key,
            cuahang_key,
            payload.get("SoTienGiaiNgan", 0),
            payload.get("MaNhanVien"),
            payload.get("ChungTuGoc"),
            f"Giải ngân HĐ {contract_no}",
        ),
    )


def handle_repayment(conn, payload: dict, event_time_str: str):
    contract_no = payload["SoHopDong"]
    row = _find_giaodich(conn, contract_no)
    if not row:
        logger.warning("Repayment before application, skip: %s", contract_no)
        return

    giaodich_key = _row_get(row, "GiaoDich_Key")
    cuahang_key = lookup_cuahang_key(conn, payload.get("MaCuaHang"), payload.get("CuaHang_Key"))
    dk = _date_key(event_time_str)
    ensure_date_key(conn, dk)

    execute_query(
        conn,
        """
        INSERT INTO Fact_LichSuTraNo
        (GiaoDich_Key, NgayThanhToan_Key, SoTienGocDaTra, SoTienLaiDaTra, PhiPhatTreHan, GhiChu)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            giaodich_key,
            dk,
            payload.get("SoTienGocDaTra", 0),
            payload.get("SoTienLaiDaTra", 0),
            payload.get("PhiPhatTreHan", 0),
            payload.get("GhiChu", ""),
        ),
    )

    # Update dư nợ nếu schema có cột DuNoConLai.
    if column_exists(conn, "Fact_GiaoDich", "DuNoConLai") and payload.get("DuNoConLai") is not None:
        execute_query(conn, "UPDATE Fact_GiaoDich SET DuNoConLai = %s WHERE GiaoDich_Key = %s", (payload.get("DuNoConLai"), giaodich_key))

    # Dòng tiền thu.
    flows = [
        ("Thu nợ gốc", payload.get("SoTienGocDaTra", 0), f"Thu gốc HĐ {contract_no}"),
        ("Thu nợ lãi", payload.get("SoTienLaiDaTra", 0), f"Thu lãi HĐ {contract_no}"),
        ("Thu phí phạt trễ hạn", payload.get("PhiPhatTreHan", 0), f"Phí phạt HĐ {contract_no}"),
    ]
    quytien_key = lookup_quytien_key(conn, payload.get("PhuongThuc", "Tiền mặt"))
    for ten_loai, amount, note in flows:
        if not amount or float(amount) <= 0:
            continue
        loai_key = lookup_loaithuci_key(conn, ten_loai, "Thu")
        execute_query(
            conn,
            """
            INSERT INTO Fact_ThuChi
            (NgayThucHien_Key, QuyTien_Key, LoaiThuChi_Key, GiaoDich_Key,
             CuaHang_Key, SoTienThu, SoTienChi, NguoiThucHien, ChungTuGoc, GhiChu)
            VALUES (%s,%s,%s,%s,%s,%s,0,%s,%s,%s)
            """,
            (
                dk,
                quytien_key,
                loai_key,
                giaodich_key,
                cuahang_key,
                amount,
                payload.get("MaNhanVien"),
                payload.get("ChungTuGoc"),
                note,
            ),
        )

    # Nếu payload có trạng thái sau thanh toán thì cập nhật.
    new_status = payload.get("TrangThaiSauThanhToan")
    if new_status:
        trangthai_key = lookup_trangthai_key(conn, new_status)
        execute_query(conn, "UPDATE Fact_GiaoDich SET TrangThai_Key = %s WHERE GiaoDich_Key = %s", (trangthai_key, giaodich_key))


def handle_status_changed(conn, payload: dict, event_time_str: str):
    contract_no = payload["SoHopDong"]
    row = _find_giaodich(conn, contract_no)
    if not row:
        logger.warning("Status before application, skip: %s", contract_no)
        return

    giaodich_key = _row_get(row, "GiaoDich_Key")
    new_status = payload.get("TrangThaiMoi")
    trangthai_key = lookup_trangthai_key(conn, new_status)
    nv_key = lookup_nhanvien_key(conn, payload.get("MaNhanVien"))
    dk = _date_key(date_str=payload.get("NgayThayDoi")) if payload.get("NgayThayDoi") else _date_key(event_time_str)
    ensure_date_key(conn, dk)

    execute_query(conn, "UPDATE Fact_GiaoDich SET TrangThai_Key = %s WHERE GiaoDich_Key = %s", (trangthai_key, giaodich_key))
    _insert_status_history(conn, giaodich_key, trangthai_key, dk, nv_key, payload.get("LyDo", f"Đổi trạng thái sang {new_status}"))


def handle_cash_recorded(conn, payload: dict, event_time_str: str):
    dk = _date_key(event_time_str)
    ensure_date_key(conn, dk)
    nhom = "Chi" if float(payload.get("SoTienChi", 0) or 0) > 0 else "Thu"
    loaithuci_key = lookup_loaithuci_key(conn, payload.get("TenLoaiThuChi"), nhom)
    quytien_key = lookup_quytien_key(conn, payload.get("PhuongThuc", "Tiền mặt"))
    cuahang_key = lookup_cuahang_key(conn, payload.get("MaCuaHang"), payload.get("CuaHang_Key"))

    giaodich_key = None
    if payload.get("SoHopDong"):
        row = _find_giaodich(conn, payload.get("SoHopDong"))
        giaodich_key = _row_get(row, "GiaoDich_Key") if row else None

    execute_query(
        conn,
        """
        INSERT INTO Fact_ThuChi
        (NgayThucHien_Key, QuyTien_Key, LoaiThuChi_Key, GiaoDich_Key,
         CuaHang_Key, SoTienThu, SoTienChi, NguoiThucHien, ChungTuGoc, GhiChu)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            dk,
            quytien_key,
            loaithuci_key,
            giaodich_key,
            cuahang_key,
            payload.get("SoTienThu", 0),
            payload.get("SoTienChi", 0),
            payload.get("NguoiThucHien"),
            payload.get("ChungTuGoc"),
            payload.get("GhiChu", ""),
        ),
    )


def handle_weather(conn, payload: dict, event_time_str: str):
    """Best-effort weather fact. Nếu schema weather khác, lỗi sẽ được log và không làm fail cả consumer."""
    try:
        dk = _date_key(event_time_str)
        ensure_date_key(conn, dk)
        ma_weather_key = lookup_mathoitiet_key(conn, payload.get("Weather_Code"), payload.get("MoTaThoiTiet_VN"))
        toa_do_key = payload.get("ToaDo_Key")

        # Fact_ThoiTiet_HienTai: insert/update nếu schema có các cột phổ biến.
        execute_query(
            conn,
            """
            INSERT INTO Fact_ThoiTiet_HienTai
            (NgayGhiNhan_Key, ToaDo_Key, MaThoiTiet_Key, NhietDo_2m, LuongMua, TocDoGio_10m, ThoiDiemDo)
            VALUES (%s,%s,%s,%s,%s,%s,NOW())
            """,
            (
                dk,
                toa_do_key,
                ma_weather_key,
                payload.get("NhietDo_2m"),
                payload.get("LuongMua"),
                payload.get("TocDoGio_10m"),
            ),
        )
    except Exception as exc:
        logger.warning("Weather fact skipped: %s", exc)
        conn.rollback()


def handle_opex(conn, payload: dict, event_time_str: str):
    dk = _date_key(event_time_str)
    ensure_date_key(conn, dk)
    cuahang_key = lookup_cuahang_key(conn, payload.get("MaCuaHang"), payload.get("CuaHang_Key"))
    khoanmuc_key = lookup_khoanmuc_key(conn, payload.get("TenKhoanMuc"))
    nv_key = lookup_nhanvien_key(conn, payload.get("MaNhanVienTao"))
    ncc_key = lookup_nhacungcap_key(conn, payload.get("TenNhaCungCap"))

    insert_returning_id(
        conn,
        """
        INSERT INTO Fact_ChiPhiHoatDong
        (NgayGhiNhan_Key, CuaHang_Key, KhoanMuc_Key, NhaCungCap_Key, NhanVien_Tao_Key,
         SoTienTruocThue, TienThueVAT, TongTienChiPhi, SoHoaDon, MoTaChiTiet, TrangThaiThanhToan)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING ChiPhi_ID
        """,
        (
            dk,
            cuahang_key,
            khoanmuc_key,
            ncc_key,
            nv_key,
            payload.get("SoTienTruocThue", 0),
            payload.get("TienThueVAT", 0),
            payload.get("TongTienChiPhi", 0),
            payload.get("SoHoaDon"),
            payload.get("MoTaChiTiet"),
            payload.get("TrangThaiThanhToan", "Chưa thanh toán"),
        ),
    )


def handle_payroll(conn, payload: dict, event_time_str: str):
    nv_key = lookup_nhanvien_key(conn, payload.get("MaNhanVien"))
    cuahang_key = lookup_cuahang_key(conn, payload.get("MaCuaHang"), payload.get("CuaHang_Key"))
    khoanmuc_key = lookup_khoanmuc_key(conn, payload.get("TenKhoanMuc", "Lương nhân viên"))

    execute_query(
        conn,
        """
        INSERT INTO Fact_LuongThuong
        (KyKeToan_Key, NhanVien_Key, CuaHang_Key, KhoanMuc_Key,
         LuongCoBan, HoaHongGiaiNgan, HoaHongThuNo, PhuCap, TongThuNhap)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            payload.get("KyKeToan"),
            nv_key,
            cuahang_key,
            khoanmuc_key,
            payload.get("LuongCoBan", 0),
            payload.get("HoaHongGiaiNgan", 0),
            payload.get("HoaHongThuNo", 0),
            payload.get("PhuCap", 0),
            payload.get("TongThuNhap", 0),
        ),
    )
