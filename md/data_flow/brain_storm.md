Đã nhớ: **chỉ thiết kế logic, không đưa code**.

Dưới đây là thiết kế luồng dữ liệu mô phỏng cho project **quản trị công ty tín dụng cho vay cầm đồ**, dựa trên schema bạn gửi. Mình sẽ thiết kế theo hướng **mô phỏng vận hành thật**, tức là dữ liệu không được sinh ngẫu nhiên rời rạc, mà phải đi theo vòng đời nghiệp vụ: khách đến cửa hàng → tạo hồ sơ → định giá tài sản → duyệt/từ chối → giải ngân → thu nợ → quá hạn/tất toán → sinh dòng tiền, chi phí, lương thưởng, rủi ro.

Schema của bạn đã có các nhóm bảng rất phù hợp cho hướng này: `Dim_CuaHang`, `Dim_NhanVien`, `Dim_KhachHang`, `Dim_TaiSan`, `Fact_GiaoDich`, `Fact_LichSuTrangThai`, `Fact_LichSuTraNo`, `Fact_ThuChi`, `Fact_ChiPhiHoatDong`, `Fact_LuongThuong`, `Fact_KhauHao` và mart thời tiết.  Kafka sẽ đóng vai trò luồng sự kiện, vì Kafka được thiết kế để ghi/đọc/lưu trữ/xử lý event theo topic; Airflow sẽ điều phối batch/micro-batch theo DAG và dependency; PostgreSQL sẽ là nơi lưu staging, ODS và data mart. ([kafka.apache.org][1])

---

# 1. Tư duy tổng thể của luồng dữ liệu

Không nên mô phỏng bằng cách insert thẳng vào `Fact_GiaoDich`, `Fact_ThuChi`, `Fact_LichSuTraNo`. Làm vậy dữ liệu sẽ “đẹp” nhưng không giống thật.

Luồng hợp lý hơn là:

**Nguồn phát sinh sự kiện mô phỏng → Kafka topic → Staging PostgreSQL → Airflow xử lý → Dim/Fact trong Data Warehouse**

Mô hình này tạo cảm giác như công ty thật đang vận hành:

1. Mỗi cửa hàng phát sinh khách/hồ sơ theo từng giờ.
2. Mỗi hồ sơ có quá trình xử lý riêng, không phải tạo là giải ngân ngay.
3. Một số hồ sơ bị từ chối hoặc khách hủy.
4. Một số hồ sơ được duyệt nhưng giải ngân trễ.
5. Sau giải ngân, hệ thống sinh lịch thu nợ.
6. Đến kỳ, khách có thể trả đúng hạn, trả trễ, trả thiếu, tất toán sớm hoặc chuyển nợ xấu.
7. Mọi dòng tiền đều đổ vào `Fact_ThuChi`.
8. Mọi thay đổi trạng thái đều đổ vào `Fact_LichSuTrangThai`.
9. Hàng ngày/tháng phát sinh thêm chi phí, lương, hoa hồng, khấu hao.

Điểm quan trọng: **Fact không phải nơi sinh dữ liệu gốc**, mà là nơi ghi nhận kết quả đã xử lý từ event nghiệp vụ.

---

# 2. Các lớp dữ liệu nên có

## Lớp 1 — Master Data / dữ liệu nền

Đây là dữ liệu cứng hoặc bán tĩnh, nạp trước:

| Nhóm           | Bảng                                   | Vai trò                            |
| -------------- | -------------------------------------- | ---------------------------------- |
| Thời gian      | `Dim_ThoiGian`                         | Lịch ngày 2020–2030                |
| Địa điểm       | `Dim_ToaDo`, `Dim_CuaHang`             | 800 phòng giao dịch toàn quốc      |
| Nhân sự        | `Dim_NhanVien`                         | Nhân viên gắn với cửa hàng         |
| Danh mục vay   | `Dim_LoaiHinh`                         | Loại hình cầm đồ/tín chấp          |
| Dòng tiền      | `Dim_LoaiThuChi`, `Dim_QuyTien`        | Loại thu chi, quỹ tiền             |
| Trạng thái     | `Dim_TrangThai`                        | Trạng thái khoản vay               |
| Chi phí        | `Dim_KhoanMucChiPhi`, `Dim_NhaCungCap` | Danh mục chi phí                   |
| Tài sản nội bộ | `Dim_TaiSanNoiBo`                      | Máy tính, két sắt, camera, bàn ghế |

Các bảng này không nên sinh liên tục theo từng phút. Chúng nên được nạp ban đầu, sau đó cập nhật theo ngày hoặc theo tháng.

## Lớp 2 — Event nghiệp vụ mô phỏng

Đây là nơi Kafka phát huy tác dụng. Mỗi hành động thực tế nên là một event riêng.

Các nhóm event chính:

| Nhóm event                  | Ý nghĩa                                         |
| --------------------------- | ----------------------------------------------- |
| `customer_created`          | Khách hàng mới phát sinh                        |
| `customer_updated`          | Khách đổi địa chỉ, thu nhập, số người phụ thuộc |
| `asset_appraised`           | Tài sản được định giá                           |
| `loan_application_created`  | Hồ sơ vay được tạo                              |
| `loan_underwriting_started` | Bắt đầu thẩm định                               |
| `loan_approved`             | Hồ sơ được duyệt                                |
| `loan_rejected`             | Hồ sơ bị từ chối                                |
| `loan_cancelled`            | Khách hủy hoặc không nhận tiền                  |
| `loan_disbursed`            | Giải ngân                                       |
| `repayment_due`             | Đến kỳ phải trả                                 |
| `repayment_paid`            | Khách trả tiền                                  |
| `repayment_late`            | Trễ hạn                                         |
| `late_fee_charged`          | Phát sinh phí phạt                              |
| `early_settlement`          | Tất toán trước hạn                              |
| `loan_closed`               | Hợp đồng kết thúc                               |
| `asset_liquidated`          | Thanh lý tài sản                                |
| `opex_recorded`             | Ghi nhận chi phí vận hành                       |
| `payroll_calculated`        | Tính lương/hoa hồng                             |
| `depreciation_recorded`     | Ghi nhận khấu hao                               |
| `weather_observed`          | Ghi nhận thời tiết theo tọa độ                  |

## Lớp 3 — Staging PostgreSQL

Staging nên lưu event thô, gần giống Kafka payload.

Mục tiêu của staging:

* Lưu toàn bộ event nhận được.
* Có `event_id` để chống trùng.
* Có `event_time` để biết nghiệp vụ xảy ra lúc nào.
* Có `ingestion_time` để biết hệ thống nhận lúc nào.
* Có `source_topic` để trace event đến từ topic nào.
* Có `business_key`, ví dụ `SoHopDong`, `MaCuaHang`, `CMND_CCCD`.
* Có trạng thái xử lý: mới nhận, đã xử lý, lỗi, cần retry.

Staging không nên ép dữ liệu quá sạch ngay. Nó giống “bãi đáp dữ liệu”.

## Lớp 4 — ODS / operational snapshot

ODS là lớp trung gian thể hiện trạng thái hiện tại của nghiệp vụ:

* Hồ sơ hiện đang ở trạng thái nào.
* Khoản vay còn dư nợ bao nhiêu.
* Khách có bao nhiêu hợp đồng đang mở.
* Cửa hàng hôm nay phát sinh bao nhiêu hồ sơ.
* Kỳ trả nợ nào đang quá hạn.
* Dòng tiền nào đã đối soát.

ODS giúp xử lý logic trước khi đổ vào fact.

## Lớp 5 — Data Warehouse / Data Mart

Đây là lớp cuối cùng:

* `Fact_GiaoDich`: hồ sơ/hợp đồng vay.
* `Fact_LichSuTrangThai`: lịch sử trạng thái.
* `Fact_LichSuTraNo`: lịch sử trả nợ.
* `Fact_ThuChi`: dòng tiền thu/chi.
* `Fact_ChiPhiHoatDong`: chi phí hoạt động.
* `Fact_KhauHao`: khấu hao.
* `Fact_LuongThuong`: lương, hoa hồng.

---

# 3. Thiết kế mật độ phát sinh dữ liệu theo cửa hàng

Bạn có 800 phòng giao dịch, trong đó:

| Nhóm địa bàn       | Số điểm | Vai trò mô phỏng            |
| ------------------ | ------: | --------------------------- |
| Hà Nội + TP.HCM    |     500 | Lõi doanh thu, hồ sơ nhiều  |
| Thành phố lớn khác |     200 | Hồ sơ khá, tăng trưởng ổn   |
| Các tỉnh           |     100 | Hồ sơ ít hơn, dao động mạnh |

Không nên chia đều hồ sơ cho 800 điểm. Trong thực tế, dù cùng thành phố, vẫn có điểm rất đông và điểm rất vắng.

## Phân hạng cửa hàng

Mỗi cửa hàng nên được gán một cấp hoạt động cố định hoặc bán cố định:

| Hạng cửa hàng | Tỷ lệ cửa hàng | Đặc điểm                                                 |
| ------------- | -------------: | -------------------------------------------------------- |
| A+            |             5% | Cực đông, vị trí đẹp, gần chợ/khu dân cư/khu công nghiệp |
| A             |            15% | Đông, doanh thu cao                                      |
| B             |            35% | Trung bình khá                                           |
| C             |            35% | Vừa hoặc hơi thấp                                        |
| D             |            10% | Vắng, mới mở, khu vực yếu                                |

Với 800 cửa hàng, sẽ có khoảng:

| Hạng | Số cửa hàng ước tính |
| ---- | -------------------: |
| A+   |                   40 |
| A    |                  120 |
| B    |                  280 |
| C    |                  280 |
| D    |                   80 |

## Mật độ hồ sơ/ngày theo hạng

Trong bối cảnh **kinh doanh tốt, lượng người và hồ sơ đông**, có thể đặt mật độ như sau:

| Nhóm khu vực    |               A+ |     A |    B |   C |   D |
| --------------- | ---------------: | ----: | ---: | --: | --: |
| Hà Nội / TP.HCM | 35–70 hồ sơ/ngày | 18–35 | 7–17 | 2–7 | 0–2 |
| Thành phố lớn   |            25–50 | 12–25 | 5–13 | 1–5 | 0–1 |
| Tỉnh            |            12–28 |  6–14 |  2–8 | 0–3 | 0–1 |

Như vậy toàn hệ thống có thể sinh khoảng:

| Chỉ tiêu              |                         Mức mô phỏng hợp lý |
| --------------------- | ------------------------------------------: |
| Hồ sơ mới/ngày        |                                 3.500–6.500 |
| Hồ sơ mới/tháng       |                             100.000–190.000 |
| Hồ sơ được duyệt/ngày |                                 2.300–4.700 |
| Hồ sơ giải ngân/ngày  |                                 2.000–4.300 |
| Giao dịch thu nợ/ngày | 15.000–45.000 tùy số hợp đồng đang lưu hành |

Con số này làm hệ thống đủ “đông” để báo cáo đẹp, nhưng vẫn có phân hóa: không phải cửa hàng nào cũng đông.

---

# 4. Thuật toán mô phỏng nên dùng

## 4.1. Weighted Random — phân bổ theo trọng số

Dùng cho:

* Chọn cửa hàng phát sinh hồ sơ.
* Chọn nhân viên xử lý hồ sơ.
* Chọn loại hình vay.
* Chọn phương thức giải ngân.
* Chọn quỹ tiền.
* Chọn khả năng trả nợ.

Không chọn đều. Mỗi cửa hàng có một trọng số kinh doanh.

Trọng số cửa hàng nên được tính từ:

| Thành phần            | Tác động                                           |
| --------------------- | -------------------------------------------------- |
| Khu vực               | Hà Nội/TP.HCM cao hơn tỉnh                         |
| Hạng cửa hàng         | A+ cao hơn D                                       |
| Tuổi cửa hàng         | Cửa hàng mở lâu ổn định hơn                        |
| Số nhân viên          | Nhiều nhân viên xử lý được nhiều hồ sơ             |
| Ngày trong tuần       | Cuối tuần có thể đông hơn                          |
| Thời điểm trong tháng | Gần ngày lương/đầu tháng/cuối tháng ảnh hưởng mạnh |
| Thời tiết             | Mưa lớn làm giảm khách đến trực tiếp               |
| Chiến dịch marketing  | Làm tăng hồ sơ trong vài ngày                      |
| Yếu tố ngẫu nhiên     | Tạo dao động thực tế                               |

## 4.2. Negative Binomial — sinh số hồ sơ theo ngày/giờ

Không nên dùng random đều. Cũng không nên chỉ dùng Poisson thuần, vì Poisson thường làm dữ liệu quá “mượt”.

Nên dùng:

* **Poisson** cho cửa hàng nhỏ, ít biến động.
* **Negative Binomial** cho cửa hàng lớn, vì thực tế có ngày bùng nổ, ngày thấp bất thường.

Ví dụ logic:

* Cửa hàng A+ ở TP.HCM có trung bình 45 hồ sơ/ngày.
* Nhưng có ngày chỉ 30, có ngày 70.
* Khi chạy marketing hoặc sau ngày lương, có thể tăng 20–40%.
* Khi mưa lớn, có thể giảm 10–30%.

## 4.3. Seasonality — mùa vụ theo thời gian

Dữ liệu phải có nhịp thời gian.

### Theo giờ trong ngày

| Khung giờ   | Mật độ                                 |
| ----------- | -------------------------------------- |
| 08:00–09:00 | Thấp                                   |
| 09:00–11:30 | Cao                                    |
| 11:30–13:30 | Giảm                                   |
| 13:30–16:30 | Trung bình cao                         |
| 16:30–19:30 | Cao                                    |
| Sau 20:00   | Thấp hoặc không phát sinh tại cửa hàng |

### Theo ngày trong tuần

| Ngày           | Tác động                                                    |
| -------------- | ----------------------------------------------------------- |
| Thứ Hai        | Hồ sơ khá nhiều, xử lý tồn từ cuối tuần                     |
| Thứ Ba–Thứ Năm | Ổn định                                                     |
| Thứ Sáu        | Hồ sơ tăng nhẹ                                              |
| Thứ Bảy        | Cầm đồ xe máy/điện thoại tăng                               |
| Chủ Nhật       | Tùy mô hình, có thể giảm hoặc chỉ một số cửa hàng hoạt động |

### Theo tháng

| Giai đoạn          | Tác động                                          |
| ------------------ | ------------------------------------------------- |
| Ngày 1–5           | Nhiều khách trả nợ, một phần khách vay lại        |
| Ngày 10–20         | Hồ sơ mới ổn định                                 |
| Ngày 25–cuối tháng | Tăng thu nợ, tất toán, gia hạn                    |
| Cuối tháng         | Chi phí, lương, hoa hồng, khấu hao phát sinh mạnh |

## 4.4. Log-normal / Gamma — sinh số tiền vay

Số tiền vay thực tế không phân phối đều. Thường có nhiều khoản nhỏ và ít khoản rất lớn.

Nên dùng phân phối lệch phải:

* **Log-normal** cho số tiền khách mong muốn.
* **Gamma** cho giá trị tài sản.
* **Beta** cho tỷ lệ LTV, tức tỷ lệ duyệt vay trên giá trị tài sản.

Ví dụ:

| Loại hình              | Khoản vay phổ biến | Ghi chú                    |
| ---------------------- | -----------------: | -------------------------- |
| Điện thoại/laptop      |         2–20 triệu | Nhiều khoản nhỏ            |
| Xe máy giữ xe          |         5–50 triệu | Chủ lực                    |
| Xe máy giữ cà vẹt      |         8–70 triệu | Chủ lực, kỳ hạn dài hơn    |
| Ô tô giữ xe            |       80–700 triệu | Ít hồ sơ nhưng giá trị lớn |
| Ô tô giữ đăng ký       |      100–900 triệu | Giá trị cao                |
| Sổ đỏ/QSDĐ             |     200 triệu–2 tỷ | Ít nhưng rất lớn           |
| Tín chấp theo lương    |         5–80 triệu | Rủi ro cao hơn             |
| Tín chấp hộ kinh doanh |       10–150 triệu | Dao động mạnh              |

## 4.5. Markov Chain — mô phỏng chuyển trạng thái khoản vay

Khoản vay phải đi theo chuỗi trạng thái hợp lý.

Một vòng đời tiêu chuẩn:

**Tạo hồ sơ → Chờ thẩm định → Đang thẩm định → Được duyệt → Đã giải ngân → Đang lưu hành → Đã tất toán**

Các nhánh khác:

* Tạo hồ sơ → Từ chối.
* Tạo hồ sơ → Khách hủy.
* Được duyệt → Không giải ngân.
* Đang lưu hành → Quá hạn.
* Quá hạn → Thu hồi được.
* Quá hạn lâu → Thanh lý tài sản.
* Đang lưu hành → Tất toán trước hạn.

Bảng `Fact_LichSuTrangThai` của bạn rất phù hợp để ghi audit trail cho các chuyển trạng thái này. Mỗi lần trạng thái đổi, thêm một dòng mới và đóng `DenNgay_Key` của trạng thái trước. 

## 4.6. Risk Scoring — mô phỏng rủi ro

Không nên cho tỷ lệ duyệt random đơn giản. Cần mô phỏng điểm rủi ro.

Điểm rủi ro nên phụ thuộc vào:

| Yếu tố                    | Tác động                                        |
| ------------------------- | ----------------------------------------------- |
| Điểm tín dụng             | Cao thì dễ duyệt, ít trễ hạn                    |
| Thu nhập hàng tháng       | Thu nhập cao thì hạn mức cao hơn                |
| Số người phụ thuộc        | Nhiều người phụ thuộc thì rủi ro tăng           |
| Loại tài sản              | Có tài sản giữ xe rủi ro thấp hơn tín chấp      |
| Giá trị định giá          | Giá trị cao nhưng thanh khoản thấp vẫn rủi ro   |
| Tỷ lệ vay/giá trị tài sản | LTV cao thì rủi ro cao                          |
| Khu vực                   | Một số khu vực có nợ quá hạn cao hơn            |
| Lịch sử khách cũ          | Trả tốt thì ưu tiên duyệt                       |
| Nhân viên/cửa hàng        | Có cửa hàng tăng trưởng nóng thì rủi ro cao hơn |

---

# 5. Luồng nghiệp vụ chi tiết

## Bước 1 — Sinh khách hàng

Mỗi ngày, hệ thống sinh khách hàng mới và khách quay lại.

Tỷ lệ hợp lý:

| Loại khách                  |  Tỷ lệ |
| --------------------------- | -----: |
| Khách mới hoàn toàn         | 55–70% |
| Khách cũ quay lại vay tiếp  | 20–35% |
| Khách được giới thiệu       |  5–10% |
| Khách từng quá hạn quay lại |   1–5% |

Dữ liệu đổ vào:

* `Dim_KhachHang`

Logic xử lý:

* Nếu khách mới: tạo bản ghi mới.
* Nếu khách cũ nhưng đổi địa chỉ, thu nhập, nghề nghiệp: dùng SCD Type 2.
* Nếu khách có `CMND_CCCD` đã tồn tại và thông tin không đổi: không tạo khách mới.
* Nếu khách có thông tin mới: đóng bản ghi cũ bằng `NgayHetHieuLuc`, tạo bản ghi mới với `Version + 1`.

Các trường cần mô phỏng:

| Trường             | Logic                                                                   |
| ------------------ | ----------------------------------------------------------------------- |
| `TenKhachHang`     | Sinh tên thật kiểu Việt Nam                                             |
| `SoDienThoai`      | Unique tương đối                                                        |
| `CMND_CCCD`        | Unique tuyệt đối                                                        |
| `NgheNghiep`       | Công nhân, nhân viên văn phòng, tài xế, kinh doanh tự do, hộ kinh doanh |
| `ThuNhapHangThang` | Theo nghề nghiệp và khu vực                                             |
| `DiemTinDung`      | 300–850 hoặc thang điểm bạn tự quy chuẩn                                |
| `SoNguoiPhuThuoc`  | 0–4, đa số 0–2                                                          |
| `DiaChi`           | Theo khu vực cửa hàng phát sinh hồ sơ                                   |

## Bước 2 — Sinh tài sản cầm cố

Mỗi hồ sơ nên có một tài sản chính, trừ nhóm tín chấp.

Dữ liệu đổ vào:

* `Dim_TaiSan`

Logic theo `Dim_LoaiHinh`:

| Loại hình                | Tài sản                                                                    |
| ------------------------ | -------------------------------------------------------------------------- |
| Cầm đồ xe máy giữ xe     | Xe máy, có biển số, hãng, đời xe, tình trạng                               |
| Cầm đồ xe máy giữ cà vẹt | Xe máy, giấy tờ xe                                                         |
| Cầm đồ ô tô giữ xe       | Ô tô, tình trạng, biển số                                                  |
| Cầm đồ ô tô giữ đăng ký  | Ô tô, đăng ký xe                                                           |
| Sổ đỏ/QSDĐ               | Đất, nhà, giấy chứng nhận                                                  |
| Điện thoại/laptop        | Thiết bị điện tử                                                           |
| Tín chấp                 | Có thể tạo tài sản mô tả là “Không có tài sản đảm bảo” hoặc để logic riêng |

Các trường cần mô phỏng:

| Trường            | Logic                                          |
| ----------------- | ---------------------------------------------- |
| `LoaiTaiSan`      | Khớp với `LoaiHinh_Key`                        |
| `MoTaChiTiet`     | Có hãng, model, năm, tình trạng                |
| `GiaTriDinhGia`   | Dựa trên loại tài sản, năm sử dụng, tình trạng |
| `TinhTrangBanDau` | Tốt, khá, trầy xước, cũ, cần kiểm tra          |
| `DuongDanAnh`     | URL giả lập hoặc path nội bộ giả lập           |

## Bước 3 — Sinh hồ sơ vay

Dữ liệu đổ vào:

* `Fact_GiaoDich`

Một hồ sơ mới không nên có đầy đủ thông tin ngay. Ban đầu có thể chỉ có:

* khách hàng,
* tài sản,
* cửa hàng,
* nhân viên sale,
* loại hình,
* số tiền mong muốn,
* trạng thái chờ thẩm định.

Sau khi duyệt mới bổ sung:

* người duyệt,
* ngày duyệt,
* số tiền duyệt vay,
* lãi suất,
* kỳ hạn,
* ngày giải ngân,
* ngày đáo hạn,
* số tiền trả mỗi kỳ.

Bảng `Fact_GiaoDich` của bạn có đủ trường để lưu toàn bộ vòng đời hồ sơ vay, gồm khách hàng, tài sản, loại hình, ngày giải ngân, ngày đáo hạn, trạng thái, cửa hàng, nhân viên sale, người duyệt, số tiền mong muốn, số tiền duyệt vay, lãi suất và kỳ hạn. 

### Tỷ trọng loại hình vay đề xuất

Vì đây là công ty cầm đồ/tín dụng, nhóm xe máy nên chiếm tỷ trọng cao.

| Loại hình                | Tỷ lệ hồ sơ |
| ------------------------ | ----------: |
| Cầm đồ xe máy giữ cà vẹt |      30–35% |
| Cầm đồ xe máy giữ xe     |      22–28% |
| Điện thoại/laptop        |      12–18% |
| Ô tô giữ đăng ký         |       6–10% |
| Ô tô giữ xe              |        3–7% |
| Sổ đỏ/QSDĐ               |        2–5% |
| Tín chấp theo lương      |        5–8% |
| Tín chấp hộ kinh doanh   |        4–7% |

### Tỷ lệ duyệt đề xuất

Vì giả định kinh doanh tốt:

| Loại hồ sơ             | Tỷ lệ duyệt |
| ---------------------- | ----------: |
| Xe máy giữ xe          |      78–88% |
| Xe máy giữ cà vẹt      |      70–82% |
| Ô tô giữ xe            |      75–85% |
| Ô tô giữ đăng ký       |      68–80% |
| Sổ đỏ/QSDĐ             |      60–75% |
| Điện thoại/laptop      |      65–78% |
| Tín chấp theo lương    |      45–62% |
| Tín chấp hộ kinh doanh |      40–58% |

Tỷ lệ duyệt không nên cố định. Nó phải giảm khi:

* điểm tín dụng thấp,
* thu nhập thấp,
* LTV cao,
* tài sản cũ,
* khách có lịch sử trễ hạn,
* cửa hàng đang tăng trưởng quá nóng.

## Bước 4 — Sinh thẩm định và phê duyệt

Mỗi hồ sơ đi qua thẩm định.

Luồng trạng thái:

| Trạng thái       | Ý nghĩa                              |
| ---------------- | ------------------------------------ |
| Chờ tiếp nhận    | Khách mới tạo hồ sơ                  |
| Chờ định giá     | Đang kiểm tra tài sản                |
| Đang thẩm định   | Kiểm tra thông tin, định giá, rủi ro |
| Chờ duyệt        | Hồ sơ đủ điều kiện đưa lên cấp duyệt |
| Đã duyệt         | Được phê duyệt hạn mức               |
| Từ chối          | Không đạt điều kiện                  |
| Khách hủy        | Khách không tiếp tục                 |
| Đã giải ngân     | Tiền đã chi cho khách                |
| Đang lưu hành    | Khoản vay đang còn dư nợ             |
| Quá hạn          | Khách trễ kỳ trả                     |
| Tất toán         | Khách trả xong                       |
| Thanh lý tài sản | Thu hồi nợ qua tài sản               |
| Nợ xấu           | Quá hạn dài                          |

Mỗi lần trạng thái đổi, ghi vào:

* `Fact_LichSuTrangThai`

Logic quan trọng:

* `Fact_GiaoDich.TrangThai_Key` lưu trạng thái hiện tại.
* `Fact_LichSuTrangThai` lưu toàn bộ lịch sử.
* Không được có hai trạng thái hiện tại cùng lúc cho một `GiaoDich_Key`.
* Trạng thái trước phải có `DenNgay_Key`.
* Trạng thái mới có `DenNgay_Key = NULL`.

## Bước 5 — Giải ngân

Khi hồ sơ được duyệt, chưa chắc giải ngân ngay.

Tỷ lệ hợp lý:

| Tình huống                            |  Tỷ lệ |
| ------------------------------------- | -----: |
| Duyệt và giải ngân trong ngày         | 65–80% |
| Duyệt hôm nay, giải ngân ngày hôm sau | 10–20% |
| Duyệt nhưng khách hủy                 |  5–10% |
| Duyệt nhưng treo hồ sơ                |   1–5% |

Khi giải ngân, phải sinh đồng thời:

| Bảng                   | Dòng dữ liệu                                         |
| ---------------------- | ---------------------------------------------------- |
| `Fact_GiaoDich`        | cập nhật ngày giải ngân, ngày đáo hạn, số tiền duyệt |
| `Fact_LichSuTrangThai` | thêm trạng thái “Đã giải ngân”                       |
| `Fact_ThuChi`          | ghi dòng chi tiền giải ngân                          |

Trong `Fact_ThuChi`, giải ngân là dòng tiền ra:

| Trường           | Logic                                 |
| ---------------- | ------------------------------------- |
| `LoaiThuChi_Key` | Giải ngân tiền mặt hoặc chuyển khoản  |
| `SoTienChi`      | bằng số tiền duyệt vay                |
| `SoTienThu`      | 0                                     |
| `GiaoDich_Key`   | gắn với hợp đồng                      |
| `CuaHang_Key`    | cửa hàng giải ngân                    |
| `QuyTien_Key`    | quỹ tiền mặt hoặc tài khoản ngân hàng |
| `ChungTuGoc`     | mã phiếu chi / mã giải ngân           |

Bảng `Fact_ThuChi` của bạn cho phép gắn dòng thu/chi với hợp đồng qua `GiaoDich_Key`, đồng thời cũng cho phép dòng không gắn hợp đồng, ví dụ chi phí vận hành. 

---

# 6. Logic trả nợ và dòng tiền

Sau giải ngân, hệ thống phải sinh lịch trả nợ theo loại hình.

## Nhóm “gốc cuối kỳ, lãi trả hàng tháng”

Áp dụng cho:

* Xe máy giữ xe.
* Ô tô giữ xe.
* Sổ đỏ/QSDĐ.
* Điện thoại/laptop.

Luồng tiền:

* Hàng tháng thu lãi.
* Cuối kỳ thu gốc.
* Có thể có phí lưu kho/bãi.
* Có thể có phí phạt trễ hạn.
* Có thể tất toán trước hạn.

## Nhóm “gốc lãi trả đều hàng tháng”

Áp dụng cho:

* Xe máy giữ cà vẹt.
* Ô tô giữ đăng ký.
* Tín chấp theo lương.

Luồng tiền:

* Mỗi kỳ trả một phần gốc + lãi.
* Nếu trễ hạn thì phát sinh phí phạt.
* Nếu tất toán sớm thì có phí tất toán trước hạn.

## Nhóm “trả góp linh hoạt”

Áp dụng cho:

* Tín chấp hộ kinh doanh.

Luồng tiền:

* Khách có thể trả không đều.
* Có tháng trả đủ, có tháng trả một phần.
* Dễ phát sinh quá hạn hơn.

## Xác suất hành vi trả nợ

Vì tình hình kinh doanh tốt, khách trả nợ phần lớn ổn định:

| Hành vi                |    Tỷ lệ |
| ---------------------- | -------: |
| Trả đúng hạn           |   72–84% |
| Trả sớm vài ngày       |    5–10% |
| Trả trễ 1–10 ngày      |    6–12% |
| Trả một phần           |     4–8% |
| Trễ 11–30 ngày         |     2–5% |
| Trễ trên 30 ngày       |     1–3% |
| Chuyển nợ xấu/thanh lý | 0.3–1.5% |

Tỷ lệ này phải phụ thuộc vào:

* điểm tín dụng,
* loại hình vay,
* tỷ lệ LTV,
* khu vực,
* lịch sử trả nợ,
* số kỳ đã trả,
* số ngày gần cuối tháng,
* thời tiết hoặc mùa vụ kinh doanh.

## Khi khách trả nợ

Mỗi lần khách trả tiền phải sinh tối thiểu hai loại bản ghi:

| Bảng               | Ý nghĩa                                                   |
| ------------------ | --------------------------------------------------------- |
| `Fact_LichSuTraNo` | ghi khách trả bao nhiêu gốc, bao nhiêu lãi, bao nhiêu phí |
| `Fact_ThuChi`      | ghi dòng tiền thực thu vào quỹ                            |

`Fact_LichSuTraNo` trong schema của bạn đã có các trường tách gốc, lãi, phí phạt trễ hạn, rất phù hợp để phân tích thu hồi vốn. 

Trong `Fact_ThuChi`, nên tách dòng tiền theo loại:

| Loại tiền        | `LoaiThuChi_Key`           |
| ---------------- | -------------------------- |
| Thu gốc          | Thu nợ gốc                 |
| Thu lãi          | Thu nợ lãi                 |
| Thu phí phạt     | Thu phí phạt trễ hạn       |
| Thu phí tất toán | Thu phí tất toán trước hạn |
| Thu phí lưu kho  | Thu phí lưu kho/bãi        |
| Thu thanh lý     | Thu thanh lý tài sản       |

Không nên gom tất cả vào một dòng “thu nợ”, vì sau này báo cáo sẽ khó tách doanh thu lãi, thu hồi gốc và phí.

---

# 7. Logic quá hạn, nợ xấu và thanh lý tài sản

Khoản vay không nên tất cả đều đẹp. Kinh doanh tốt vẫn phải có quá hạn và nợ xấu.

## Trạng thái theo số ngày quá hạn

| Số ngày quá hạn | Trạng thái                                 |
| --------------- | ------------------------------------------ |
| 1–10 ngày       | Quá hạn nhẹ                                |
| 11–30 ngày      | Quá hạn cần nhắc nợ                        |
| 31–60 ngày      | Nợ chú ý                                   |
| 61–90 ngày      | Nợ nghi ngờ                                |
| Trên 90 ngày    | Nợ xấu                                     |
| Sau xử lý       | Thanh lý tài sản hoặc xóa/thu hồi một phần |

## Logic nhắc nợ

Mỗi kỳ trễ hạn nên phát sinh hành động nghiệp vụ, dù schema hiện tại chưa có bảng riêng cho nhắc nợ. Có thể phản ánh gián tiếp qua:

* `Fact_LichSuTrangThai.GhiChu`
* `Fact_LichSuTraNo.GhiChu`
* `Fact_ThuChi.GhiChu`

Ví dụ ghi chú:

* Nhắc nợ lần 1.
* Khách hẹn thanh toán.
* Khách trả một phần.
* Chuyển xử lý thu hồi.
* Đề xuất thanh lý tài sản.

## Logic thanh lý tài sản

Chỉ áp dụng cho khoản có tài sản giữ hoặc tài sản có thể xử lý.

Tỷ lệ thanh lý nên rất thấp:

| Nhóm              | Tỷ lệ thanh lý trên khoản quá hạn nặng |
| ----------------- | -------------------------------------: |
| Xe máy giữ xe     |                                 10–25% |
| Ô tô giữ xe       |                                  5–15% |
| Điện thoại/laptop |                                 15–30% |
| Sổ đỏ/QSDĐ        |                    rất thấp, xử lý lâu |
| Tín chấp          |                 không thanh lý tài sản |

Khi thanh lý:

* `Fact_LichSuTrangThai`: chuyển sang “Thanh lý tài sản”.
* `Fact_ThuChi`: ghi dòng “Thu thanh lý tài sản”.
* `Fact_GiaoDich`: trạng thái cuối có thể là tất toán do thanh lý hoặc nợ xấu đã xử lý.

---

# 8. Logic chi phí vận hành

Chi phí không nên sinh đều nhau cho mọi cửa hàng. Cửa hàng lớn phải tốn nhiều hơn.

Dữ liệu đổ vào:

* `Fact_ChiPhiHoatDong`
* `Fact_ThuChi`

Các nhóm chi phí nên có:

| Nhóm chi phí         | Tần suất        | Logic                                |
| -------------------- | --------------- | ------------------------------------ |
| Thuê mặt bằng        | Hàng tháng      | Cao ở Hà Nội/TP.HCM, thấp hơn ở tỉnh |
| Điện nước            | Hàng tháng      | Phụ thuộc hạng cửa hàng              |
| Internet/điện thoại  | Hàng tháng      | Gần cố định                          |
| Bảo vệ/an ninh       | Hàng tháng      | Cao ở cửa hàng giữ nhiều tài sản     |
| Marketing địa phương | Theo chiến dịch | Tăng hồ sơ sau đó                    |
| Văn phòng phẩm       | Hàng tháng      | Nhỏ                                  |
| Sửa chữa/bảo trì     | Ngẫu nhiên      | Không đều                            |
| Phí ngân hàng        | Theo giao dịch  | Tăng theo chuyển khoản               |
| Chi phí lưu kho/bãi  | Hàng tháng      | Cao với cửa hàng giữ xe              |

Bảng `Fact_ChiPhiHoatDong` có các trường đủ để ghi nhận ngày phát sinh, cửa hàng, khoản mục, nhà cung cấp, số tiền trước thuế, VAT, tổng tiền, trạng thái thanh toán và phiếu chi liên quan. 

## Mật độ chi phí

| Loại cửa hàng | Số chứng từ chi phí/tháng |
| ------------- | ------------------------: |
| A+            |                     30–60 |
| A             |                     20–40 |
| B             |                     12–25 |
| C             |                      8–18 |
| D             |                      4–12 |

Không phải chi phí nào cũng thanh toán ngay:

| Trạng thái thanh toán   |  Tỷ lệ |
| ----------------------- | -----: |
| Đã thanh toán ngay      | 65–80% |
| Chưa thanh toán         | 15–25% |
| Thanh toán sau vài ngày |  5–15% |

Khi thanh toán chi phí, cần sinh thêm dòng `Fact_ThuChi` với loại “Chi phí vận hành Cửa hàng”.

---

# 9. Logic lương, thưởng, hoa hồng

Dữ liệu đổ vào:

* `Fact_LuongThuong`
* Có thể sinh thêm `Fact_ThuChi` khi chi trả lương.

Bảng `Fact_LuongThuong` của bạn đã có lương cơ bản, hoa hồng giải ngân, hoa hồng thu nợ, phụ cấp và tổng thu nhập. 

## Cơ cấu nhân sự theo cửa hàng

| Hạng cửa hàng | Số nhân viên |
| ------------- | -----------: |
| A+            |         8–15 |
| A             |         5–10 |
| B             |          3–6 |
| C             |          2–4 |
| D             |          1–3 |

Chức vụ nên gồm:

* Cửa hàng trưởng.
* Giao dịch viên.
* Nhân viên thẩm định.
* Nhân viên thu hồi nợ.
* Nhân viên kho/tài sản.
* Nhân viên kế toán/quỹ.

## Logic hoa hồng

Hoa hồng nên phụ thuộc vào:

| Thành phần             | Ý nghĩa                       |
| ---------------------- | ----------------------------- |
| Doanh số giải ngân     | Nhân viên sale được hưởng     |
| Tỷ lệ hồ sơ được duyệt | Khuyến khích hồ sơ chất lượng |
| Tỷ lệ thu nợ đúng hạn  | Giảm nếu nợ xấu cao           |
| Thu lãi thực tế        | Gắn với doanh thu             |
| Thu phí                | Có thể tính bonus nhỏ         |
| Cửa hàng đạt KPI       | Thưởng thêm                   |

Không nên chỉ tính hoa hồng theo giải ngân, vì như vậy mô phỏng sẽ tạo hành vi tăng trưởng nóng nhưng rủi ro cao. Nên có hệ số phạt nếu cửa hàng có tỷ lệ quá hạn tăng.

---

# 10. Logic khấu hao tài sản nội bộ

Dữ liệu đổ vào:

* `Dim_TaiSanNoiBo`
* `Fact_KhauHao`

Tài sản nội bộ nên gồm:

| Loại tài sản | Ví dụ                            | Thời gian khấu hao |
| ------------ | -------------------------------- | -----------------: |
| Thiết bị IT  | Laptop, máy in, máy scan         |        24–36 tháng |
| Nội thất     | Bàn ghế, tủ hồ sơ                |        36–60 tháng |
| An ninh      | Camera, két sắt                  |        36–60 tháng |
| Kho bãi      | Kệ để tài sản, thiết bị bảo quản |        36–72 tháng |

Mỗi tháng, với tài sản còn giá trị, ghi một dòng `Fact_KhauHao`.

Logic:

* Cửa hàng mới mở sẽ phát sinh nhiều tài sản nội bộ ban đầu.
* Cửa hàng lớn có nhiều tài sản hơn.
* Một số tài sản có thể hết khấu hao nhưng vẫn đang sử dụng.
* Khấu hao không tạo dòng tiền thực chi trong tháng, nhưng là chi phí kế toán.

---

# 11. Logic thời tiết

Bạn có `Dim_ToaDo`, `Fact_ThoiTiet_HienTai`, `Fact_ThoiTiet_TheoGio`, vì vậy có thể dùng thời tiết làm biến ảnh hưởng đến kinh doanh.

Dữ liệu thời tiết không chỉ để trang trí. Nên dùng nó để tác động đến hành vi:

| Điều kiện thời tiết | Tác động mô phỏng                                      |
| ------------------- | ------------------------------------------------------ |
| Mưa lớn             | Giảm khách đến cửa hàng 10–30%                         |
| Mưa kéo dài         | Tăng trễ hạn nhẹ do khách ngại đi thanh toán           |
| Nắng nóng           | Giảm nhẹ khách giữa trưa                               |
| Cuối tuần trời đẹp  | Tăng hồ sơ xe máy/ô tô                                 |
| Bão/áp thấp         | Giảm mạnh hồ sơ tại khu vực bị ảnh hưởng               |
| Mưa tại tỉnh        | Có thể tăng vay ngắn hạn với hộ kinh doanh/nông nghiệp |

Điểm hay của schema bạn là cửa hàng gắn với tọa độ, còn thời tiết cũng gắn với tọa độ, nên có thể mô phỏng tác động theo từng địa bàn. 

---

# 12. Thiết kế Kafka topic logic

Kafka nên chia topic theo nghiệp vụ, không nên dồn tất cả vào một topic. Topic là đơn vị tổ chức event trong Kafka; producer ghi event vào topic và consumer đọc từ topic. ([docs.confluent.io][2])

## Nhóm topic đề xuất

| Topic                      | Nội dung                           |
| -------------------------- | ---------------------------------- |
| `branch_activity_events`   | Lượt khách, tương tác tại cửa hàng |
| `customer_events`          | Tạo mới/cập nhật khách hàng        |
| `asset_events`             | Định giá tài sản                   |
| `loan_application_events`  | Tạo hồ sơ, sửa hồ sơ               |
| `loan_decision_events`     | Duyệt, từ chối, hủy                |
| `loan_disbursement_events` | Giải ngân                          |
| `repayment_events`         | Đến hạn, trả nợ, trả thiếu         |
| `loan_status_events`       | Chuyển trạng thái khoản vay        |
| `cashflow_events`          | Thu/chi tiền                       |
| `opex_events`              | Chi phí vận hành                   |
| `payroll_events`           | Lương thưởng                       |
| `depreciation_events`      | Khấu hao                           |
| `weather_events`           | Thời tiết theo tọa độ              |

## Partition key nên dùng

| Nhóm event | Partition key                    |
| ---------- | -------------------------------- |
| Hồ sơ vay  | `GiaoDich_Key` hoặc `SoHopDong`  |
| Khách hàng | `KhachHang_Key` hoặc `CMND_CCCD` |
| Cửa hàng   | `CuaHang_Key`                    |
| Trả nợ     | `GiaoDich_Key`                   |
| Dòng tiền  | `CuaHang_Key` hoặc `Phieu_ID`    |
| Thời tiết  | `ToaDo_Key`                      |

Lý do: các event liên quan cùng một hợp đồng nên đi cùng partition để giữ thứ tự xử lý.

---

# 13. Thiết kế Airflow DAG logic

Airflow nên không trực tiếp sinh từng event nhỏ theo giây. Kafka xử lý phần real-time/micro-event. Airflow nên làm vai trò điều phối batch, kiểm tra, tổng hợp, retry. Airflow dùng DAG để biểu diễn workflow gồm các task có dependency; scheduler sẽ trigger task khi dependency hoàn tất. ([Apache Airflow][3])

## DAG 1 — Nạp dữ liệu nền

Tần suất: khi khởi tạo hoặc khi cần refresh.

Nhiệm vụ:

1. Nạp `Dim_ThoiGian`.
2. Nạp `Dim_ToaDo`.
3. Nạp `Dim_CuaHang`.
4. Nạp `Dim_NhanVien`.
5. Nạp `Dim_LoaiHinh`.
6. Nạp `Dim_LoaiThuChi`.
7. Nạp `Dim_TrangThai`.
8. Nạp danh mục chi phí, quỹ tiền, nhà cung cấp.

Chạy trước tất cả các DAG còn lại.

## DAG 2 — Sinh event hoạt động hàng ngày

Tần suất: mỗi giờ hoặc mỗi 15 phút.

Nhiệm vụ:

1. Tính mật độ hồ sơ theo cửa hàng trong khung giờ hiện tại.
2. Sinh event khách hàng.
3. Sinh event tài sản.
4. Sinh event tạo hồ sơ.
5. Đẩy vào Kafka topic tương ứng.
6. Ghi metadata batch.

## DAG 3 — Xử lý hồ sơ tín dụng

Tần suất: mỗi 15 phút hoặc mỗi giờ.

Nhiệm vụ:

1. Lấy event từ staging.
2. Validate khách hàng, cửa hàng, nhân viên.
3. Tạo/cập nhật `Dim_KhachHang`.
4. Tạo `Dim_TaiSan`.
5. Tạo/cập nhật `Fact_GiaoDich`.
6. Ghi `Fact_LichSuTrangThai`.
7. Đưa hồ sơ sang trạng thái tiếp theo.

## DAG 4 — Xử lý duyệt vay và giải ngân

Tần suất: mỗi giờ trong giờ làm việc.

Nhiệm vụ:

1. Lấy hồ sơ đang chờ duyệt.
2. Tính điểm rủi ro.
3. Quyết định duyệt/từ chối/hủy.
4. Với hồ sơ được duyệt, sinh xác suất giải ngân.
5. Ghi dòng chi tiền vào `Fact_ThuChi`.
6. Cập nhật trạng thái khoản vay.

## DAG 5 — Sinh và xử lý trả nợ

Tần suất: hàng ngày, có thể chạy sáng sớm và cuối ngày.

Nhiệm vụ:

1. Tìm các hợp đồng đến kỳ.
2. Sinh hành vi thanh toán.
3. Ghi `Fact_LichSuTraNo`.
4. Ghi `Fact_ThuChi`.
5. Cập nhật trạng thái đúng hạn/quá hạn/tất toán.
6. Sinh phí phạt nếu trễ hạn.
7. Sinh thanh lý nếu quá hạn nặng.

## DAG 6 — Chi phí vận hành

Tần suất: hàng ngày và cuối tháng.

Nhiệm vụ:

1. Sinh chi phí định kỳ.
2. Sinh chi phí ngẫu nhiên.
3. Ghi `Fact_ChiPhiHoatDong`.
4. Nếu đã thanh toán, ghi `Fact_ThuChi`.
5. Nếu chưa thanh toán, để trạng thái chờ.

## DAG 7 — Lương thưởng

Tần suất: cuối tháng.

Nhiệm vụ:

1. Tổng hợp doanh số giải ngân theo nhân viên.
2. Tổng hợp thu nợ theo nhân viên/cửa hàng.
3. Tính hoa hồng.
4. Tính phạt KPI nếu nợ xấu cao.
5. Ghi `Fact_LuongThuong`.
6. Ghi dòng chi lương vào `Fact_ThuChi`.

## DAG 8 — Khấu hao

Tần suất: cuối tháng.

Nhiệm vụ:

1. Tìm tài sản nội bộ còn khấu hao.
2. Tính khấu hao tháng.
3. Ghi `Fact_KhauHao`.

## DAG 9 — Data Quality

Tần suất: sau mỗi batch chính.

Kiểm tra:

| Kiểm tra             | Điều kiện                                                        |
| -------------------- | ---------------------------------------------------------------- |
| FK hợp lệ            | `CuaHang_Key`, `KhachHang_Key`, `TaiSan_Key`, `Date_Key` tồn tại |
| Không âm             | Số tiền vay, thu, chi không âm                                   |
| Ngày hợp lý          | Ngày đáo hạn sau ngày giải ngân                                  |
| Trạng thái hợp lý    | Không tất toán trước khi giải ngân                               |
| Dòng tiền hợp lý     | Giải ngân phải là `SoTienChi`, thu nợ phải là `SoTienThu`        |
| Không trùng event    | `event_id` duy nhất                                              |
| Không trùng hợp đồng | `SoHopDong` duy nhất                                             |
| Tỷ lệ duyệt          | Không vượt ngưỡng bất thường                                     |
| Tỷ lệ nợ xấu         | Có nhưng không quá vô lý                                         |
| Cửa hàng vắng/đông   | Phù hợp hạng cửa hàng                                            |

---

# 14. Logic đổ dữ liệu vào từng bảng chính

## `Dim_KhachHang`

Nguồn: `customer_created`, `customer_updated`.

Xử lý:

* Khách mới: insert bản ghi mới.
* Khách cũ không đổi thông tin: giữ nguyên.
* Khách cũ đổi thông tin quan trọng: tạo version mới.
* Chỉ một bản ghi có `IsCurrent = TRUE`.

Trường cần quan tâm:

* `CMND_CCCD` là business key.
* `NgayHieuLuc`, `NgayHetHieuLuc`, `IsCurrent`, `Version` dùng cho SCD Type 2.

## `Dim_TaiSan`

Nguồn: `asset_appraised`.

Xử lý:

* Mỗi hồ sơ vay có một tài sản chính.
* Giá trị định giá phải liên quan đến loại hình vay.
* Tài sản giá trị cao phải ít xuất hiện hơn tài sản phổ biến.

## `Fact_GiaoDich`

Nguồn: `loan_application_created`, `loan_approved`, `loan_rejected`, `loan_disbursed`, `loan_closed`.

Xử lý:

* Khi tạo hồ sơ: tạo dòng ban đầu.
* Khi duyệt: cập nhật số tiền duyệt, lãi suất, người duyệt, ngày duyệt.
* Khi từ chối: cập nhật lý do từ chối, trạng thái từ chối.
* Khi giải ngân: cập nhật ngày giải ngân, ngày đáo hạn.
* Khi tất toán: cập nhật trạng thái cuối.

Không nên tạo một dòng mới cho mỗi trạng thái của cùng hợp đồng trong `Fact_GiaoDich`; trạng thái chi tiết nên nằm ở `Fact_LichSuTrangThai`.

## `Fact_LichSuTrangThai`

Nguồn: `loan_status_events`.

Xử lý:

* Append-only.
* Mỗi lần đổi trạng thái thêm một dòng.
* Dòng trạng thái hiện tại có `DenNgay_Key = NULL`.
* Khi có trạng thái mới, đóng trạng thái cũ.

## `Fact_LichSuTraNo`

Nguồn: `repayment_paid`, `late_fee_charged`, `early_settlement`.

Xử lý:

* Mỗi lần khách trả tiền ghi một dòng.
* Tách gốc, lãi, phí phạt.
* Nếu trả thiếu, ghi số thực trả, không tự làm đẹp dữ liệu.
* Nếu trả trễ, ghi phí phạt nếu có.

## `Fact_ThuChi`

Nguồn: `loan_disbursement_events`, `repayment_events`, `opex_events`, `payroll_events`.

Xử lý:

* Giải ngân: `SoTienChi > 0`, `SoTienThu = 0`.
* Thu gốc/lãi/phí: `SoTienThu > 0`, `SoTienChi = 0`.
* Chi phí: `SoTienChi > 0`.
* Giao dịch liên quan hợp đồng thì có `GiaoDich_Key`.
* Chi phí vận hành không nhất thiết có `GiaoDich_Key`.

## `Fact_ChiPhiHoatDong`

Nguồn: `opex_recorded`.

Xử lý:

* Ghi nhận chi phí theo ngày phát sinh.
* Thanh toán có thể xảy ra cùng ngày hoặc sau đó.
* Nếu thanh toán, liên kết mềm sang `PhieuChi_ID`.

## `Fact_LuongThuong`

Nguồn: `payroll_calculated`.

Xử lý:

* Tổng hợp theo tháng.
* Một nhân viên một dòng cho một kỳ kế toán.
* Hoa hồng giải ngân phụ thuộc doanh số.
* Hoa hồng thu nợ phụ thuộc tiền thực thu.
* Tổng thu nhập = lương cơ bản + hoa hồng + phụ cấp.

## `Fact_KhauHao`

Nguồn: `depreciation_recorded`.

Xử lý:

* Ghi nhận theo tháng.
* Không phải dòng tiền.
* Phục vụ báo cáo chi phí kế toán.

---

# 15. Logic mô phỏng một ngày vận hành

Ví dụ một ngày bình thường trong hệ thống:

## 07:00–08:00

* Airflow kiểm tra dữ liệu nền.
* Cập nhật thời tiết theo tọa độ.
* Tính hệ số hoạt động theo cửa hàng trong ngày.
* Tạo danh sách cửa hàng có khả năng đông/vắng.

## 08:00–11:30

* Kafka bắt đầu nhận nhiều event khách đến cửa hàng.
* Cửa hàng A/A+ ở Hà Nội, TP.HCM phát sinh mạnh hồ sơ xe máy, điện thoại.
* Một phần khách cũ quay lại vay tiếp.
* Một phần hồ sơ được định giá tài sản ngay.

## 11:30–13:30

* Lượng hồ sơ mới giảm.
* Hệ thống xử lý các hồ sơ tồn buổi sáng.
* Một số hồ sơ được chuyển sang chờ duyệt.

## 13:30–16:30

* Duyệt hồ sơ nhiều hơn.
* Sinh event phê duyệt/từ chối.
* Một số hồ sơ được giải ngân.

## 16:30–19:30

* Tăng khách đến sau giờ làm.
* Tăng trả nợ tại cửa hàng.
* Tăng giải ngân tiền mặt.

## Cuối ngày

* Đóng batch trong ngày.
* Tổng hợp dòng tiền.
* Kiểm tra chênh lệch thu/chi.
* Cập nhật trạng thái khoản vay quá hạn.
* Ghi cảnh báo data quality nếu có.

---

# 16. Logic “kinh doanh tốt nhưng không phải điểm nào cũng đông”

Để mô phỏng đúng câu này của bạn, cần có 5 lớp biến động.

## Lớp 1 — Khu vực

Hà Nội và TP.HCM có base demand cao nhất.

| Khu vực                                           | Hệ số nhu cầu |
| ------------------------------------------------- | ------------: |
| Hà Nội                                            |     1.35–1.60 |
| TP.HCM                                            |     1.40–1.70 |
| Đà Nẵng, Hải Phòng, Cần Thơ, Bình Dương, Đồng Nai |     1.05–1.35 |
| Thành phố lớn khác                                |     0.85–1.15 |
| Tỉnh                                              |     0.45–0.85 |

## Lớp 2 — Hạng cửa hàng

| Hạng |    Hệ số |
| ---- | -------: |
| A+   |  2.5–4.0 |
| A    |  1.6–2.4 |
| B    |  0.9–1.5 |
| C    |  0.4–0.9 |
| D    | 0.05–0.4 |

## Lớp 3 — Nhân sự

Cửa hàng có nhiều nhân viên xử lý được nhiều hồ sơ hơn.

| Số nhân viên | Tác động               |
| ------------ | ---------------------- |
| 1–2          | giới hạn mạnh số hồ sơ |
| 3–5          | xử lý bình thường      |
| 6–10         | xử lý tốt              |
| >10          | phù hợp cửa hàng A+    |

## Lớp 4 — Thời gian

* Cuối tuần tăng nhóm cầm xe, điện thoại.
* Đầu tháng tăng trả nợ.
* Cuối tháng tăng tất toán, thu hồi, chi phí.
* Ngày mưa giảm hồ sơ trực tiếp.

## Lớp 5 — Sự kiện bất thường

Mỗi tháng nên có vài sự kiện:

| Sự kiện              | Tác động                                |
| -------------------- | --------------------------------------- |
| Chiến dịch marketing | Tăng hồ sơ 15–50% tại một nhóm cửa hàng |
| Cửa hàng mới mở      | 1–2 tháng đầu tăng trưởng dần           |
| Cạnh tranh khu vực   | Một số cửa hàng giảm hồ sơ              |
| Nhân viên nghỉ việc  | Giảm khả năng xử lý                     |
| Mưa bão              | Giảm khách đến cửa hàng                 |
| Đợt thu hồi nợ mạnh  | Tăng thu nợ, giảm nợ quá hạn            |

---

# 17. Chỉ số kiểm soát để dữ liệu nhìn “thật”

Sau khi sinh dữ liệu, nên kiểm tra các chỉ số tổng thể. Nếu lệch quá thì điều chỉnh tham số.

| Nhóm chỉ số                           | Khoảng hợp lý |
| ------------------------------------- | ------------: |
| Tỷ lệ duyệt toàn hệ thống             |        62–78% |
| Tỷ lệ giải ngân trên hồ sơ được duyệt |        88–96% |
| Tỷ lệ từ chối                         |        12–25% |
| Tỷ lệ khách hủy                       |          3–8% |
| Tỷ lệ trả đúng hạn                    |        72–84% |
| Tỷ lệ quá hạn nhẹ                     |         6–12% |
| Tỷ lệ nợ xấu                          |          1–4% |
| Tỷ lệ tất toán trước hạn              |         4–10% |
| Tỷ lệ hồ sơ xe máy                    |        50–65% |
| Tỷ lệ hồ sơ ô tô                      |         8–15% |
| Tỷ lệ tín chấp                        |         8–15% |
| Tỷ lệ giao dịch tiền mặt              |        45–65% |
| Tỷ lệ giao dịch chuyển khoản          |        35–55% |

Vì giả định kinh doanh tốt, các chỉ số nên thể hiện:

* hồ sơ mới tăng đều,
* giải ngân cao,
* thu nợ ổn định,
* doanh thu lãi/phí tốt,
* nợ xấu có nhưng không phá vỡ mô hình,
* cửa hàng A/A+ đóng góp phần lớn doanh thu,
* cửa hàng D vẫn tồn tại nhưng hiệu quả thấp.

---

# 18. Luồng tổng quát cuối cùng

Có thể hiểu toàn bộ hệ thống như sau:

**Master data**

`Dim_ThoiGian`, `Dim_ToaDo`, `Dim_CuaHang`, `Dim_NhanVien`, `Dim_LoaiHinh`, `Dim_LoaiThuChi`, `Dim_TrangThai`, `Dim_QuyTien`

↓

**Event mô phỏng theo thời gian**

Khách hàng, tài sản, hồ sơ, duyệt vay, giải ngân, trả nợ, quá hạn, chi phí, lương, khấu hao, thời tiết

↓

**Kafka topics**

Mỗi nhóm nghiệp vụ một topic, partition theo hợp đồng/cửa hàng/khách hàng

↓

**PostgreSQL staging**

Lưu event thô, chống trùng, kiểm tra lỗi, giữ lịch sử nhận dữ liệu

↓

**ODS**

Tạo trạng thái hiện tại của khách hàng, hợp đồng, dư nợ, kỳ trả nợ, quỹ tiền

↓

**Airflow xử lý**

Validate, chuẩn hóa, tính toán, phân bổ, tổng hợp, kiểm tra chất lượng

↓

**Data mart**

`Fact_GiaoDich`, `Fact_LichSuTrangThai`, `Fact_LichSuTraNo`, `Fact_ThuChi`, `Fact_ChiPhiHoatDong`, `Fact_LuongThuong`, `Fact_KhauHao`, `Fact_ThoiTiet`

↓

**Báo cáo quản trị**

* Doanh số giải ngân.
* Dư nợ.
* Doanh thu lãi.
* Doanh thu phí.
* Dòng tiền thu/chi.
* Tỷ lệ duyệt.
* Tỷ lệ nợ xấu.
* Hiệu quả cửa hàng.
* Hiệu quả nhân viên.
* Chi phí vận hành.
* Lợi nhuận theo khu vực.
* Tác động thời tiết đến hoạt động.

---

# 19. Kết luận thiết kế

Logic mô phỏng nên đi theo nguyên tắc:

1. **Sinh event trước, đổ fact sau.**
2. **Không chia đều dữ liệu cho 800 cửa hàng.**
3. **Dùng trọng số để tạo cửa hàng đông/vắng.**
4. **Dùng phân phối lệch phải cho số tiền vay.**
5. **Dùng Markov Chain cho vòng đời khoản vay.**
6. **Dùng risk scoring cho phê duyệt và trễ hạn.**
7. **Dòng tiền phải sinh từ nghiệp vụ thật: giải ngân, thu nợ, phí, chi phí, lương.**
8. **Lịch sử trạng thái phải append-only.**
9. **Khách hàng thay đổi thông tin phải xử lý SCD Type 2.**
10. **Airflow chỉ điều phối và xử lý batch/micro-batch, Kafka giữ vai trò event streaming.**

Thiết kế này sẽ làm dữ liệu của bạn giống một hệ thống thật: có tăng trưởng, có lệch vùng miền, có cửa hàng mạnh/yếu, có duyệt/từ chối, có thu nợ, có nợ xấu, có chi phí, có lương thưởng, có dòng tiền và có lịch sử trạng thái rõ ràng.

[1]: https://kafka.apache.org/quickstart/?utm_source=chatgpt.com "Quickstart - Apache Kafka"
[2]: https://docs.confluent.io/kafka/introduction.html?utm_source=chatgpt.com "Introduction to Apache Kafka"
[3]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html?utm_source=chatgpt.com "Architecture Overview — Airflow 3.2.1 Documentation"
