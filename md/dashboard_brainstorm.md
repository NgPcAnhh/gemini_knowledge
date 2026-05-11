1. Mô hình kinh doanh đề xuất
1.1. Khách hàng mục tiêu

Tệp chính: tài xế Grab, Be, Gojek, Xanh SM, Ahamove, ShopeeFood, giao hàng tự do.

Đặc điểm:

Đặc điểm	Ý nghĩa quản trị
Thu nhập theo ngày	Nên thiết kế lịch trả góp/ngày/tuần thay vì kỳ hạn dài
Phụ thuộc thời tiết, đơn hàng, xăng xe	Dashboard cần theo dõi “khả năng kiếm tiền hôm nay”
Tài sản chính là xe máy, điện thoại	Phù hợp mô hình cầm đồ tài sản lưu động
Dễ phát sinh nhu cầu tiền gấp	Cần phê duyệt nhanh nhưng kiểm soát fraud
Rủi ro quá hạn cao nếu xe hỏng, mưa lớn, bệnh, tài khoản app bị khóa	Cần cảnh báo sớm trước khi nợ xấu xảy ra
1.2. Sản phẩm vay đề xuất
Sản phẩm	Tài sản bảo đảm	Số tiền	Kỳ hạn	Cách trả
Vay cầm cavet xe	Xe máy + giấy đăng ký	2–15 triệu	7–30 ngày	Trả cuối kỳ hoặc góp ngày
Vay cầm điện thoại	Smartphone tài xế đang dùng	1–8 triệu	7–21 ngày	Góp ngày
Vay xoay vòng tài xế thân thiết	Dựa trên lịch sử trả nợ + tài sản	1–10 triệu	7–14 ngày	Trả góp linh hoạt
Gia hạn có kiểm soát	Hợp đồng hiện hữu	Theo dư nợ	7–15 ngày	Chỉ cho khách tốt

Nguyên tắc quản trị: không tối đa hóa khoản vay theo nhu cầu khách, mà theo khả năng trả nợ hằng ngày + giá trị tài sản + rủi ro mùa vụ/thời tiết.

2. Luồng nghiệp vụ tổng thể
2.1. Luồng từ lúc khách đăng ký đến tất toán
[Lead phát sinh]
    ↓
[Thu thập thông tin khách]
    ↓
[KYC + đồng ý xử lý dữ liệu]
    ↓
[Định danh tài xế]
    ↓
[Định giá tài sản cầm cố]
    ↓
[Chấm điểm rủi ro]
    ↓
[Đề xuất hạn mức/kỳ hạn/lịch trả]
    ↓
[Quản lý duyệt]
    ↓
[Ký hợp đồng + lưu tài sản/giấy tờ]
    ↓
[Giải ngân]
    ↓
[Theo dõi realtime: thu nhập, thời tiết, quá hạn, cảnh báo]
    ↓
[Nhắc thanh toán / thu tiền]
    ↓
[Tất toán / gia hạn / xử lý quá hạn]
2.2. Swimlane chi tiết
Bước	Khách hàng	Nhân viên	Hệ thống	Quản trị
1. Đăng ký	Gửi CCCD, số điện thoại, loại tài sản	Nhập hồ sơ	Tạo loan_application	Xem số lead mới
2. KYC	Chụp CCCD, selfie, biển số xe	Kiểm tra thủ công	Check trùng khách, blacklist, OCR	Xem tỷ lệ pass/fail
3. Định danh tài xế	Cung cấp app đang chạy, khu vực chạy	Ghi nhận bằng chứng thu nhập	Lưu hồ sơ tài xế	Xem phân bổ theo app/khu vực
4. Định giá tài sản	Mang xe/điện thoại đến	Chụp ảnh, kiểm tra giấy tờ	Gợi ý giá trị tài sản	Xem LTV trung bình
5. Chấm điểm	Xác nhận khoản vay	Nhập đề xuất	Risk engine tính điểm	Xem hồ sơ rủi ro cao
6. Duyệt	Ký hợp đồng	Gửi duyệt	Rule engine kiểm tra lãi/phí, hạn mức	Duyệt/khóa khoản vay
7. Giải ngân	Nhận tiền	Xác nhận tiền ra	Tạo hợp đồng, lịch trả	Theo dõi giải ngân trong ngày
8. Theo dõi	Trả theo lịch	Thu tiền, nhắc nợ	Stream payment/weather/overdue	Dashboard realtime
9. Kết thúc	Tất toán/gia hạn	Trả tài sản/giấy tờ	Đóng hợp đồng	Xem lợi nhuận, nợ xấu
3. Kịch bản mô phỏng thực tế
3.1. Nhân vật mô phỏng

Khách hàng: Nguyễn Văn Nam
Nghề: tài xế GrabBike + ShopeeFood
Khu vực chạy: Quận Bình Thạnh, Gò Vấp, Quận 1, TP.HCM
Tài sản cầm: xe Honda Vision 2021
Nhu cầu vay: 5.000.000 VNĐ
Lý do vay: sửa xe + đóng tiền nhà
Kỳ hạn đề xuất: 14 ngày
Hình thức trả: góp ngày, tự động nhắc qua Zalo/SMS

3.2. Dữ liệu mô phỏng đầu vào
{
  "customer": {
    "full_name": "Nguyễn Văn Nam",
    "phone": "0909123456",
    "dob": "1994-08-12",
    "city": "Ho Chi Minh City",
    "district": "Binh Thanh",
    "job_type": "app_driver",
    "platforms": ["Grab", "ShopeeFood"],
    "monthly_income_estimate": 13500000
  },
  "collateral": {
    "asset_type": "motorbike",
    "brand": "Honda",
    "model": "Vision",
    "year": 2021,
    "plate_number": "59S1-12345",
    "estimated_market_value": 17000000,
    "forced_sale_value": 12500000,
    "ownership_verified": true
  },
  "loan_request": {
    "requested_amount": 5000000,
    "term_days": 14,
    "repayment_type": "daily_installment",
    "purpose": "repair_motorbike_and_rent"
  },
  "external_context": {
    "weather_today": "heavy_rain",
    "rain_probability": 0.82,
    "fuel_price_trend": "up",
    "driver_income_risk_today": "high"
  }
}
3.3. Chấm điểm rủi ro mô phỏng
Tiêu chí	Dữ liệu	Điểm
LTV = khoản vay / giá trị thanh lý	5.000.000 / 12.500.000 = 40%	Tốt
Thu nhập/ngày ước tính	450.000–600.000	Tốt
Số nền tảng chạy	2 app	Tốt
Khu vực mưa lớn hôm nay	Có	Rủi ro ngắn hạn
Khách mới hay cũ	Khách mới	Trung bình
Tài sản có giấy tờ rõ	Có	Tốt
Khoản góp/ngày	khoảng 360.000–390.000	Cần kiểm tra

Kết luận hệ thống: duyệt có điều kiện.

{
  "risk_score": 68,
  "risk_grade": "B",
  "decision": "approve_with_conditions",
  "approved_amount": 4500000,
  "term_days": 14,
  "recommended_daily_payment": 330000,
  "conditions": [
    "Giữ cavet gốc hoặc xác minh tài sản theo quy trình nội bộ",
    "Yêu cầu ảnh xe, số khung, số máy",
    "Không cho giải ngân vượt 40% forced_sale_value",
    "Theo dõi thời tiết 3 ngày đầu để điều chỉnh lịch nhắc"
  ]
}
3.4. Timeline sau giải ngân
Ngày	Sự kiện	Dữ liệu realtime	Hành động hệ thống
D0	Giải ngân 4,5 triệu	Hợp đồng active	Tạo lịch trả 14 ngày
D1	Mưa lớn TP.HCM	Rain risk = high	Không nhắc gắt, gửi nhắc mềm
D2	Khách trả 330.000	Payment success	Risk giảm
D3	Không trả	Weather xấu + thu nhập thấp	Gắn “watchlist”
D4	Trả bù 600.000	Khôi phục	Bỏ cảnh báo đỏ
D7	Trễ 1 ngày	DPD = 1	Gọi chăm sóc
D10	Có mưa + đơn ít	Income shock index cao	Cho phép dời giờ thanh toán trong ngày
D14	Tất toán	Contract closed	Cập nhật khách tốt
D15	Gợi ý hạn mức tái vay	Repayment tốt	Offer 5–6 triệu
4. Thiết kế cơ sở dữ liệu chi tiết

Tôi đề xuất dùng PostgreSQL cho OLTP, Redis cho realtime cache, Kafka/Redpanda hoặc RabbitMQ cho event streaming, và ClickHouse/BigQuery/PostgreSQL materialized view cho dashboard.

4.1. Nhóm bảng người dùng và phân quyền
CREATE TABLE branches (
    id UUID PRIMARY KEY,
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    district VARCHAR(100),
    address TEXT,
    lat NUMERIC(10,7),
    lng NUMERIC(10,7),
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE staff_users (
    id UUID PRIMARY KEY,
    branch_id UUID REFERENCES branches(id),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(30) UNIQUE,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_id UUID,
    actor_type VARCHAR(30), -- staff/system/customer
    action VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT now()
);
4.2. Nhóm bảng khách hàng
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(255),
    dob DATE,
    gender VARCHAR(20),
    national_id_hash VARCHAR(255), -- không lưu CCCD plain text nếu không cần
    city VARCHAR(100),
    district VARCHAR(100),
    ward VARCHAR(100),
    address TEXT,
    customer_segment VARCHAR(50), -- app_driver, worker, merchant
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE customer_documents (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    document_type VARCHAR(50), -- cccd_front, cccd_back, selfie, driver_app_screenshot
    file_url TEXT NOT NULL,
    file_hash VARCHAR(255),
    verification_status VARCHAR(30) DEFAULT 'pending',
    verified_by UUID REFERENCES staff_users(id),
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE customer_consents (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    consent_type VARCHAR(100), -- personal_data, location, income_proof, marketing
    consent_version VARCHAR(50),
    consent_text TEXT,
    consent_status VARCHAR(30), -- granted, withdrawn
    granted_at TIMESTAMP,
    withdrawn_at TIMESTAMP,
    ip_address VARCHAR(50),
    device_info JSONB
);

Ghi chú quản trị: customer_consents rất quan trọng vì hệ thống có thể xử lý dữ liệu nhạy cảm như CCCD, vị trí, thu nhập, tài sản. Thiếu bảng này thì dashboard có thể đẹp nhưng vận hành rủi ro pháp lý.

4.3. Hồ sơ tài xế
CREATE TABLE driver_profiles (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    primary_platform VARCHAR(50), -- Grab, Be, Gojek, ShopeeFood, Ahamove
    secondary_platforms TEXT[],
    driver_since DATE,
    main_working_city VARCHAR(100),
    main_working_districts TEXT[],
    avg_daily_income NUMERIC(14,2),
    avg_daily_trips INT,
    working_days_per_week INT,
    income_proof_method VARCHAR(50), -- screenshot, bank_statement, manual, api
    verification_status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE driver_income_observations (
    id BIGSERIAL PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    observation_date DATE NOT NULL,
    platform VARCHAR(50),
    gross_income NUMERIC(14,2),
    trip_count INT,
    online_hours NUMERIC(6,2),
    fuel_cost_estimate NUMERIC(14,2),
    net_income_estimate NUMERIC(14,2),
    source VARCHAR(50), -- screenshot, bank_txn, manual, api
    confidence_score INT, -- 0-100
    created_at TIMESTAMP DEFAULT now()
);
4.4. Tài sản cầm cố
CREATE TABLE collateral_assets (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    asset_type VARCHAR(50) NOT NULL, -- motorbike, phone, laptop
    brand VARCHAR(100),
    model VARCHAR(100),
    manufacture_year INT,
    serial_number VARCHAR(100),
    plate_number VARCHAR(50),
    engine_number VARCHAR(100),
    chassis_number VARCHAR(100),
    ownership_status VARCHAR(50), -- owned, family_owned, unclear
    legal_document_status VARCHAR(50), -- original, copy, missing
    physical_condition VARCHAR(50), -- good, fair, poor
    storage_location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE collateral_photos (
    id UUID PRIMARY KEY,
    asset_id UUID REFERENCES collateral_assets(id),
    photo_type VARCHAR(50), -- front, back, plate, engine, odometer, scratch
    file_url TEXT,
    uploaded_by UUID REFERENCES staff_users(id),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE asset_valuations (
    id UUID PRIMARY KEY,
    asset_id UUID REFERENCES collateral_assets(id),
    appraised_by UUID REFERENCES staff_users(id),
    market_value NUMERIC(14,2),
    forced_sale_value NUMERIC(14,2),
    max_ltv_percent NUMERIC(5,2),
    recommended_loan_amount NUMERIC(14,2),
    valuation_method VARCHAR(50), -- manual, rule_based, marketplace_reference
    notes TEXT,
    created_at TIMESTAMP DEFAULT now()
);
4.5. Hồ sơ vay và hợp đồng
CREATE TABLE loan_applications (
    id UUID PRIMARY KEY,
    application_code VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID REFERENCES customers(id),
    branch_id UUID REFERENCES branches(id),
    requested_amount NUMERIC(14,2) NOT NULL,
    requested_term_days INT NOT NULL,
    purpose TEXT,
    application_status VARCHAR(50) DEFAULT 'draft',
    created_by UUID REFERENCES staff_users(id),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE loan_application_assets (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES loan_applications(id),
    asset_id UUID REFERENCES collateral_assets(id),
    valuation_id UUID REFERENCES asset_valuations(id)
);

CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES loan_applications(id),
    risk_score INT,
    risk_grade VARCHAR(10), -- A, B, C, D
    pd_estimate NUMERIC(8,4), -- probability of default
    ltv NUMERIC(8,4),
    dti_daily NUMERIC(8,4), -- daily payment / daily income
    weather_risk_score INT,
    fraud_risk_score INT,
    recommendation VARCHAR(50), -- approve, reject, manual_review
    reason_codes TEXT[],
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE loan_contracts (
    id UUID PRIMARY KEY,
    contract_code VARCHAR(50) UNIQUE NOT NULL,
    application_id UUID REFERENCES loan_applications(id),
    customer_id UUID REFERENCES customers(id),
    branch_id UUID REFERENCES branches(id),
    principal_amount NUMERIC(14,2) NOT NULL,
    interest_rate_annual NUMERIC(8,4),
    fee_total NUMERIC(14,2) DEFAULT 0,
    apr_estimate NUMERIC(8,4),
    term_days INT NOT NULL,
    disbursement_method VARCHAR(50), -- cash, bank_transfer, ewallet
    disbursed_at TIMESTAMP,
    maturity_date DATE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, active, overdue, closed, liquidated
    approved_by UUID REFERENCES staff_users(id),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE repayment_schedules (
    id UUID PRIMARY KEY,
    contract_id UUID REFERENCES loan_contracts(id),
    due_date DATE NOT NULL,
    installment_no INT,
    principal_due NUMERIC(14,2),
    interest_due NUMERIC(14,2),
    fee_due NUMERIC(14,2),
    total_due NUMERIC(14,2),
    paid_amount NUMERIC(14,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'unpaid', -- unpaid, partial, paid, overdue
    created_at TIMESTAMP DEFAULT now()
);
4.6. Thanh toán, nợ quá hạn, thu hồi
CREATE TABLE payments (
    id UUID PRIMARY KEY,
    contract_id UUID REFERENCES loan_contracts(id),
    customer_id UUID REFERENCES customers(id),
    payment_code VARCHAR(50) UNIQUE,
    amount NUMERIC(14,2) NOT NULL,
    payment_method VARCHAR(50), -- cash, bank_transfer, momo, zalopay
    payment_channel VARCHAR(50), -- branch, collector, online
    paid_at TIMESTAMP NOT NULL,
    received_by UUID REFERENCES staff_users(id),
    status VARCHAR(50) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE overdue_cases (
    id UUID PRIMARY KEY,
    contract_id UUID REFERENCES loan_contracts(id),
    customer_id UUID REFERENCES customers(id),
    dpd INT DEFAULT 0, -- days past due
    overdue_amount NUMERIC(14,2),
    bucket VARCHAR(20), -- DPD1_3, DPD4_7, DPD8_15, DPD16_PLUS
    case_status VARCHAR(50), -- open, promised, escalated, closed
    assigned_to UUID REFERENCES staff_users(id),
    last_contact_at TIMESTAMP,
    next_action_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE collection_actions (
    id UUID PRIMARY KEY,
    overdue_case_id UUID REFERENCES overdue_cases(id),
    contract_id UUID REFERENCES loan_contracts(id),
    action_type VARCHAR(50), -- sms, call, zalo, visit, promise_to_pay
    action_result VARCHAR(50), -- contacted, no_answer, promised, refused
    promise_amount NUMERIC(14,2),
    promise_date DATE,
    notes TEXT,
    actor_id UUID REFERENCES staff_users(id),
    created_at TIMESTAMP DEFAULT now()
);

Nguyên tắc thu hồi nên đưa vào hệ thống: tất cả hành động nhắc nợ phải được log; không cho nhân viên tự ý gọi quá tần suất, đe dọa, làm phiền người thân, hoặc hành xử ngoài quy trình.

4.7. Weather, traffic, external signals

OpenWeather One Call API 3.0 có dữ liệu thời tiết hiện tại, dự báo theo phút/giờ/ngày và cảnh báo thời tiết; phù hợp để tính “income shock” cho tài xế theo khu vực. Google Routes API có traffic model như BEST_GUESS, PESSIMISTIC, OPTIMISTIC, và có thể dùng dữ liệu giao thông để ước tính thời gian di chuyển.

CREATE TABLE geo_zones (
    id UUID PRIMARY KEY,
    city VARCHAR(100),
    district VARCHAR(100),
    ward VARCHAR(100),
    zone_name VARCHAR(255),
    center_lat NUMERIC(10,7),
    center_lng NUMERIC(10,7),
    radius_km NUMERIC(8,2),
    status VARCHAR(30) DEFAULT 'active'
);

CREATE TABLE weather_observations (
    id BIGSERIAL PRIMARY KEY,
    zone_id UUID REFERENCES geo_zones(id),
    observed_at TIMESTAMP NOT NULL,
    temperature NUMERIC(6,2),
    humidity NUMERIC(6,2),
    rain_mm NUMERIC(8,2),
    rain_probability NUMERIC(5,2),
    wind_speed NUMERIC(8,2),
    weather_condition VARCHAR(100),
    alert_level VARCHAR(30), -- normal, rain, heavy_rain, storm
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE traffic_observations (
    id BIGSERIAL PRIMARY KEY,
    zone_id UUID REFERENCES geo_zones(id),
    observed_at TIMESTAMP NOT NULL,
    avg_speed_kmh NUMERIC(8,2),
    congestion_level VARCHAR(30), -- low, medium, high
    travel_time_index NUMERIC(8,2),
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE external_risk_indices (
    id BIGSERIAL PRIMARY KEY,
    zone_id UUID REFERENCES geo_zones(id),
    index_date DATE NOT NULL,
    hour INT,
    weather_risk_score INT,
    traffic_risk_score INT,
    demand_risk_score INT,
    fuel_cost_risk_score INT,
    driver_income_shock_score INT,
    explanation JSONB,
    created_at TIMESTAMP DEFAULT now()
);
5. Event stream cho dashboard realtime
5.1. Các event chính
{
  "event_type": "loan.disbursed",
  "event_time": "2026-05-10T09:15:00+07:00",
  "contract_id": "LC-000123",
  "customer_id": "CUS-000888",
  "branch_id": "BR-HCM-BT",
  "amount": 4500000,
  "risk_grade": "B",
  "ltv": 0.40
}
{
  "event_type": "payment.received",
  "event_time": "2026-05-11T20:30:00+07:00",
  "contract_id": "LC-000123",
  "amount": 330000,
  "payment_method": "bank_transfer",
  "dpd_before_payment": 0
}
{
  "event_type": "weather.heavy_rain_alert",
  "event_time": "2026-05-12T16:00:00+07:00",
  "zone": "HCM-BinhThanh",
  "rain_probability": 0.82,
  "rain_mm_forecast": 18.5,
  "affected_active_contracts": 183,
  "estimated_income_drop_percent": 22
}
{
  "event_type": "loan.overdue_detected",
  "event_time": "2026-05-13T23:59:00+07:00",
  "contract_id": "LC-000123",
  "customer_id": "CUS-000888",
  "dpd": 1,
  "overdue_amount": 330000,
  "recommended_action": "soft_reminder"
}
5.2. Kiến trúc dữ liệu realtime
Mobile/Web App nhân viên
        ↓
Backend API
        ↓
PostgreSQL OLTP
        ↓
Outbox Events
        ↓
Kafka/Redpanda
        ↓
Stream Processor
        ↓
Redis realtime cache + ClickHouse/BigQuery
        ↓
Dashboard quản trị
        ↓
Alert: Zalo/SMS/Email/Slack/Telegram nội bộ

Pattern nên dùng: Transactional Outbox. Khi tạo hợp đồng hoặc thanh toán, hệ thống ghi DB và ghi event trong cùng transaction, tránh tình trạng “DB có dữ liệu nhưng dashboard không nhận event”.

6. Thiết kế dashboard real-time cho nhà quản trị
6.1. Dashboard cấp CEO/Owner
Màn hình 1: Tổng quan hôm nay
Chỉ số	Công thức	Ý nghĩa
Tổng giải ngân hôm nay	SUM principal disbursed today	Tốc độ tăng dư nợ
Tổng thu hôm nay	SUM payments today	Dòng tiền về
Net cashflow	Thu - giải ngân	Áp lực tiền mặt
Active loans	Count contract active	Quy mô danh mục
PAR 1+	Dư nợ quá hạn từ 1 ngày / tổng dư nợ	Sức khỏe danh mục
DPD mới hôm nay	Count loans chuyển sang overdue	Cảnh báo sớm
Tỷ lệ duyệt	Approved / Applications	Chất lượng lead
LTV trung bình	Principal / forced sale value	An toàn tài sản
Khách tái vay	Repeat borrowers / total borrowers	Độ bền tệp khách
Weather income shock	Điểm 0–100	Dự báo khả năng trả tiền hôm nay
Mẫu layout
┌──────────────────────────────────────────────────────────┐
│ OWNER REAL-TIME COMMAND CENTER                            │
├──────────────┬──────────────┬──────────────┬─────────────┤
│ Giải ngân    │ Thu hôm nay   │ Net cashflow │ PAR 1+      │
│ 185 triệu    │ 142 triệu     │ -43 triệu    │ 7.8%        │
├──────────────┴──────────────┴──────────────┴─────────────┤
│ Biểu đồ dòng tiền theo giờ                                │
├───────────────────────────┬──────────────────────────────┤
│ Bản đồ rủi ro theo quận   │ Cảnh báo nóng                 │
│ Bình Thạnh: cao           │ 42 khoản DPD1                 │
│ Gò Vấp: trung bình        │ 18 khoản bị ảnh hưởng mưa     │
├───────────────────────────┴──────────────────────────────┤
│ Top chi nhánh / nhân viên / nhóm khách                    │
└──────────────────────────────────────────────────────────┘
6.2. Dashboard vận hành chi nhánh
Module	Câu hỏi quản trị
Hồ sơ đang chờ duyệt	Hồ sơ nào quá SLA 15 phút?
Hồ sơ rủi ro cao	Ai đang cố duyệt khoản LTV cao?
Tài sản tồn kho	Xe/giấy tờ nào đang giữ?
Khoản đến hạn hôm nay	Ai cần nhắc trước 18h?
Nhân viên thu tiền	Ai thu được bao nhiêu?
Tỷ lệ hứa trả thất bại	Nhân viên nào xử lý kém?
Ngoại lệ	Hợp đồng sửa tay, miễn phí, gia hạn nhiều lần
6.3. Dashboard rủi ro
Các chỉ số bắt buộc
KPI	Ngưỡng xanh	Ngưỡng vàng	Ngưỡng đỏ
PAR 1+	< 5%	5–10%	> 10%
PAR 7+	< 2%	2–5%	> 5%
Write-off rate	< 1%	1–3%	> 3%
Avg LTV	< 45%	45–60%	> 60%
First payment default	< 3%	3–7%	> 7%
Repeat borrower overdue	< 4%	4–8%	> 8%
New borrower overdue	< 8%	8–15%	> 15%
Same phone/device duplicate	0	1–3	> 3
Manual override rate	< 5%	5–15%	> 15%
Risk heatmap
Theo khu vực:
- Quận 1: dư nợ cao, thu tốt, rủi ro thấp
- Bình Thạnh: dư nợ cao, mưa lớn, DPD tăng
- Gò Vấp: nhiều khách mới, LTV cao
- Thủ Đức: thu nhập tài xế biến động mạnh
6.4. Dashboard thời tiết ảnh hưởng thu nhập tài xế
Chỉ số đề xuất: Driver Income Shock Index

Công thức mẫu:

Driver Income Shock Score =
  35% * Rain Severity
+ 20% * Rain Probability
+ 15% * Traffic Congestion
+ 10% * Heat/Fatigue Risk
+ 10% * Historical Payment Sensitivity
+ 10% * Local Demand Weakness
Ý nghĩa điểm
Điểm	Ý nghĩa	Hành động
0–30	Bình thường	Nhắc nợ theo lịch
31–60	Có ảnh hưởng	Nhắc mềm, ưu tiên khách DPD
61–80	Rủi ro cao	Không đẩy mạnh giải ngân mới ở khu vực đó
81–100	Rủi ro rất cao	Tạm giảm hạn mức, giám sát thanh khoản
Ví dụ cảnh báo
CẢNH BÁO 16:00
Khu vực: Bình Thạnh, Gò Vấp, Quận 1
Tình trạng: mưa lớn, kẹt xe cao
Số hợp đồng active bị ảnh hưởng: 384
Tổng dư nợ bị ảnh hưởng: 1,82 tỷ
Dự kiến tỷ lệ thu hụt hôm nay: -18% đến -25%
Đề xuất:
- Dời nhắc thanh toán từ 18:00 sang 21:30
- Không gọi nhắc nợ nhóm DPD0 trước 20:00
- Tập trung nhóm DPD1–3 có lịch sử trả tốt
7. API tích hợp đề xuất
7.1. Weather API

Nguồn: OpenWeather One Call API 3.0.
Dữ liệu cần lấy: current weather, hourly forecast 48h, daily forecast 8 ngày, alerts. OpenWeather cũng công bố gói One Call có 1.000 API call/ngày miễn phí trước khi tính thêm phí theo lượt gọi.

Tần suất gọi đề xuất
Khu vực	Tần suất
Khu vực có nhiều khoản vay	10 phút/lần
Khu vực ít khoản vay	30 phút/lần
Khi có cảnh báo mưa lớn	5 phút/lần
Ban đêm	60 phút/lần
Pseudo request
GET /data/3.0/onecall?lat=10.8017&lon=106.7148&appid=API_KEY&units=metric&lang=vi
7.2. Traffic API

Nguồn: Google Routes API hoặc dịch vụ bản đồ khác.
Dùng để đo ảnh hưởng kẹt xe đến số chuyến/ngày, thời gian giao hàng, và khả năng tài xế kiếm tiền.

Input:
- Lat/lng trung tâm khu vực tài xế hay chạy
- Khung giờ: 7h, 11h, 17h, 21h
- Traffic model: BEST_GUESS / PESSIMISTIC

Output:
- Thời gian di chuyển ước tính
- Chỉ số kẹt xe
- Dự báo giảm số chuyến
7.3. Zalo/SMS/Call Center

Mục đích:

Tình huống	Kênh
Nhắc trước hạn	Zalo OA
Đến hạn trong ngày	Zalo + SMS
DPD1	Gọi chăm sóc
DPD3+	Nhân viên phụ trách
Thanh toán thành công	Zalo/SMS xác nhận
7.4. Payment API

Tích hợp:

Kênh	Dùng cho
QR ngân hàng	Thu tiền tự động
MoMo/ZaloPay/VietQR	Khách bình dân dễ trả
Tiền mặt tại điểm	Có biên nhận điện tử
Nhân viên thu hộ	Bắt buộc GPS + ảnh biên nhận
8. Công thức quản trị quan trọng
8.1. LTV
LTV = Principal Amount / Forced Sale Value

Ví dụ:

Khoản vay = 5.000.000
Giá thanh lý xe = 12.500.000
LTV = 40%

Khuyến nghị:

Xe máy phổ thông: LTV tối đa 35–50%
Điện thoại: LTV tối đa 25–40%
Khách mới: giảm LTV 5–10 điểm %
Khách tái vay tốt: tăng LTV có kiểm soát
8.2. Daily Payment Burden
Daily Payment Burden = Daily Installment / Estimated Daily Net Income

Ví dụ:

Góp ngày = 330.000
Thu nhập ròng/ngày = 550.000
Burden = 60%

Khuyến nghị: không nên để khoản góp/ngày vượt 40–50% thu nhập ròng/ngày, vì tài xế còn ăn uống, xăng, tiền nhà, gia đình.

8.3. Early Warning Score
Early Warning Score =
  25% * Payment Delay Pattern
+ 20% * Weather Income Shock
+ 15% * Low Income Observation
+ 15% * High LTV
+ 10% * New Borrower
+ 10% * Staff Override
+ 5%  * Duplicate Device/Phone
Phân loại
Điểm	Nhóm	Hành động
0–40	Bình thường	Nhắc tự động
41–60	Theo dõi	Nhân viên kiểm tra
61–80	Rủi ro cao	Gọi chăm sóc + hứa trả
81–100	Nguy hiểm	Chuyển quản lý duyệt phương án
9. Rule engine phê duyệt
9.1. Hard rules

Các rule này vi phạm là không được duyệt:

- Không có consent xử lý dữ liệu cá nhân
- Không xác minh được danh tính
- Tài sản không rõ quyền sở hữu
- LTV vượt trần nội bộ
- Lãi/phí vượt chính sách pháp lý nội bộ
- Khách đang có hợp đồng quá hạn nghiêm trọng
- Số điện thoại/CCCD/device nằm trong blacklist
- Nhân viên tự duyệt hồ sơ do chính mình tạo vượt hạn mức
9.2. Soft rules

Các rule cần quản lý xem xét:

- Khách mới nhưng muốn vay cao
- Tài xế chỉ chạy 1 app, thu nhập không ổn định
- Khu vực làm việc đang mưa lớn nhiều ngày
- First payment rơi vào ngày dự báo thời tiết xấu
- Tài sản dễ mất giá nhanh
- Khách xin gia hạn từ lần vay đầu
10. Mẫu dashboard cảnh báo realtime
10.1. Alert: dòng tiền âm
{
  "alert_type": "cashflow_negative",
  "severity": "high",
  "message": "Giải ngân hôm nay vượt thu vào 43 triệu",
  "metrics": {
    "disbursement_today": 185000000,
    "collection_today": 142000000,
    "net_cashflow": -43000000
  },
  "recommended_actions": [
    "Giảm hạn mức duyệt mới sau 17:00",
    "Ưu tiên thu các khoản đến hạn hôm nay",
    "Tạm dừng duyệt nhóm rủi ro C/D"
  ]
}
10.2. Alert: thời tiết làm giảm thu nhập
{
  "alert_type": "driver_income_shock",
  "severity": "medium",
  "zone": "HCM-BinhThanh",
  "message": "Mưa lớn có thể làm giảm thu nhập tài xế 18-25%",
  "affected_contracts": 183,
  "outstanding_principal": 870000000,
  "recommended_actions": [
    "Chuyển nhắc nợ sang khung 21:00-22:00",
    "Không tăng nhóm khách mới tại khu vực này hôm nay",
    "Theo dõi DPD0 chuyển DPD1 lúc cuối ngày"
  ]
}
10.3. Alert: nhân viên override bất thường
{
  "alert_type": "staff_override_anomaly",
  "severity": "high",
  "staff_id": "STF-009",
  "message": "Nhân viên có tỷ lệ override LTV cao gấp 2.4 lần trung bình",
  "metrics": {
    "override_rate": 0.31,
    "branch_avg": 0.13,
    "overdue_after_override": 0.18
  },
  "recommended_actions": [
    "Khóa quyền duyệt tự động trên 5 triệu",
    "Kiểm tra 20 hồ sơ gần nhất",
    "Yêu cầu quản lý vùng duyệt lại"
  ]
}
11. Mô hình dữ liệu cho báo cáo phân tích
11.1. Fact tables
CREATE TABLE fact_loan_daily (
    report_date DATE,
    branch_id UUID,
    contract_id UUID,
    customer_id UUID,
    principal_outstanding NUMERIC(14,2),
    dpd INT,
    risk_grade VARCHAR(10),
    ltv NUMERIC(8,4),
    status VARCHAR(50),
    PRIMARY KEY (report_date, contract_id)
);

CREATE TABLE fact_payment_daily (
    report_date DATE,
    branch_id UUID,
    contract_id UUID,
    customer_id UUID,
    amount_paid NUMERIC(14,2),
    payment_count INT,
    on_time_flag BOOLEAN,
    PRIMARY KEY (report_date, contract_id)
);

CREATE TABLE fact_zone_risk_hourly (
    report_date DATE,
    hour INT,
    zone_id UUID,
    active_contracts INT,
    outstanding_principal NUMERIC(14,2),
    weather_risk_score INT,
    traffic_risk_score INT,
    expected_collection_amount NUMERIC(14,2),
    actual_collection_amount NUMERIC(14,2),
    PRIMARY KEY (report_date, hour, zone_id)
);
11.2. Dimensions
CREATE TABLE dim_customer_segment (
    segment_code VARCHAR(50) PRIMARY KEY,
    segment_name VARCHAR(255),
    description TEXT
);

CREATE TABLE dim_risk_grade (
    risk_grade VARCHAR(10) PRIMARY KEY,
    min_score INT,
    max_score INT,
    description TEXT
);

CREATE TABLE dim_date (
    date_key DATE PRIMARY KEY,
    day_of_week INT,
    week_of_year INT,
    month INT,
    quarter INT,
    year INT,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);
12. Màn hình quản trị hợp đồng cụ thể

Khi click vào một hợp đồng, quản lý nên thấy:

Hợp đồng: LC-000123
Khách: Nguyễn Văn Nam
Nghề: GrabBike + ShopeeFood
Khoản vay: 4.500.000
Dư nợ: 3.200.000
DPD: 0
Risk grade: B
LTV: 40%
Tài sản: Honda Vision 2021
Khu vực chạy: Bình Thạnh, Gò Vấp, Quận 1

Timeline:
- 10/05 09:15 giải ngân
- 11/05 20:30 trả 330.000
- 12/05 16:00 mưa lớn, income shock high
- 12/05 21:40 trả 320.000
- 13/05 chưa thanh toán

Khuyến nghị:
- Nhắc mềm qua Zalo lúc 21:00
- Không chuyển thu hồi cứng vì thời tiết đang ảnh hưởng
- Theo dõi nếu quá 23:59 chưa trả
13. Ý tưởng bổ sung có lợi cho nhà cho vay
13.1. Dynamic repayment

Không nên nhắc nợ cứng một giờ cố định. Với tài xế, nên nhắc theo khả năng kiếm tiền trong ngày.

Ví dụ:

Điều kiện	Hành động
Trời nắng, đơn nhiều	Nhắc lúc 18:30
Mưa lớn giờ cao điểm	Nhắc sau 21:00
Khách vừa trả hôm qua	Nhắc mềm
DPD1 + thời tiết tốt	Gọi trực tiếp
DPD1 + mưa lớn	Cho hứa trả cuối ngày
13.2. Driver good customer ladder

Tạo thang khách hàng tốt:

Level	Điều kiện	Quyền lợi
Bronze	Tất toán 1 lần đúng hạn	Duyệt nhanh
Silver	3 lần đúng hạn	Hạn mức cao hơn
Gold	5 lần đúng hạn, không DPD	Giảm phí hợp lệ
Blacklist	Gian lận/quá hạn nặng	Từ chối
13.3. Asset liquidity score

Không phải tài sản nào giá cao cũng dễ xử lý.

Asset Liquidity Score =
  thương hiệu phổ biến
+ đời xe/điện thoại
+ giấy tờ rõ
+ tình trạng vật lý
+ nhu cầu thị trường
- rủi ro tranh chấp

Ví dụ:

Tài sản	Giá trị	Thanh khoản
Honda Vision	Trung bình	Cao
SH cũ giấy tờ thiếu	Cao	Trung bình/thấp
iPhone đời mới	Cao	Cao nhưng rủi ro mất giá
Android cũ	Thấp	Thấp
13.4. Staff risk control

Dashboard phải theo dõi cả rủi ro nhân viên, không chỉ khách hàng.

Chỉ số	Ý nghĩa
Tỷ lệ hồ sơ do nhân viên tạo bị quá hạn	Chất lượng bán hàng
Tỷ lệ override	Có đang duyệt lỏng không
Tỷ lệ LTV cao	Có đẩy rủi ro cho công ty không
Tỷ lệ khách quay lại	Khả năng chăm sóc
Số lần sửa hợp đồng	Rủi ro gian lận nội bộ
Thu tiền mặt chưa nộp	Rủi ro thất thoát
14. Roadmap triển khai
Giai đoạn 1: MVP trong 4–6 tuần
Hạng mục	Kết quả
Quản lý khách hàng	Tạo hồ sơ, KYC, consent
Quản lý tài sản	Xe/điện thoại, ảnh, định giá
Quản lý khoản vay	Tạo hồ sơ, duyệt, giải ngân
Lịch trả nợ	Tự động sinh kỳ trả
Thanh toán	Ghi nhận tiền mặt/chuyển khoản
Dashboard cơ bản	Giải ngân, thu tiền, DPD, PAR
Audit log	Ghi toàn bộ hành động quan trọng
Giai đoạn 2: Realtime + cảnh báo
Hạng mục	Kết quả
Event streaming	loan/payment/overdue realtime
Alert engine	Cảnh báo DPD, cashflow, override
Weather API	Mưa, cảnh báo thời tiết
Zone risk	Rủi ro theo quận/huyện
Nhắc nợ thông minh	Zalo/SMS theo tình huống
Giai đoạn 3: Risk engine nâng cao
Hạng mục	Kết quả
Chấm điểm khách hàng	Risk score A/B/C/D
Early warning model	Dự báo quá hạn
Staff anomaly detection	Phát hiện nhân viên bất thường
Dynamic limit	Hạn mức theo lịch sử trả
Profitability dashboard	Lợi nhuận theo sản phẩm/chi nhánh
Giai đoạn 4: Tối ưu tăng trưởng
Hạng mục	Kết quả
Customer ladder	Hạng khách hàng tốt
Campaign tái vay	Tự động gợi ý khách tốt
Heatmap mở điểm giao dịch	Chọn khu vực có tài xế nhiều
Forecast dòng tiền	Dự báo thiếu hụt tiền mặt
Cohort analysis	Phân tích nhóm khách theo tháng vay
15. Bộ KPI cốt lõi nên theo dõi hằng ngày
Nhóm	KPI
Tăng trưởng	Lead mới, hồ sơ duyệt, giải ngân, khách mới, khách tái vay
Rủi ro	PAR1+, PAR7+, DPD mới, first payment default, LTV trung bình
Dòng tiền	Thu hôm nay, giải ngân hôm nay, net cashflow, expected vs actual collection
Tài sản	Tổng tài sản giữ, giá trị thanh lý, tài sản quá hạn chưa xử lý
Nhân viên	Hồ sơ tạo, tỷ lệ duyệt, tỷ lệ nợ xấu, override rate
Khu vực	Dư nợ theo quận, DPD theo quận, weather shock
Khách hàng	Repeat rate, vintage repayment, nhóm app tài xế
Tuân thủ	Hồ sơ thiếu consent, thiếu ảnh tài sản, sửa hợp đồng, hành động thu hồi bất thường
16. Kết luận mô hình đề xuất

Hệ thống nên được thiết kế như một Command Center cho vay cầm đồ tài xế, không chỉ là phần mềm ghi hợp đồng.

Trọng tâm quản trị nên là:

Biết hôm nay tiền đang đi đâu, thu về bao nhiêu.
Biết khoản nào sắp quá hạn trước khi nó quá hạn.
Biết thời tiết/kẹt xe/khu vực nào đang làm tài xế kiếm ít tiền.
Biết nhân viên nào đang tạo rủi ro cho danh mục.
Biết tài sản nào đủ an toàn để cho vay, tài sản nào không nên nhận.
Tất cả lãi/phí/dữ liệu cá nhân/thu hồi nợ phải có rule kiểm soát và audit log.

Thiết kế này giúp nhà cho vay chuyển từ kiểu “duyệt bằng kinh nghiệm” sang quản trị bằng dữ liệu realtime, rất phù hợp với tệp tài xế xe công nghệ có thu nhập biến động từng ngày.