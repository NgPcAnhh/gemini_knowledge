# Quy trình Luồng dữ liệu Real-time (Tab 1)

Tài liệu này mô tả kiến trúc và luồng dữ liệu cho Tab "Tổng quan Real-time" của hệ thống Dashboard F88.

## 1. Kiến trúc Tổng thể
Hệ thống sử dụng mô hình Event-Driven Architecture (EDA) với các thành phần chính:
- **Simulator**: Sinh dữ liệu giả lập.
- **Kafka**: Broker trung chuyển sự kiện.
- **Consumer**: Xử lý và lưu trữ dữ liệu.
- **Redis**: Truyền tin real-time tốc độ cao (Pub/Sub).
- **FastAPI**: Backend phục vụ WebSocket và API.
- **Frontend**: Dashboard tương tác real-time.

---

## 2. Luồng dữ liệu chi tiết

### Bước 1: Sinh sự kiện (Simulator)
- Dịch vụ `kafka-simulator` đọc danh sách cửa hàng từ `Dim_CuaHang` (PostgreSQL).
- Dựa trên hạng cửa hàng (A+, A, B, C, D) và trọng số thời gian, simulator sinh ra các chuỗi sự kiện:
    - `customer_created`
    - `loan_application_created`
    - `loan_approved` / `loan_rejected`
    - `loan_disbursed`
    - `repayment_paid`
    - `cash_recorded` (Thu/Chi ngoài luồng)
- Các sự kiện này được đẩy vào các Kafka Topics tương ứng.

### Bước 2: Tiếp nhận và Chuyển đổi (Consumer)
- Dịch vụ `kafka-pg-consumer` lắng nghe toàn bộ các topics.
- **Lưu trữ**: Mọi sự kiện thô được lưu vào bảng `Raw_Staging_Events` để phục vụ audit và replay.
- **Biến đổi**: Consumer cập nhật các bảng Dimension và Fact (SCD Type 2 cho khách hàng, Fact giao dịch...).
- **Kích hoạt Real-time**: Sau khi lưu DB thành công, Consumer bắn sự kiện thô vào **Redis Channel** `f88_realtime`.

### Bước 3: Backend Hub (FastAPI)
- FastAPI khởi tạo một `RealtimeState` để quản lý số liệu tổng hợp trong ngày (Today's Stats).
- **Initial Load**: Khi người dùng mở Dashboard, Frontend gọi `GET /api/snapshot`. FastAPI sẽ truy vấn PostgreSQL (bảng staging) để tính toán toàn bộ dữ liệu từ đầu ngày đến hiện tại.
- **Live Stream**: FastAPI subcribe vào Redis Channel. Khi có sự kiện mới:
    - Cập nhật số liệu cộng dồn trong bộ nhớ (Memory).
    - Kiểm tra reset ngày mới (nếu qua 24h).
    - Broadcast (phát sóng) dữ liệu đã đóng gói qua **WebSocket** (`/ws/realtime`) tới tất cả Dashboard đang mở.

### Bước 4: Hiển thị (Frontend Dashboard)
- **Khởi tạo**: Dashboard nhận snapshot từ API để vẽ biểu đồ và điền các KPI (Giải ngân, Thu nợ, PAR1...).
- **Cập nhật**: Khi nhận message từ WebSocket:
    - Cập nhật các đồng hồ số (Counter animation).
    - Đẩy thêm điểm dữ liệu mới vào biểu đồ Line Chart/Bar Chart.
    - Đẩy thông báo mới vào **Live Event Feed**.
    - Cập nhật rủi ro trên bản đồ Map.

---

## 3. Cơ chế Reset dữ liệu
- **Hệ thống**: Khi simulator bắn sự kiện `system_reset`, Consumer sẽ thực hiện `TRUNCATE` các bảng Fact để bắt đầu phiên mô phỏng mới.
- **Giao diện**: FastAPI tự động phát hiện ngày mới hoặc lệnh reset để trả dữ liệu về 0, đảm bảo Dashboard luôn hiển thị đúng số liệu "Trong ngày hôm nay".

---

## 4. Sơ đồ tóm tắt
`Simulator` -> `Kafka` -> `Consumer` -> `PostgreSQL` (Lưu trữ)
                                  |
                                  v
                               `Redis` -> `FastAPI` (WebSocket) -> `Dashboard` (UI)
