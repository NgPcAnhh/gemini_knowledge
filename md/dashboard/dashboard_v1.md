# Kế hoạch Tối ưu hóa Dashboard (Góc nhìn Business Analyst - Version 2)

Dưới góc độ phân tích nghiệp vụ, một dashboard quản trị (Executive Dashboard) không chỉ để **"Nhìn" (Monitoring)** mà phải phục vụ việc **"Hành động" (Actionable Insights)**. Để dashboard thực sự tối ưu, tôi đề xuất kế hoạch cải tiến toàn diện sau:

## User Review Required

> [!IMPORTANT]
> **Xác nhận Phương án Kỹ thuật & Tương tác:**
> 1. **Bản đồ (Map):** Sử dụng Interactive SVG nhúng trực tiếp (đảm bảo nhẹ, có tooltip, có legend giải thích màu sắc chi tiết từng tỉnh).
> 2. **Interactive UI:** Tôi sẽ thêm hiệu ứng UI mô phỏng (ví dụ: các nút hành động nhanh, thanh cảnh báo ngưỡng) bằng HTML/CSS/JS thuần trong file. Bạn có đồng ý với phạm vi thay đổi này không?

## Open Questions

> [!NOTE]
> Bạn có muốn thêm một cột "Hành động khuyến nghị" (Recommended Actions) trực tiếp vào cạnh các con số bị báo Đỏ (Ví dụ: PAR 1+ vượt ngưỡng -> Nút giả lập *"Gửi SMS nhắc nợ hàng loạt"*) để tăng tính Actionable không?

## Proposed Changes

### 1. Tối ưu Layout & Bản đồ (Theo yêu cầu gốc)
- **Đảo vị trí Tab 1**: Đưa Bản đồ Việt Nam sang bên trái (ưu tiên luồng nhìn cảnh báo địa lý), Biểu đồ Lưu lượng (Line chart) sang phải.
- **Nâng cấp Bản đồ Việt Nam**:
  - Dùng SVG phân chia ranh giới các tỉnh/thành chính.
  - Thêm **Tooltip tương tác**: Hover vào TP.HCM sẽ hiện bảng chi tiết *"TP.HCM: 1,250 khoản vay | Rủi ro: Cao (Mưa bão) | Hụt thu: 20%"*.
  - Thêm **Legend (Chú giải)**: Thang màu Nóng - Lạnh cảnh báo rủi ro ngay cạnh bản đồ.

### 2. Góp ý Tối ưu hóa Dashboard (Business Analyst Suggestions)

#### A. Biến Số liệu thành Hành động (Actionable Insights)
- **Nút Hành động nhanh (Quick Actions)**: Thêm các nút CTA nhỏ ở các thẻ rủi ro. 
  - *Ví dụ:* Dưới thẻ `PAR 1+ 8.2%` thêm link giả lập `[Xuất file DPD1]`. Dưới thẻ cảnh báo Net Cashflow âm thêm link `[Điều chỉnh Rule duyệt]`.
- **Feed phân loại**: Chuyển luồng "Live Event Stream" thành có Tabs (pill buttons): `Tất cả` | `Cảnh báo` | `Giao dịch` để quản trị viên dễ lọc thông tin lúc khẩn cấp.

#### B. Tối ưu UX/UI cho Biểu đồ (Data Visualization Best Practices)
- **Thước đo Ngưỡng rủi ro (Threshold Bars)**: Thay vì chỉ hiện số `% LTV` hay `% PAR`, sẽ thêm một thanh tiến trình (mini progress bar) mỏng bên dưới con số để thể hiện khoảng cách đến ngưỡng rủi ro đỏ (Threshold), giúp sếp nhìn lướt qua là biết mức độ nguy hiểm.
- **Tab 2 (Tổng thu)**: Thêm **Center Text** ở tâm biểu đồ Doughnut hiển thị Tổng giá trị, tránh việc người xem phải tự cộng nhẩm các phần cắt.
- **Tab 3 (Chi phí & Rủi ro)**: Biểu đồ Bubble (LTV vs Thu nhập) sẽ được vẽ thêm 2 đường trung bình (Crosshairs) để chia làm 4 **Góc phần tư (Quadrants)**, giúp định vị ngay lập tức tệp khách hàng nằm ở góc "Thu nhập thấp - LTV cao" (Góc rủi ro nhất).
- **Trạng thái Bộ lọc (Active Filters)**: Khu vực bộ lọc sẽ có các "Chip" hiển thị filter đang được áp dụng để người dùng không bị mất bối cảnh (Context loss) khi xem biểu đồ.

#### C. Khả năng phân tích sâu (Tooltips & Formats)
- **Đồng bộ Tooltips & Trục Y**: Format lại toàn bộ Tooltips của Chart.js để hiển thị số liệu tiền tệ rõ ràng (Ví dụ: `45,000,000 VND` thay vì `45`) và phần trăm (`%`).

## Verification Plan

### Manual Verification
1. Mở file `mock_dashboard.html` trên trình duyệt.
2. Kiểm tra **Tab 1**: Bản đồ SVG tương tác nằm bên trái, có Tooltip khi hover và Legend bên cạnh. Đảm bảo UI không bị vỡ trên 1 màn hình.
3. Kiểm tra **Actionable UI**: Nhìn thấy các thanh tiến trình (progress bars) nhỏ dưới các chỉ số PAR/LTV và các nút Action text (Export/Call).
4. Kiểm tra **Biểu đồ**: 
   - Có chữ Tổng ở giữa biểu đồ Doughnut.
   - Có đường gióng Quadrant chia 4 trên biểu đồ Bubble.
   - Trục Y và Tooltip hiển thị format tiền tệ/phần trăm chuẩn.
