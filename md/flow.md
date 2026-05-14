# Tài liệu mô tả luồng nghiệp vụ và luồng dữ liệu realtime

## 1. Bối cảnh hệ thống

Hệ thống mô phỏng luồng dữ liệu cho nghiệp vụ cho vay/cầm đồ F88 trên toàn quốc, tập trung trước vào dashboard realtime phục vụ chiến dịch tài chính bình dân cho nhóm tài xế công nghệ/shipper.

Dữ liệu trong hệ thống là dữ liệu fake nhưng được sinh theo logic nghiệp vụ gần thực tế. Mục tiêu không phải tái hiện đúng từng khách hàng/cửa hàng thật, mà là tạo dòng dữ liệu có cấu trúc, có quan hệ cửa hàng - khách hàng - nhân viên - hợp đồng - tài sản - dòng tiền - thời tiết để kiểm thử dashboard, Kafka pipeline, Redis realtime cache, FastAPI API/WebSocket và data warehouse.

## 2. Phạm vi xử lý giai đoạn hiện tại

Giai đoạn hiện tại ưu tiên tab 1 của dashboard: **Tổng quan Real-time**.

Các nhóm dữ liệu được xử lý trong giai đoạn này gồm:

* Hợp đồng phát sinh trong ngày.
* Quyết định duyệt/từ chối khoản vay.
* Giải ngân khoản vay.
* Thu tiền khách hàng theo kỳ hoặc theo hành vi trả nợ.
* Trạng thái hợp đồng: đang lưu hành, quá hạn, nợ xấu, tất toán.
* Dòng tiền thu/chi.
* Bản đồ realtime theo cửa hàng/khu vực.
* Cảnh báo thời tiết ảnh hưởng đến nhóm shipper.
* Các KPI realtime: giải ngân hôm nay, tổng thu hôm nay, net cashflow, PAR 1+, product mix, approval status, hourly flow, risk radar, live event stream.

## 3. Nguyên tắc mô phỏng nghiệp vụ

### 3.1. Không chia đều tuyệt đối cho tất cả chi nhánh

Không phải tất cả chi nhánh đều phát sinh hợp đồng trong cùng một giờ hoặc cùng một ngày.

Một số chi nhánh sẽ có nhiều hợp đồng hơn do:

* Thuộc khu vực metro như Hà Nội, TP.HCM.
* Nằm ở khu vực có nhiều tài xế công nghệ/shipper.
* Có hạng cửa hàng cao hơn: A+, A, B.
* Đang ở khung giờ cao điểm.
* Có yếu tố random theo traffic/hotness.
* Có ảnh hưởng thời tiết làm tăng nhu cầu vay ngắn hạn hoặc làm tăng rủi ro hụt thu.

Một số chi nhánh nhỏ hoặc ở khu vực tỉnh có thể ít hợp đồng, thậm chí không có hợp đồng trong một số khung giờ.

### 3.2. Mục tiêu volume

Mục tiêu mô phỏng:

* Toàn hệ thống: khoảng **1.000 - 5.000 hợp đồng/ngày**.
* Theo giờ hoạt động: khoảng **50 - 300 hợp đồng/giờ**.
* Hợp đồng được phân bổ ngẫu nhiên có trọng số theo khu vực, hạng chi nhánh, giờ trong ngày và yếu tố thời tiết.

Trong realtime mode, thời gian mô phỏng có thể chạy nhanh hơn thời gian thật. Ví dụ: 1 giây thật tương ứng 1 phút nghiệp vụ. Nhờ đó dashboard có đủ dữ liệu realtime để quan sát mà vẫn giữ logic phát sinh theo giờ/ngày.

### 3.3. Dữ liệu phải đủ quan hệ nghiệp vụ

Mỗi hợp đồng hoặc giao dịch thu tiền phải có đủ ngữ cảnh:

* Cửa hàng/PGD phát sinh.
* Tọa độ cửa hàng.
* Khu vực/tỉnh/thành.
* Nhân viên liên quan.
* Khách hàng.
* Tài sản hoặc thông tin tín chấp.
* Loại hình vay.
* Số tiền vay, số tiền duyệt, số tiền giải ngân.
* Lãi suất, kỳ hạn, hình thức trả nợ.
* Số dư gốc trước/sau thanh toán.
* Dòng tiền thu/chi.
* Trạng thái khoản vay.
* Thời tiết/khu vực nếu có ảnh hưởng realtime.

## 4. Luồng nghiệp vụ hợp đồng phát sinh

### 4.1. Bước 1 - Khách hàng thỏa thuận vay/cầm đồ

Khách hàng đến cửa hàng hoặc được tiếp nhận qua kênh bán hàng. Nhân viên ghi nhận nhu cầu vay, loại hình vay và tài sản đảm bảo nếu có.

Event phát sinh:

```text
customer_created
```

Ý nghĩa:

* Tạo hoặc ghi nhận khách hàng mới.
* Sinh thông tin nghề nghiệp, thu nhập, điểm tín dụng, phân khúc khách hàng.
* Với chiến dịch shipper, nhiều khách hàng thuộc phân khúc `App Driver` hoặc `Tài xế công nghệ/shipper`.

Dữ liệu chính:

* `CMND_CCCD`
* `TenKhachHang`
* `SoDienThoai`
* `NgheNghiep`
* `PhanKhuc`
* `ThuNhapHangThang`
* `DiemTinDung`
* `SoNguoiPhuThuoc`
* `DiaChi`

Bảng đích dự kiến:

```text
Dim_KhachHang
```

### 4.2. Bước 2 - Định giá tài sản

Nếu khoản vay có tài sản đảm bảo, hệ thống sinh event định giá tài sản. Với khoản tín chấp, tài sản có thể là `Không có tài sản đảm bảo`.

Event phát sinh:

```text
asset_appraised
```

Dữ liệu chính:

* `CMND_CCCD`
* `LoaiTaiSan`
* `MoTaChiTiet`
* `GiaTriDinhGia`
* `TinhTrangBanDau`
* `DuongDanAnh`

Bảng đích dự kiến:

```text
Dim_TaiSan
```

### 4.3. Bước 3 - Tạo hồ sơ/hợp đồng vay

Sau khi khách thỏa thuận, hệ thống phát sinh hợp đồng/hồ sơ vay.

Event phát sinh:

```text
loan_application_created
```

Ý nghĩa:

* Đây là thời điểm hợp đồng phát sinh về mặt dữ liệu.
* Event này phải được đổ vào database để dashboard và data warehouse biết có hồ sơ mới.
* Trạng thái ban đầu thường là `Chờ tiếp nhận`, `Chờ định giá`, `Đang thẩm định` hoặc `Chờ duyệt` tùy cách mô phỏng.

Dữ liệu chính:

* `SoHopDong`
* `CMND_CCCD`
* `MaCuaHang`
* `CuaHang_Key`
* `ToaDo_Key`
* `MaNhanVienSale`
* `TenLoaiHinh`
* `HinhThucTraNo`
* `SoTienMongMuon`
* `TrangThai`

Bảng đích dự kiến:

```text
Fact_GiaoDich
Fact_LichSuTrangThai
```

### 4.4. Bước 4 - Thẩm định và quyết định duyệt/từ chối

Hồ sơ được chấm điểm dựa trên:

* Điểm tín dụng.
* Thu nhập.
* DTI.
* LTV.
* Loại hình vay.
* Khách mới/khách quay lại.
* Rủi ro thời tiết/khu vực nếu áp dụng cho nhóm shipper.

Event phát sinh nếu được duyệt:

```text
loan_approved
```

Event phát sinh nếu bị từ chối:

```text
loan_rejected
```

Dữ liệu chính khi duyệt:

* `SoHopDong`
* `MaNguoiDuyet`
* `NgayDuyet`
* `SoTienDuyetVay`
* `LaiSuat`
* `PhiPhatTraTruoc`
* `ThoiHanVay_Thang`
* `KyTraNo_Thang`
* `SoTienTraMoiKy`
* `TrangThai = Đã duyệt`

Dữ liệu chính khi từ chối:

* `SoHopDong`
* `LyDoTuChoi`
* `TrangThai = Từ chối`

Bảng đích dự kiến:

```text
Fact_GiaoDich
Fact_LichSuTrangThai
```

### 4.5. Bước 5 - Giải ngân

Nếu hồ sơ được duyệt và khách không hủy, hệ thống phát sinh event giải ngân.

Event phát sinh:

```text
loan_disbursed
```

Ý nghĩa:

* Khoản vay chính thức được giải ngân.
* Dư nợ gốc ban đầu được hình thành.
* Hợp đồng chuyển sang trạng thái `Đã giải ngân` hoặc `Đang lưu hành`.

Dữ liệu chính:

* `SoHopDong`
* `MaCuaHang`
* `CuaHang_Key`
* `ToaDo_Key`
* `MaNhanVien`
* `SoTienGiaiNgan`
* `NgayGiaiNgan`
* `NgayDaoHan`
* `PhuongThuc`
* `ChungTuGoc`
* `TrangThai`
* `DuNoGocBanDau`
* `DuNoConLai`

Bảng đích dự kiến:

```text
Fact_GiaoDich
Fact_LichSuTrangThai
```

### 4.6. Bước 6 - Ghi nhận dòng tiền chi giải ngân

Khi giải ngân, dòng tiền chi ra khỏi quỹ/cửa hàng phải được ghi nhận.

Event phát sinh:

```text
cash_recorded
```

Dữ liệu chính:

* `MaCuaHang`
* `SoHopDong`
* `TenLoaiThuChi = Giải ngân bằng Tiền mặt / Giải ngân qua Chuyển khoản`
* `SoTienThu = 0`
* `SoTienChi = SoTienGiaiNgan`
* `PhuongThuc`
* `NguoiThucHien`
* `ChungTuGoc`
* `GhiChu`

Bảng đích dự kiến:

```text
Fact_ThuChi
```

## 5. Luồng nghiệp vụ khách trả tiền

### 5.1. Bước 1 - Chọn hợp đồng đang lưu hành

Thanh toán không nhất thiết phát sinh ngay sau hợp đồng mới. Khách trả tiền phải được sinh từ tập hợp các hợp đồng đang lưu hành.

Simulator cần duy trì danh sách `active loans`, gồm:

* `SoHopDong`
* `CMND_CCCD`
* `MaCuaHang`
* `CuaHang_Key`
* `ToaDo_Key`
* `MaNhanVien`
* `SoTienGiaiNgan`
* `DuNoConLai`
* `LaiSuat`
* `ThoiHanVay_Thang`
* `KyThanhToanHienTai`
* `HinhThucTraNo`
* `NgayDaoHan`
* `TrangThai`

### 5.2. Bước 2 - Sinh hành vi trả nợ

Hành vi trả nợ được random theo xác suất, có điều chỉnh theo:

* Điểm tín dụng.
* DTI.
* Nghề nghiệp.
* Phân khúc shipper.
* Điều kiện thời tiết.
* Tình trạng quá hạn hiện tại.

Các hành vi có thể gồm:

```text
on_time
early
partial
late_1_10
late_11_30
late_30_plus
bad_debt
```

### 5.3. Bước 3 - Ghi nhận thanh toán

Event phát sinh:

```text
repayment_paid
```

Dữ liệu chính:

* `SoHopDong`
* `MaCuaHang`
* `CuaHang_Key`
* `ToaDo_Key`
* `CMND_CCCD`
* `MaNhanVien`
* `SoTienGocDaTra`
* `SoTienLaiDaTra`
* `PhiPhatTreHan`
* `SoDuGocTruocThanhToan`
* `SoDuGocSauThanhToan`
* `DuNoConLai`
* `KyThanhToan`
* `HinhThucTraNo`
* `HanhViTraNo`
* `ChungTuGoc`
* `GhiChu`

Bảng đích dự kiến:

```text
Fact_LichSuTraNo
```

### 5.4. Bước 4 - Ghi nhận dòng tiền thu nợ

Với mỗi khoản khách trả, hệ thống cần ghi riêng dòng tiền theo bản chất:

```text
Thu nợ Gốc
Thu nợ Lãi
Thu phí phạt Trễ hạn
```

Event phát sinh:

```text
cash_recorded
```

Dữ liệu chính:

* `MaCuaHang`
* `SoHopDong`
* `TenLoaiThuChi`
* `SoTienThu`
* `SoTienChi = 0`
* `PhuongThuc`
* `NguoiThucHien`
* `ChungTuGoc`
* `GhiChu`

Bảng đích dự kiến:

```text
Fact_ThuChi
```

### 5.5. Bước 5 - Cập nhật trạng thái khoản vay

Sau thanh toán, hệ thống cập nhật trạng thái hợp đồng.

Các trường hợp:

* Nếu `DuNoConLai = 0`: chuyển sang `Tất toán` hoặc `Tất toán trước hạn`.
* Nếu trả trễ nhẹ: chuyển sang `Quá hạn nhẹ`.
* Nếu trễ dài: chuyển sang `Quá hạn`, `Nợ nghi ngờ`, hoặc `Nợ xấu`.
* Nếu trả bù và hết quá hạn: chuyển về `Đang lưu hành`.

Event phát sinh:

```text
loan_status_changed
```

Dữ liệu chính:

* `SoHopDong`
* `TrangThaiCu`
* `TrangThaiMoi`
* `LyDo`
* `MaNhanVien`
* `NgayThayDoi`

Bảng đích dự kiến:

```text
Fact_LichSuTrangThai
Fact_GiaoDich
```

## 6. Luồng nghiệp vụ thời tiết và ảnh hưởng shipper

### 6.1. Sinh dữ liệu thời tiết

Hệ thống có API hoặc simulator thời tiết để phát sinh dữ liệu theo khu vực/cửa hàng.

Event phát sinh:

```text
weather_updated
```

Dữ liệu chính:

* `ToaDo_Key`
* `MaCuaHang`
* `CuaHang_Key`
* `TenKhuVuc`
* `lat`
* `lng`
* `Weather_Code`
* `MoTaThoiTiet_VN`
* `NhietDo_2m`
* `LuongMua`
* `TocDoGio_10m`
* `risk`

Bảng đích dự kiến:

```text
Dim_MaThoiTiet
Fact_ThoiTiet_HienTai
Fact_ThoiTiet_TheoGio
```

### 6.2. Ảnh hưởng đến nghiệp vụ

Thời tiết ảnh hưởng đến nhóm tài xế công nghệ/shipper theo 2 hướng:

1. **Tăng nhu cầu vay ngắn hạn** khi thời tiết xấu làm giảm thu nhập trong ngày.
2. **Tăng rủi ro trả chậm** khi mưa lớn, bão, ngập hoặc điều kiện giao hàng xấu.

Các chỉ số dashboard có thể dùng:

* Weather risk theo khu vực.
* Income shock score.
* Số hợp đồng shipper bị ảnh hưởng.
* Ước tính hụt thu.
* PAR 1+ theo khu vực có mưa.

## 7. Luồng đi của dữ liệu end-to-end

### 7.1. Sơ đồ tổng quan

```text
Fake Data Simulator
        ↓
Kafka Topics
        ↓
Kafka Consumer
        ↓
PostgreSQL Data Warehouse
        ↓
Redis Snapshot / Redis PubSub
        ↓
FastAPI REST API + WebSocket
        ↓
Dashboard Real-time
```

## 8. Chi tiết từng tầng dữ liệu

### 8.1. Fake Data Simulator

Simulator chịu trách nhiệm sinh event nghiệp vụ.

Nhiệm vụ chính:

* Load dữ liệu master từ PostgreSQL nếu có: cửa hàng, tọa độ, loại hình vay, loại thu chi.
* Sinh khách hàng theo phân khúc, ưu tiên shipper.
* Sinh hợp đồng theo khu vực, hạng cửa hàng, giờ và random traffic.
* Sinh giải ngân và dòng tiền chi.
* Duy trì danh sách hợp đồng đang lưu hành.
* Sinh repayment từ hợp đồng đang lưu hành.
* Sinh thời tiết theo tọa độ/khu vực.
* Gửi event vào Kafka topic tương ứng.

### 8.2. Kafka Topics

Kafka đóng vai trò event bus.

Các topic chính:

```text
customer.events
asset.events
loan.application.events
loan.decision.events
loan.disbursement.events
loan.repayment.events
loan.status.events
cashflow.events
weather.events
```

Có thể có topic tổng hợp để debug:

```text
f88.business.events
```

Nguyên tắc partition key:

* Event theo khách hàng: dùng `CMND_CCCD`.
* Event theo hợp đồng: dùng `SoHopDong`.
* Event theo thời tiết/cửa hàng: dùng `MaCuaHang` hoặc `ToaDo_Key`.

### 8.3. Kafka Consumer

Consumer đọc event từ Kafka và xử lý theo nhóm:

```text
Dim handler
Fact handler
Realtime aggregator
```

Nhiệm vụ:

* Upsert dimension.
* Insert fact.
* Cập nhật trạng thái hợp đồng.
* Tính số dư gốc còn lại.
* Ghi lịch sử trả nợ.
* Ghi lịch sử trạng thái.
* Ghi dòng tiền thu/chi.
* Tính payload realtime để đưa vào Redis.

### 8.4. PostgreSQL Data Warehouse

PostgreSQL lưu dữ liệu dài hạn, phục vụ dashboard và phân tích.

Các bảng liên quan trực tiếp đến tab realtime:

```text
Dim_ThoiGian
Dim_ToaDo
Dim_CuaHang
Dim_NhanVien
Dim_KhachHang
Dim_TaiSan
Dim_LoaiHinh
Dim_TrangThai
Dim_QuyTien
Dim_LoaiThuChi
Dim_MaThoiTiet
Fact_GiaoDich
Fact_LichSuTrangThai
Fact_LichSuTraNo
Fact_ThuChi
Fact_ThoiTiet_HienTai
Fact_ThoiTiet_TheoGio
```

### 8.5. Redis

Redis dùng cho realtime layer.

Vai trò:

* Lưu snapshot dashboard mới nhất.
* Lưu feed realtime gần nhất.
* Lưu trạng thái map realtime.
* Pub/Sub payload mới cho FastAPI WebSocket.

Các key gợi ý:

```text
f88:realtime:snapshot
f88:realtime:feed
f88:realtime:map
f88:realtime:stats
f88:realtime:hourly
```

Channel pub/sub gợi ý:

```text
f88.realtime.dashboard
```

### 8.6. FastAPI

FastAPI cung cấp 2 nhóm endpoint chính cho tab realtime.

REST snapshot:

```text
GET /api/snapshot
```

Trả về trạng thái dashboard mới nhất từ Redis. Endpoint này giúp dashboard có dữ liệu ngay khi reload, không phụ thuộc vào việc có socket message vừa tới hay không.

WebSocket realtime:

```text
/ws/realtime
```

Đẩy payload realtime từ Redis Pub/Sub đến browser.

### 8.7. Dashboard realtime

Dashboard nhận payload và cập nhật:

* KPI cards.
* Approval/status bar.
* Product mix doughnut.
* Line chart giải ngân/thu theo giờ.
* Risk radar.
* Map marker theo chi nhánh/khu vực.
* Live event feed.

Payload kỳ vọng:

```json
{
  "stats": {
    "disbursement": 0,
    "collection": 0,
    "net_cashflow": 0,
    "par1": 0
  },
  "approval_bar": [0, 0, 0],
  "product_mix": [0, 0, 0, 0],
  "hourly": {
    "labels": [],
    "disbursement": [],
    "collection": []
  },
  "risk_radar": [0, 0, 0, 0, 0, 0],
  "feed": [],
  "map": []
}
```

## 9. Mapping event sang bảng Dim/Fact

### 9.1. `customer_created`

```text
Dim_KhachHang
```

Upsert theo `CMND_CCCD`.

### 9.2. `asset_appraised`

```text
Dim_TaiSan
```

Insert hoặc upsert tài sản theo khách hàng/hợp đồng nếu có khóa liên kết.

### 9.3. `loan_application_created`

```text
Fact_GiaoDich
Fact_LichSuTrangThai
```

Tạo bản ghi giao dịch/hợp đồng ban đầu.

### 9.4. `loan_approved` / `loan_rejected`

```text
Fact_GiaoDich
Fact_LichSuTrangThai
```

Cập nhật trạng thái, số tiền duyệt, lãi suất, kỳ hạn hoặc lý do từ chối.

### 9.5. `loan_disbursed`

```text
Fact_GiaoDich
Fact_LichSuTrangThai
Fact_ThuChi
```

Cập nhật ngày giải ngân, ngày đáo hạn, dư nợ ban đầu, trạng thái và dòng tiền chi giải ngân.

### 9.6. `repayment_paid`

```text
Fact_LichSuTraNo
Fact_ThuChi
Fact_GiaoDich
```

Insert lịch sử trả nợ, dòng tiền thu, cập nhật dư nợ còn lại.

### 9.7. `loan_status_changed`

```text
Fact_LichSuTrangThai
Fact_GiaoDich
```

Insert lịch sử trạng thái và cập nhật trạng thái hiện tại của hợp đồng.

### 9.8. `cash_recorded`

```text
Fact_ThuChi
```

Ghi nhận dòng tiền thu hoặc chi.

### 9.9. `weather_updated`

```text
Dim_MaThoiTiet
Fact_ThoiTiet_HienTai
Fact_ThoiTiet_TheoGio
```

Cập nhật thời tiết realtime và lịch sử theo giờ.

## 10. Công thức KPI realtime tab 1

### 10.1. Giải ngân hôm nay

```text
Tổng SoTienChi của Fact_ThuChi
với LoaiThuChi thuộc nhóm Giải ngân
và NgayGiaoDich = hôm nay
```

Hoặc lấy trực tiếp từ event `loan_disbursed` trong ngày.

### 10.2. Tổng thu hôm nay

```text
Tổng SoTienThu của Fact_ThuChi
với NhomThuChi = Thu
và NgayGiaoDich = hôm nay
```

Bao gồm:

* Thu nợ gốc.
* Thu nợ lãi.
* Thu phí phạt.
* Thu phí tất toán nếu có.

### 10.3. Net cashflow

```text
Net Cashflow = Tổng thu hôm nay - Tổng chi hôm nay
```

### 10.4. PAR 1+

```text
PAR 1+ = Dư nợ các hợp đồng quá hạn từ 1 ngày trở lên / Tổng dư nợ đang lưu hành
```

Trong mô phỏng realtime, có thể tạm tính theo trạng thái:

```text
PAR 1+ = Dư nợ của trạng thái Quá hạn nhẹ/Quá hạn/Nợ nghi ngờ/Nợ xấu / Tổng dư nợ active
```

### 10.5. Approval bar

```text
[Quá hạn, Chấp thuận, Từ chối]
```

Nguồn:

* Quá hạn: event `loan_status_changed` sang nhóm quá hạn.
* Chấp thuận: event `loan_approved`.
* Từ chối: event `loan_rejected`.

### 10.6. Product mix

```text
[Xe máy, Ô tô, Điện thoại, Tín chấp]
```

Nguồn:

* `TenLoaiHinh` trong hợp đồng.
* Mapping loại hình vay sang nhóm sản phẩm.

### 10.7. Hourly flow

Theo từng giờ trong ngày:

```text
Giải ngân = tổng tiền giải ngân theo giờ
Thu nợ = tổng tiền thu theo giờ
```

### 10.8. Risk radar

Các trục gợi ý:

```text
Thời tiết
Kẹt xe
Hụt thu
DTI cao
LTV cao
Fraud
```

Nguồn:

* Weather event.
* Customer/income event.
* Loan decision scoring.
* Repayment behavior.
* Status changes.

### 10.9. Map realtime

Mỗi marker trên bản đồ đại diện cho cửa hàng hoặc cụm giao dịch.

Field cần trả về dashboard:

```json
{
  "key": "CH0001",
  "name": "PGD ...",
  "area": "TP.HCM - Bình Thạnh",
  "lat": 10.8,
  "lng": 106.7,
  "risk": "medium",
  "weather": "Mưa vừa",
  "temp": "29°C",
  "loans": 42,
  "disb_m": 185.5
}
```

## 11. Thứ tự xử lý khuyến nghị trong consumer

### 11.1. Với hợp đồng mới

```text
1. Nhận customer_created
2. Upsert Dim_KhachHang
3. Nhận asset_appraised
4. Insert/Upsert Dim_TaiSan
5. Nhận loan_application_created
6. Lookup Dim_CuaHang, Dim_KhachHang, Dim_LoaiHinh, Dim_TrangThai
7. Insert Fact_GiaoDich
8. Insert Fact_LichSuTrangThai
9. Publish realtime snapshot
```

### 11.2. Với giải ngân

```text
1. Nhận loan_approved
2. Update Fact_GiaoDich
3. Insert Fact_LichSuTrangThai
4. Nhận loan_disbursed
5. Update Fact_GiaoDich: giải ngân, dư nợ, ngày đáo hạn
6. Insert Fact_LichSuTrangThai
7. Nhận cash_recorded chi giải ngân
8. Insert Fact_ThuChi
9. Update Redis snapshot
10. Publish WebSocket payload
```

### 11.3. Với thu tiền

```text
1. Nhận repayment_paid
2. Lookup hợp đồng trong Fact_GiaoDich
3. Insert Fact_LichSuTraNo
4. Update dư nợ còn lại trong Fact_GiaoDich
5. Nhận cash_recorded Thu nợ Gốc
6. Insert Fact_ThuChi
7. Nhận cash_recorded Thu nợ Lãi
8. Insert Fact_ThuChi
9. Nếu có phí phạt, insert thêm Fact_ThuChi
10. Nếu đổi trạng thái, insert Fact_LichSuTrangThai
11. Update Redis snapshot
12. Publish WebSocket payload
```

### 11.4. Với thời tiết

```text
1. Nhận weather_updated
2. Upsert Dim_MaThoiTiet nếu cần
3. Insert/Update Fact_ThoiTiet_HienTai
4. Insert Fact_ThoiTiet_TheoGio nếu dùng lịch sử giờ
5. Tính risk map theo khu vực/cửa hàng
6. Update Redis map state
7. Publish WebSocket payload
```

## 12. Nguyên tắc đảm bảo tính nhất quán dữ liệu

### 12.1. Khóa nghiệp vụ

* Khách hàng: `CMND_CCCD`.
* Hợp đồng: `SoHopDong`.
* Cửa hàng: `MaCuaHang` hoặc `CuaHang_Key`.
* Nhân viên: `MaNhanVien`.
* Tọa độ: `ToaDo_Key`.
* Loại hình vay: `TenLoaiHinh` hoặc `LoaiHinh_Key`.
* Loại thu chi: `TenLoaiThuChi` hoặc `LoaiThuChi_Key`.

### 12.2. Idempotency

Consumer nên xử lý idempotent theo `event_id` để tránh insert trùng khi Kafka retry hoặc consumer restart.

Khuyến nghị có bảng hoặc Redis set:

```text
processed_events
```

Gồm:

* `event_id`
* `event_type`
* `processed_at`
* `status`

### 12.3. Thứ tự event

Các event theo cùng hợp đồng nên dùng partition key là `SoHopDong` để giữ thứ tự xử lý trong Kafka partition.

### 12.4. Snapshot realtime

Redis snapshot cần được cập nhật sau mỗi batch nhỏ hoặc sau mỗi event quan trọng. Dashboard không nên query trực tiếp PostgreSQL cho từng tick realtime.

### 12.5. Dữ liệu âm/dư nợ âm

Khi xử lý repayment:

```text
SoDuGocSauThanhToan = max(0, SoDuGocTruocThanhToan - SoTienGocDaTra)
```

Không cho dư nợ âm.

### 12.6. Dòng tiền phải cân với nghiệp vụ

* Giải ngân: `SoTienChi > 0`, `SoTienThu = 0`.
* Thu nợ: `SoTienThu > 0`, `SoTienChi = 0`.
* Thu phí phạt: là dòng thu riêng.
* Nếu hợp đồng bị từ chối hoặc khách hủy: không sinh dòng chi giải ngân.

## 13. Docker flow mong muốn

Ở thư mục `be`, chỉ cần chạy:

```bash
docker compose up --build
```

Các service cần chạy:

```text
postgres_dw
redis
zookeeper
kafka
api
producer
consumer
```

Thứ tự phụ thuộc:

```text
postgres_dw + redis + kafka ready
        ↓
consumer start
        ↓
producer start
        ↓
api start
        ↓
dashboard connect /api/snapshot + /ws/realtime
```

Trong thực tế, API có thể start trước producer/consumer, miễn là `/api/snapshot` có fallback payload rỗng khi Redis chưa có dữ liệu.

## 14. Checklist hoàn thiện tab realtime

* [ ] Producer sinh đủ event hợp đồng phát sinh.
* [ ] Producer sinh repayment từ active loans, không chỉ từ hợp đồng mới.
* [ ] Event có đủ `MaCuaHang`, `CuaHang_Key`, `ToaDo_Key`, `MaNhanVien`, `CMND_CCCD`, `SoHopDong`.
* [ ] Consumer insert/update đúng Dim/Fact.
* [ ] Consumer cập nhật Redis snapshot.
* [ ] FastAPI trả đúng `/api/snapshot`.
* [ ] FastAPI push đúng `/ws/realtime`.
* [ ] Dashboard nhận đúng field `stats`, `approval_bar`, `product_mix`, `hourly`, `risk_radar`, `feed`, `map`.
* [ ] Map marker dùng đúng lat/lng từ `Dim_ToaDo`.
* [ ] KPI realtime không bị âm sai logic.
* [ ] PAR 1+ tính từ dư nợ còn lại, không tính từ số hợp đồng đơn thuần.
* [ ] Feed realtime có event hợp đồng, thu tiền, quá hạn, thời tiết.

## 15. Kết luận

Luồng nghiệp vụ chính của hệ thống gồm hai dòng phát sinh quan trọng:

1. **Khách thỏa thuận vay/cầm đồ → phát sinh hợp đồng → duyệt/từ chối → giải ngân → ghi dòng tiền chi.**
2. **Khách trả tiền → ghi lịch sử trả nợ → ghi dòng tiền thu → cập nhật số dư và trạng thái.**

Luồng dữ liệu kỹ thuật đi qua:

```text
Fake Data Simulator → Kafka → Consumer → PostgreSQL + Redis → FastAPI → WebSocket → Dashboard
```

Thiết kế này giúp dashboard realtime phản ánh được trạng thái vận hành theo thời gian gần thực tế, đồng thời dữ liệu vẫn được lưu đầy đủ trong data warehouse để phục vụ phân tích chiến lược, đặc biệt là chiến dịch tài chính bình dân cho nhóm shipper.
