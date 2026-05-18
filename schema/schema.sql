create schema public;

-- ===================================================================
-- SCHEMA TỔ CHỨC TÍN DỤNG - HỆ THỐNG QUẢN LÝ QUY TRÌNH CHO VAY
-- Phiên bản: 2.0
-- Mô tả: Chạy một lần để tạo toàn bộ schema theo đúng thứ tự dependency
-- ===================================================================


-- ===================================================================
-- PHẦN 1: CÁC CHIỀU DÙNG CHUNG (CONFORMED DIMENSIONS)
-- Phải tạo trước vì được tham chiếu bởi hầu hết các bảng khác
-- ===================================================================

CREATE TABLE Dim_ThoiGian (
    Date_Key        INT PRIMARY KEY,        -- Định dạng YYYYMMDD (VD: 20260511)
    FullDate        DATE        NOT NULL,
    Nam             INT,
    Quy             INT,
    Thang           INT,
    Tuan            INT,                    -- Tuần trong năm (1-53)
    Ngay            INT,
    TenThu          VARCHAR(10),            -- Thứ Hai, Thứ Ba...
    LaaNgayLe       BOOLEAN     DEFAULT FALSE,
    LaaNgayCuoiThang BOOLEAN    DEFAULT FALSE
);

-- ===================================================================
-- PHẦN 5: WEATHER MART — Tạo Dim_ToaDo SỚM vì Dim_CuaHang cần FK vào đây
-- ===================================================================

CREATE TABLE Dim_ToaDo (
    ToaDo_Key           SERIAL PRIMARY KEY,
    Vido_Latitude       DECIMAL(9, 6)   NOT NULL,
    Kinhdo_Longitude    DECIMAL(9, 6)   NOT NULL,
    MuiGio_Timezone     VARCHAR(50),
    TenKhuVuc           VARCHAR(100),
    CONSTRAINT unq_toado UNIQUE (Vido_Latitude, Kinhdo_Longitude)
);

-- ===================================================================
-- PHẦN 1 (tiếp): Dim_CuaHang — phụ thuộc Dim_ToaDo
-- ===================================================================

CREATE TABLE Dim_CuaHang (
    CuaHang_Key     SERIAL PRIMARY KEY,
    MaCuaHang       VARCHAR(20)     UNIQUE NOT NULL,
    TenCuaHang      VARCHAR(100)    NOT NULL,
    DiaChi          TEXT,
    KhuVuc          VARCHAR(50),            -- VD: Hà Nội, TP.HCM
    HangCuaHang     VARCHAR(10),            -- A+, A, B, C, D
    NgayKhaiTruong  DATE,
    TrangThai       VARCHAR(20)     DEFAULT 'Hoạt động',
    ToaDo_Key       INT,
    FOREIGN KEY (ToaDo_Key) REFERENCES Dim_ToaDo(ToaDo_Key)
);

CREATE TABLE Dim_NhanVien (
    NhanVien_Key    SERIAL PRIMARY KEY,
    MaNhanVien      VARCHAR(20)     UNIQUE NOT NULL,
    TenNhanVien     VARCHAR(100)    NOT NULL,
    ChucVu          VARCHAR(50),            -- Cửa hàng trưởng, Giao dịch viên
    CuaHang_Key     INT,
    TrangThai       VARCHAR(20)     DEFAULT 'Đang làm việc',
    FOREIGN KEY (CuaHang_Key) REFERENCES Dim_CuaHang(CuaHang_Key)
);


-- ===================================================================
-- PHẦN 2: DATA MART TÍN DỤNG & RỦI RO (CREDIT MART)
-- ===================================================================

CREATE TABLE Dim_KhachHang (
    KhachHang_Key       SERIAL PRIMARY KEY,
    TenKhachHang        VARCHAR(255)    NOT NULL,
    SoDienThoai         VARCHAR(20)     NOT NULL,
    CMND_CCCD           VARCHAR(20)     UNIQUE NOT NULL,
    NgheNghiep          VARCHAR(100),
    ThuNhapHangThang    DECIMAL(15, 2),
    DiemTinDung         INT,
    SoNguoiPhuThuoc     INT,
    DiaChi              TEXT,
    -- SCD Type 2: theo dõi thay đổi thông tin khách hàng theo thời gian
    NgayHieuLuc         DATE            NOT NULL DEFAULT CURRENT_DATE,
    NgayHetHieuLuc      DATE,                   -- NULL = bản ghi hiện tại
    IsCurrent           BOOLEAN         DEFAULT TRUE,
    Version             INT             DEFAULT 1
);

CREATE TABLE Dim_TaiSan (
    TaiSan_Key          SERIAL PRIMARY KEY,
    LoaiTaiSan          VARCHAR(100)    NOT NULL,   -- VD: Xe máy, Ô tô, Sổ đỏ
    MoTaChiTiet         TEXT,
    GiaTriDinhGia       DECIMAL(15, 2),
    TinhTrangBanDau     TEXT,
    DuongDanAnh         VARCHAR(500)
);

CREATE TABLE Dim_LoaiHinh (
    LoaiHinh_Key        SERIAL PRIMARY KEY,
    TenLoaiHinh         VARCHAR(50)     NOT NULL,   -- Cầm đồ, Tín chấp, Thế chấp
    HinhThucTraNo       VARCHAR(100)    NOT NULL    -- Góp đều, Gốc đều, Cuối kỳ
);

CREATE TABLE Dim_TrangThai (
    TrangThai_Key       SERIAL PRIMARY KEY,
    TrangThaiKhoanVay   VARCHAR(50),    -- Chờ duyệt, Đang lưu hành, Đã tất toán...
    NhomNo              VARCHAR(50)     -- Nợ tiêu chuẩn, Nợ xấu...
);

-- Fact: Hồ sơ & Giao dịch vay
CREATE TABLE Fact_GiaoDich (
    GiaoDich_Key        BIGSERIAL PRIMARY KEY,
    KhachHang_Key       INT,
    TaiSan_Key          INT,
    LoaiHinh_Key        INT,
    NgayGiaiNgan_Key    INT,            -- Có thể NULL nếu hủy/từ chối
    NgayDaoHan_Key      INT,
    TrangThai_Key       INT,
    CuaHang_Key         INT,
    NhanVien_Sale_Key   INT,
    NguoiDuyet_Key      INT,            -- FK -> Dim_NhanVien, NULL nếu chưa duyệt
    NgayDuyet_Key       INT,            -- FK -> Dim_ThoiGian, NULL nếu chưa duyệt
    SoHopDong           VARCHAR(50)     UNIQUE,
    LyDoTuChoi          TEXT,           -- NULL nếu được duyệt
    SoTienMongMuon      DECIMAL(15, 2),
    SoTienDuyetVay      DECIMAL(15, 2), -- NULL cho hồ sơ từ chối
    LaiSuat             FLOAT,
    PhiPhatTraTruoc     DECIMAL(15, 2),
    ThoiHanVay_Thang    INT,
    KyTraNo_Thang       INT,
    SoTienTraMoiKy      DECIMAL(15, 2),
    FOREIGN KEY (KhachHang_Key)     REFERENCES Dim_KhachHang(KhachHang_Key),
    FOREIGN KEY (TaiSan_Key)        REFERENCES Dim_TaiSan(TaiSan_Key),
    FOREIGN KEY (LoaiHinh_Key)      REFERENCES Dim_LoaiHinh(LoaiHinh_Key),
    FOREIGN KEY (NgayGiaiNgan_Key)  REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (NgayDaoHan_Key)    REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (NgayDuyet_Key)     REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (TrangThai_Key)     REFERENCES Dim_TrangThai(TrangThai_Key),
    FOREIGN KEY (CuaHang_Key)       REFERENCES Dim_CuaHang(CuaHang_Key),
    FOREIGN KEY (NhanVien_Sale_Key) REFERENCES Dim_NhanVien(NhanVien_Key),
    FOREIGN KEY (NguoiDuyet_Key)    REFERENCES Dim_NhanVien(NhanVien_Key)
);

-- Fact: Lịch sử chuyển trạng thái hợp đồng (audit trail)
CREATE TABLE Fact_LichSuTrangThai (
    LichSu_ID               BIGSERIAL PRIMARY KEY,
    GiaoDich_Key            BIGINT  NOT NULL,
    TrangThai_Key           INT     NOT NULL,
    TuNgay_Key              INT     NOT NULL,   -- Ngày bắt đầu mang trạng thái này
    DenNgay_Key             INT,                -- NULL = trạng thái hiện tại
    NhanVien_ThucHien_Key   INT,
    GhiChu                  TEXT,
    FOREIGN KEY (GiaoDich_Key)          REFERENCES Fact_GiaoDich(GiaoDich_Key),
    FOREIGN KEY (TrangThai_Key)         REFERENCES Dim_TrangThai(TrangThai_Key),
    FOREIGN KEY (TuNgay_Key)            REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (DenNgay_Key)           REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (NhanVien_ThucHien_Key) REFERENCES Dim_NhanVien(NhanVien_Key)
);

CREATE INDEX idx_lichsu_giaodich ON Fact_LichSuTrangThai(GiaoDich_Key);

-- Fact: Lịch sử trả nợ (thu hồi vốn)
CREATE TABLE Fact_LichSuTraNo (
    TraNo_ID            BIGSERIAL PRIMARY KEY,
    GiaoDich_Key        BIGINT  NOT NULL,
    NgayThanhToan_Key   INT     NOT NULL,
    SoTienGocDaTra      DECIMAL(15, 2)  DEFAULT 0,
    SoTienLaiDaTra      DECIMAL(15, 2)  DEFAULT 0,
    PhiPhatTreHan       DECIMAL(15, 2)  DEFAULT 0,
    GhiChu              TEXT,
    FOREIGN KEY (GiaoDich_Key)      REFERENCES Fact_GiaoDich(GiaoDich_Key),
    FOREIGN KEY (NgayThanhToan_Key) REFERENCES Dim_ThoiGian(Date_Key)
);


-- ===================================================================
-- PHẦN 3: DATA MART KẾ TOÁN & DÒNG TIỀN (CASHFLOW MART)
-- ===================================================================

CREATE TABLE Dim_QuyTien (
    QuyTien_Key     SERIAL PRIMARY KEY,
    TenQuy          VARCHAR(100)    NOT NULL,
    LoaiQuy         VARCHAR(50)     NOT NULL,   -- Tiền mặt, Bank
    SoTaiKhoan      VARCHAR(50),
    TrangThai       VARCHAR(20)     DEFAULT 'Hoạt động'
);

CREATE TABLE Dim_LoaiThuChi (
    LoaiThuChi_Key  SERIAL PRIMARY KEY,
    TenLoaiThuChi   VARCHAR(100)    NOT NULL,   -- Thu nợ, Giải ngân, Chi phí...
    NhomThuChi      VARCHAR(50)     NOT NULL
);

-- Fact: Sổ quỹ dòng tiền
CREATE TABLE Fact_ThuChi (
    Phieu_ID            BIGSERIAL PRIMARY KEY,
    NgayThucHien_Key    INT     NOT NULL,
    QuyTien_Key         INT     NOT NULL,
    LoaiThuChi_Key      INT     NOT NULL,
    GiaoDich_Key        BIGINT,                 -- NULL nếu không gắn với hợp đồng
    CuaHang_Key         INT,
    SoTienThu           DECIMAL(15, 2)  DEFAULT 0,
    SoTienChi           DECIMAL(15, 2)  DEFAULT 0,
    NguoiThucHien       VARCHAR(100),
    ChungTuGoc          VARCHAR(100),
    GhiChu              TEXT,
    FOREIGN KEY (NgayThucHien_Key)  REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (QuyTien_Key)       REFERENCES Dim_QuyTien(QuyTien_Key),
    FOREIGN KEY (LoaiThuChi_Key)    REFERENCES Dim_LoaiThuChi(LoaiThuChi_Key),
    FOREIGN KEY (GiaoDich_Key)      REFERENCES Fact_GiaoDich(GiaoDich_Key),
    FOREIGN KEY (CuaHang_Key)       REFERENCES Dim_CuaHang(CuaHang_Key)
);


-- ===================================================================
-- PHẦN 4: DATA MART CHI PHÍ & NHÂN SỰ (OPEX & HR MART)
-- ===================================================================

CREATE TABLE Dim_KhoanMucChiPhi (
    KhoanMuc_Key    SERIAL PRIMARY KEY,
    NhomChiPhi      VARCHAR(100)    NOT NULL,   -- Chi phí BH, Chi phí QLDN
    TenKhoanMuc     VARCHAR(150)    NOT NULL,   -- Lương, Khấu hao, Điện nước
    DienGiai        TEXT,
    TrangThai       VARCHAR(20)     DEFAULT 'Sử dụng'
);

CREATE TABLE Dim_NhaCungCap (
    NhaCungCap_Key  SERIAL PRIMARY KEY,
    TenNhaCungCap   VARCHAR(200)    NOT NULL,
    LoaiDichVu      VARCHAR(100),
    SoDienThoai     VARCHAR(20),
    MaSoThue        VARCHAR(20),
    SoTaiKhoan      VARCHAR(50)
);

CREATE TABLE Dim_TaiSanNoiBo (
    TaiSanNoiBo_Key         SERIAL PRIMARY KEY,
    MaTaiSan                VARCHAR(50)     UNIQUE NOT NULL,
    TenTaiSan               VARCHAR(150)    NOT NULL,
    LoaiTaiSan              VARCHAR(50),
    NgayMua                 DATE,
    GiaTriNguyenGia         DECIMAL(15, 2),
    ThoiGianKhauHao_Thang   INT
);

-- Fact: Chi phí hoạt động chung
CREATE TABLE Fact_ChiPhiHoatDong (
    ChiPhi_ID           BIGSERIAL PRIMARY KEY,
    NgayGhiNhan_Key     INT     NOT NULL,
    CuaHang_Key         INT     NOT NULL,
    KhoanMuc_Key        INT     NOT NULL,
    NhaCungCap_Key      INT,
    NhanVien_Tao_Key    INT,
    SoTienTruocThue     DECIMAL(15, 2)  DEFAULT 0,
    TienThueVAT         DECIMAL(15, 2)  DEFAULT 0,
    TongTienChiPhi      DECIMAL(15, 2)  NOT NULL,
    SoHoaDon            VARCHAR(50),
    MoTaChiTiet         TEXT,
    TrangThaiThanhToan  VARCHAR(50)     DEFAULT 'Chưa thanh toán',
    NgayThanhToan_Key   INT,
    PhieuChi_ID         BIGINT,         -- Tham chiếu mềm tới Fact_ThuChi
    FOREIGN KEY (NgayGhiNhan_Key)   REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (NgayThanhToan_Key) REFERENCES Dim_ThoiGian(Date_Key),
    FOREIGN KEY (CuaHang_Key)       REFERENCES Dim_CuaHang(CuaHang_Key),
    FOREIGN KEY (KhoanMuc_Key)      REFERENCES Dim_KhoanMucChiPhi(KhoanMuc_Key),
    FOREIGN KEY (NhaCungCap_Key)    REFERENCES Dim_NhaCungCap(NhaCungCap_Key),
    FOREIGN KEY (NhanVien_Tao_Key)  REFERENCES Dim_NhanVien(NhanVien_Key)
);

-- Fact: Khấu hao tài sản nội bộ (ghi nhận theo tháng)
CREATE TABLE Fact_KhauHao (
    KhauHao_ID          BIGSERIAL PRIMARY KEY,
    KyKeToan_Key        INT     NOT NULL,       -- Định dạng YYYYMM
    CuaHang_Key         INT     NOT NULL,
    TaiSanNoiBo_Key     INT     NOT NULL,
    KhoanMuc_Key        INT     NOT NULL,
    GiaTriKhauHaoThang  DECIMAL(15, 2),
    GiaTriConLai        DECIMAL(15, 2),
    FOREIGN KEY (CuaHang_Key)       REFERENCES Dim_CuaHang(CuaHang_Key),
    FOREIGN KEY (TaiSanNoiBo_Key)   REFERENCES Dim_TaiSanNoiBo(TaiSanNoiBo_Key),
    FOREIGN KEY (KhoanMuc_Key)      REFERENCES Dim_KhoanMucChiPhi(KhoanMuc_Key)
);

-- Fact: Lương và hoa hồng (tổng hợp theo kỳ)
CREATE TABLE Fact_LuongThuong (
    BangLuong_ID        BIGSERIAL PRIMARY KEY,
    KyKeToan_Key        INT     NOT NULL,       -- Định dạng YYYYMM
    NhanVien_Key        INT     NOT NULL,
    CuaHang_Key         INT     NOT NULL,
    KhoanMuc_Key        INT     NOT NULL,
    LuongCoBan          DECIMAL(15, 2)  DEFAULT 0,
    HoaHongGiaiNgan     DECIMAL(15, 2)  DEFAULT 0,
    HoaHongThuNo        DECIMAL(15, 2)  DEFAULT 0,
    PhuCap              DECIMAL(15, 2)  DEFAULT 0,
    TongThuNhap         DECIMAL(15, 2)  NOT NULL,
    FOREIGN KEY (NhanVien_Key)  REFERENCES Dim_NhanVien(NhanVien_Key),
    FOREIGN KEY (CuaHang_Key)   REFERENCES Dim_CuaHang(CuaHang_Key),
    FOREIGN KEY (KhoanMuc_Key)  REFERENCES Dim_KhoanMucChiPhi(KhoanMuc_Key)
);


-- ===================================================================
-- PHẦN 5 (tiếp): DATA MART THỜI TIẾT (WEATHER MART)
-- Dim_ToaDo đã tạo ở trên — chỉ tạo các bảng còn lại ở đây
-- ===================================================================

CREATE TABLE Dim_MaThoiTiet (
    MaThoiTiet_Key      SERIAL PRIMARY KEY,
    Weather_Code        INT             UNIQUE NOT NULL,
    MoTaThoiTiet_VN     VARCHAR(100),
    MoTaThoiTiet_EN     VARCHAR(100)
);

CREATE TABLE Fact_ThoiTiet_HienTai (
    Current_ID          BIGSERIAL PRIMARY KEY,
    ToaDo_Key           INT     NOT NULL,
    MaThoiTiet_Key      INT,
    ThoiDiemDo          TIMESTAMP   NOT NULL,
    NhietDo_2m          FLOAT,
    DoAm_2m             FLOAT,
    LuongMua            FLOAT,
    TocDoGio_10m        FLOAT,
    NgayGhiNhan_Key     INT,
    FOREIGN KEY (ToaDo_Key)         REFERENCES Dim_ToaDo(ToaDo_Key),
    FOREIGN KEY (MaThoiTiet_Key)    REFERENCES Dim_MaThoiTiet(MaThoiTiet_Key)
);

CREATE TABLE Fact_ThoiTiet_TheoGio (
    Hourly_ID           BIGSERIAL PRIMARY KEY,
    ToaDo_Key           INT     NOT NULL,
    ThoiDiemDuBao       TIMESTAMP   NOT NULL,
    NhietDo_2m          FLOAT,
    XacSuatMua          FLOAT,
    NgayDuBao_Key       INT,
    GioDuBao            INT,
    FOREIGN KEY (ToaDo_Key) REFERENCES Dim_ToaDo(ToaDo_Key),
    CONSTRAINT unq_hourly_log UNIQUE (ToaDo_Key, ThoiDiemDuBao)
);
