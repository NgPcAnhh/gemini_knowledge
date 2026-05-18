import logging
import random
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger("airflow.task")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "generate_cost_data",
    default_args=default_args,
    description="Seed dimensions, fix historical employee links, and backfill 12 months of cost & HR data",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
)

def get_db_hook():
    return PostgresHook(postgres_conn_id="credit_control_postgres")

def seed_dimensions():
    hook = get_db_hook()
    conn = hook.get_conn()
    cursor = conn.cursor()
    try:
        # 1. Seed Dim_NhanVien
        cursor.execute("SELECT COUNT(*) FROM Dim_NhanVien")
        emp_count = cursor.fetchone()[0]
        if emp_count == 0:
            logger.info("Seeding Dim_NhanVien...")
            cursor.execute("SELECT CuaHang_Key, MaCuaHang, TenCuaHang FROM Dim_CuaHang")
            stores = cursor.fetchall()
            employees_data = []
            for store_key, store_code, store_name in stores:
                employees_data.append((f"NV-{store_code}-001", f"Trưởng cửa hàng {store_name}", "Cửa hàng trưởng", store_key))
                employees_data.append((f"NV-{store_code}-002", f"Giao dịch viên A {store_name}", "Giao dịch viên", store_key))
                employees_data.append((f"NV-{store_code}-003", f"Giao dịch viên B {store_name}", "Giao dịch viên", store_key))
            
            insert_query = """
                INSERT INTO Dim_NhanVien (MaNhanVien, TenNhanVien, ChucVu, CuaHang_Key, TrangThai)
                VALUES (%s, %s, %s, %s, 'Đang làm việc')
                ON CONFLICT (MaNhanVien) DO NOTHING
            """
            cursor.executemany(insert_query, employees_data)
            logger.info(f"Seeding completed: Inserted {len(employees_data)} employees.")

        # 2. Seed Dim_KhoanMucChiPhi
        cursor.execute("SELECT COUNT(*) FROM Dim_KhoanMucChiPhi")
        km_count = cursor.fetchone()[0]
        if km_count == 0:
            logger.info("Seeding Dim_KhoanMucChiPhi...")
            khoan_mucs = [
                ("Chi phí BH", "Lương cơ bản Sale", "Lương cơ bản của nhân viên Sale tại chi nhánh"),
                ("Chi phí BH", "Hoa hồng giải ngân", "Hoa hồng chi trả dựa trên doanh số giải ngân hợp đồng"),
                ("Chi phí BH", "Hoa hồng thu nợ", "Hoa hồng chi trả dựa trên số tiền thu hồi nợ thành công"),
                ("Chi phí BH", "Phụ cấp Sale", "Phụ cấp ăn trưa, xăng xe, điện thoại cho nhân viên Sale"),
                ("Chi phí BH", "Chi phí marketing", "Chi phí quảng cáo Google, Facebook, tờ rơi, băng rôn"),
                ("Chi phí BH", "Chi phí mặt bằng", "Tiền thuê địa điểm mở cửa hàng giao dịch"),
                ("Chi phí BH", "Chi phí điện nước cửa hàng", "Hóa đơn điện nước phát sinh tại cửa hàng hàng tháng"),
                ("Chi phí QLDN", "Lương cơ bản Admin", "Lương cơ bản của nhân viên hỗ trợ, kế toán, admin"),
                ("Chi phí QLDN", "Phụ cấp Admin", "Phụ cấp cho nhân viên admin, hỗ trợ"),
                ("Chi phí QLDN", "Khấu hao tài sản", "Khấu hao định kỳ hàng tháng cho trang thiết bị nội bộ"),
                ("Chi phí QLDN", "Văn phòng phẩm", "Chi phí mua giấy, bút, sổ sách, ghim bấm"),
                ("Chi phí QLDN", "Chi phí internet/IT", "Chi phí đường truyền internet FPT, Viettel và hỗ trợ kỹ thuật"),
            ]
            cursor.executemany(
                "INSERT INTO Dim_KhoanMucChiPhi (NhomChiPhi, TenKhoanMuc, DienGiai) VALUES (%s, %s, %s)",
                khoan_mucs
            )
            logger.info("Seeding Dim_KhoanMucChiPhi completed.")

        # 3. Seed Dim_NhaCungCap
        cursor.execute("SELECT COUNT(*) FROM Dim_NhaCungCap")
        ncc_count = cursor.fetchone()[0]
        if ncc_count == 0:
            logger.info("Seeding Dim_NhaCungCap...")
            ncc_list = [
                ("Tổng công ty Điện lực Việt Nam (EVN)", "Điện lực", "19001006", "MST001234", "1100223344"),
                ("Công ty Cổ phần Cấp nước Sài Gòn (SAWACO)", "Nước sinh hoạt", "19001007", "MST001235", "1100223345"),
                ("Tổng công ty Viễn thông Viettel", "Internet/IT", "18008098", "MST001236", "1100223346"),
                ("Công ty Cổ phần Viễn thông FPT", "Internet/IT", "19006600", "MST001237", "1100223347"),
                ("Công ty Cổ phần Tập đoàn Thiên Long", "Văn phòng phẩm", "028375055", "MST001238", "1100223348"),
                ("Công ty Cổ phần Đầu tư Thế Giới Di Động", "Thiết bị IT/Văn phòng", "18001060", "MST001239", "1100223349"),
            ]
            cursor.executemany(
                "INSERT INTO Dim_NhaCungCap (TenNhaCungCap, LoaiDichVu, SoDienThoai, MaSoThue, SoTaiKhoan) VALUES (%s, %s, %s, %s, %s)",
                ncc_list
            )
            logger.info("Seeding Dim_NhaCungCap completed.")

        # 4. Seed Dim_TaiSanNoiBo
        cursor.execute("SELECT COUNT(*) FROM Dim_TaiSanNoiBo")
        ts_count = cursor.fetchone()[0]
        if ts_count == 0:
            logger.info("Seeding Dim_TaiSanNoiBo...")
            cursor.execute("SELECT CuaHang_Key, MaCuaHang FROM Dim_CuaHang")
            stores = cursor.fetchall()
            assets = []
            for store_key, store_code in stores:
                assets.append((f"TS-{store_code}-LAP", f"Máy tính xách tay Dell Latitude {store_code}", "Máy tính", "2025-01-15", 15000000, 36))
                assets.append((f"TS-{store_code}-PRN", f"Máy in Canon LBP2900 {store_code}", "Máy văn phòng", "2025-02-10", 5000000, 24))
                assets.append((f"TS-{store_code}-AC", f"Điều hòa Daikin 12000BTU {store_code}", "Điều hòa", "2025-03-20", 12000000, 60))
            
            cursor.executemany(
                "INSERT INTO Dim_TaiSanNoiBo (MaTaiSan, TenTaiSan, LoaiTaiSan, NgayMua, GiaTriNguyenGia, ThoiGianKhauHao_Thang) VALUES (%s, %s, %s, %s, %s, %s)",
                assets
            )
            logger.info("Seeding Dim_TaiSanNoiBo completed.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error seeding dimensions: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def fix_historical_keys():
    hook = get_db_hook()
    conn = hook.get_conn()
    cursor = conn.cursor()
    try:
        logger.info("Linking historical loan and transaction records to newly seeded employee dimensions...")
        
        # Cập nhật NhanVien_Sale_Key trong Fact_GiaoDich dựa trên CuaHang_Key
        cursor.execute("""
            UPDATE Fact_GiaoDich fg
            SET NhanVien_Sale_Key = nv.NhanVien_Key
            FROM Dim_NhanVien nv
            WHERE fg.CuaHang_Key = nv.CuaHang_Key 
              AND nv.ChucVu = 'Giao dịch viên'
              AND fg.NhanVien_Sale_Key IS NULL
        """)
        updated_sales = cursor.rowcount
        
        # Cập nhật NguoiDuyet_Key trong Fact_GiaoDich dựa trên CuaHang_Key
        cursor.execute("""
            UPDATE Fact_GiaoDich fg
            SET NguoiDuyet_Key = nv.NhanVien_Key
            FROM Dim_NhanVien nv
            WHERE fg.CuaHang_Key = nv.CuaHang_Key 
              AND nv.ChucVu = 'Cửa hàng trưởng'
              AND fg.NguoiDuyet_Key IS NULL
        """)
        updated_approvers = cursor.rowcount

        # Cập nhật NhanVien_ThucHien_Key trong Fact_LichSuTrangThai
        cursor.execute("""
            UPDATE Fact_LichSuTrangThai fl
            SET NhanVien_ThucHien_Key = nv.NhanVien_Key
            FROM Fact_GiaoDich fg
            JOIN Dim_NhanVien nv ON fg.CuaHang_Key = nv.CuaHang_Key AND nv.ChucVu = 'Giao dịch viên'
            WHERE fl.GiaoDich_Key = fg.GiaoDich_Key 
              AND fl.NhanVien_ThucHien_Key IS NULL
        """)
        updated_history = cursor.rowcount

        conn.commit()
        logger.info(f"Historical employee links fixed: {updated_sales} sales, {updated_approvers} approvers, {updated_history} history states linked.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error fixing historical employee keys: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def generate_cost_and_hr_data():
    hook = get_db_hook()
    conn = hook.get_conn()
    cursor = conn.cursor()
    try:
        logger.info("Generating cost, depreciation, and payroll records for the last 12 months...")

        # 1. Lấy thông tin cơ bản
        cursor.execute("SELECT CuaHang_Key, MaCuaHang, HangCuaHang FROM Dim_CuaHang")
        stores = cursor.fetchall()
        
        cursor.execute("SELECT KhoanMuc_Key, TenKhoanMuc, NhomChiPhi FROM Dim_KhoanMucChiPhi")
        km_list = cursor.fetchall()
        km_map = {km[1]: km[0] for km in km_list}
        
        cursor.execute("SELECT NhaCungCap_Key, TenNhaCungCap FROM Dim_NhaCungCap")
        ncc_list = cursor.fetchall()
        ncc_map = {ncc[1]: ncc[0] for ncc in ncc_list}

        cursor.execute("SELECT NhanVien_Key, MaNhanVien, ChucVu, CuaHang_Key FROM Dim_NhanVien")
        employees = cursor.fetchall()
        emp_by_store = {}
        for emp in employees:
            emp_by_store.setdefault(emp[3], []).append(emp)

        cursor.execute("SELECT TaiSanNoiBo_Key, MaTaiSan, GiaTriNguyenGia, ThoiGianKhauHao_Thang, RIGHT(MaTaiSan, 3) AS type_code, CAST(SPLIT_PART(MaTaiSan, '-', 2) AS VARCHAR) AS store_code FROM Dim_TaiSanNoiBo")
        assets = cursor.fetchall()

        # Tạo danh sách các tháng trong 12 tháng qua
        today = datetime.now()
        months = []
        for i in range(12, -1, -1):
            m_date = today - timedelta(days=i*30)
            months.append((m_date.year, m_date.month, int(m_date.strftime("%Y%m"))))

        # 2. Xóa các bản ghi cũ trong fact chi phí để tránh lặp dữ liệu
        cursor.execute("TRUNCATE TABLE Fact_ChiPhiHoatDong CASCADE")
        cursor.execute("TRUNCATE TABLE Fact_KhauHao CASCADE")
        cursor.execute("TRUNCATE TABLE Fact_LuongThuong CASCADE")

        # 3. Tạo Fact_ChiPhiHoatDong (Chi phí hàng tháng và hàng ngày)
        logger.info("Populating Fact_ChiPhiHoatDong...")
        opex_records = []
        bill_counter = 1000000

        for year, month, ky_ke_toan in months:
            for store_key, store_code, store_rank in stores:
                # Tiền thuê mặt bằng hàng tháng (Rent)
                rent_base = 25000000 if store_rank == 'A+' else (20000000 if store_rank == 'A' else (15000000 if store_rank == 'B' else 10000000))
                rent_amt = rent_base * random.uniform(0.95, 1.05)
                date_key = int(f"{year}{month:02d}01")
                bill_counter += 1
                
                # Tìm đại diện người tạo chi phí (Store Manager)
                creator_key = None
                store_emps = emp_by_store.get(store_key, [])
                for emp in store_emps:
                    if emp[2] == 'Cửa hàng trưởng':
                        creator_key = emp[0]
                        break
                if not creator_key and store_emps:
                    creator_key = store_emps[0][0]

                opex_records.append((
                    date_key, store_key, km_map["Chi phí mặt bằng"], None, creator_key,
                    rent_amt, 0, rent_amt, f"HD-RENT-{ky_ke_toan}-{store_code}", "Tiền thuê mặt bằng chi nhánh", "Đã thanh toán", date_key
                ))

                # Các chi phí vận hành hàng tháng (Điện, Nước, Internet)
                services = [
                    ("Chi phí điện nước cửa hàng", "Tổng công ty Điện lực Việt Nam (EVN)", random.uniform(2000000, 5000000)),
                    ("Chi phí điện nước cửa hàng", "Công ty Cổ phần Cấp nước Sài Gòn (SAWACO)", random.uniform(400000, 1000000)),
                    ("Chi phí internet/IT", "Tổng công ty Viễn thông Viettel" if random.choice([True, False]) else "Công ty Cổ phần Viễn thông FPT", random.uniform(500000, 800000))
                ]
                for service_name, ncc_name, base_cost in services:
                    cost_amt = base_cost * random.uniform(0.9, 1.1)
                    bill_counter += 1
                    opex_records.append((
                        date_key, store_key, km_map[service_name], ncc_map[ncc_name], creator_key,
                        cost_amt, cost_amt * 0.1, cost_amt * 1.1, f"HD-SRV-{bill_counter}", f"Thanh toán hóa đơn {service_name}", "Đã thanh toán", date_key
                    ))

                # Chi phí Marketing hàng tháng
                mkt_amt = random.uniform(3000000, 10000000)
                bill_counter += 1
                opex_records.append((
                    date_key, store_key, km_map["Chi phí marketing"], None, creator_key,
                    mkt_amt, 0, mkt_amt, f"HD-MKT-{bill_counter}", "Chi phí quảng cáo và in ấn sự kiện", "Đã thanh toán", date_key
                ))

                # Chi phí Văn phòng phẩm định kỳ
                vpp_amt = random.uniform(300000, 800000)
                bill_counter += 1
                opex_records.append((
                    date_key, store_key, km_map["Văn phòng phẩm"], ncc_map["Công ty Cổ phần Tập đoàn Thiên Long"], creator_key,
                    vpp_amt, vpp_amt * 0.1, vpp_amt * 1.1, f"HD-VPP-{bill_counter}", "Chi phí văn phòng phẩm định kỳ", "Đã thanh toán", date_key
                ))

        cursor.executemany("""
            INSERT INTO Fact_ChiPhiHoatDong (
                NgayGhiNhan_Key, CuaHang_Key, KhoanMuc_Key, NhaCungCap_Key, NhanVien_Tao_Key,
                SoTienTruocThue, TienThueVAT, TongTienChiPhi, SoHoaDon, MoTaChiTiet, TrangThaiThanhToan, NgayThanhToan_Key
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, opex_records)
        logger.info(f"Fact_ChiPhiHoatDong populated: Inserted {len(opex_records)} records.")

        # 4. Tạo Fact_KhauHao (Khấu hao tài sản nội bộ hàng tháng)
        logger.info("Populating Fact_KhauHao...")
        depr_records = []
        
        # Áp dụng cho 12 tháng
        for year, month, ky_ke_toan in months:
            # Map stores to keys
            store_key_map = {store[1]: store[0] for store in stores}
            
            for asset_key, asset_code, cost, term, type_code, store_code in assets:
                store_key = store_key_map.get(store_code)
                if not store_key:
                    continue
                
                monthly_depr = cost / term
                
                # Tính giá trị còn lại (Giả định tài sản mua năm 2025)
                # Tính xem đã trôi qua bao nhiêu tháng kể từ khi mua
                purchase_date = datetime(2025, 1, 15) if type_code == 'LAP' else (datetime(2025, 2, 10) if type_code == 'PRN' else datetime(2025, 3, 20))
                current_date = datetime(year, month, 15)
                elapsed_months = max(1, (current_date.year - purchase_date.year) * 12 + (current_date.month - purchase_date.month))
                
                remaining_val = max(0, cost - (monthly_depr * elapsed_months))
                
                depr_records.append((
                    ky_ke_toan, store_key, asset_key, km_map["Khấu hao tài sản"], monthly_depr, remaining_val
                ))

        cursor.executemany("""
            INSERT INTO Fact_KhauHao (
                KyKeToan_Key, CuaHang_Key, TaiSanNoiBo_Key, KhoanMuc_Key, GiaTriKhauHaoThang, GiaTriConLai
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, depr_records)
        logger.info(f"Fact_KhauHao populated: Inserted {len(depr_records)} records.")

        # 5. Tạo Fact_LuongThuong (Lương hàng tháng + hoa hồng tính động)
        logger.info("Populating Fact_LuongThuong với hoa hồng động...")
        payroll_records = []

        for year, month, ky_ke_toan in months:
            # Truy vấn tổng số tiền giải ngân của từng nhân viên sale trong tháng này
            cursor.execute("""
                SELECT NhanVien_Sale_Key, SUM(SoTienDuyetVay) as disb_sum
                FROM Fact_GiaoDich
                WHERE NgayGiaiNgan_Key IS NOT NULL 
                  AND NgayGiaiNgan_Key / 100 = %s
                  AND NhanVien_Sale_Key IS NOT NULL
                GROUP BY 1
            """, (ky_ke_toan,))
            disb_map = {row[0]: float(row[1]) for row in cursor.fetchall()}

            # Truy vấn tổng số tiền thu nợ gốc & lãi của từng cửa hàng trong tháng này (được đại diện chia cho sale)
            cursor.execute("""
                SELECT fg.CuaHang_Key, SUM(fl.SoTienGocDaTra + fl.SoTienLaiDaTra) as coll_sum
                FROM Fact_LichSuTraNo fl
                JOIN Fact_GiaoDich fg ON fl.GiaoDich_Key = fg.GiaoDich_Key
                WHERE fl.NgayThanhToan_Key / 100 = %s
                GROUP BY 1
            """, (ky_ke_toan,))
            coll_store_map = {row[0]: float(row[1]) for row in cursor.fetchall()}

            for emp_key, emp_code, chuc_vu, store_key in employees:
                basic_salary = 15000000 if chuc_vu == 'Cửa hàng trưởng' else 8000000
                allowance = 2000000 if chuc_vu == 'Cửa hàng trưởng' else 1500000
                
                # Tính toán hoa hồng động
                disb_commission = 0.0
                coll_commission = 0.0
                
                if chuc_vu == 'Giao dịch viên':
                    # 0.1% doanh số giải ngân của riêng Agent này
                    agent_disb = disb_map.get(emp_key, 0.0)
                    disb_commission = agent_disb * 0.001
                    
                    # 0.5% doanh số thu hồi nợ của cửa hàng chia đôi cho các giao dịch viên
                    store_coll = coll_store_map.get(store_key, 0.0)
                    coll_commission = (store_coll * 0.005) / 2.0
                else:
                    # Cửa hàng trưởng nhận hoa hồng quản lý: 0.05% giải ngân + 0.1% thu nợ của toàn cửa hàng
                    # Tính tổng giải ngân của toàn cửa hàng
                    store_disb = sum(disb_map.get(e[0], 0.0) for e in emp_by_store.get(store_key, []))
                    disb_commission = store_disb * 0.0005
                    coll_commission = coll_store_map.get(store_key, 0.0) * 0.001

                # Đảm bảo làm tròn
                disb_commission = round(disb_commission, 0)
                coll_commission = round(coll_commission, 0)
                total_income = basic_salary + allowance + disb_commission + coll_commission

                payroll_records.append((
                    ky_ke_toan, emp_key, store_key, km_map["Lương cơ bản Sale"] if chuc_vu == 'Giao dịch viên' else km_map["Lương cơ bản Admin"],
                    basic_salary, disb_commission, coll_commission, allowance, total_income
                ))

        cursor.executemany("""
            INSERT INTO Fact_LuongThuong (
                KyKeToan_Key, NhanVien_Key, CuaHang_Key, KhoanMuc_Key,
                LuongCoBan, HoaHongGiaiNgan, HoaHongThuNo, PhuCap, TongThuNhap
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, payroll_records)
        logger.info(f"Fact_LuongThuong populated: Inserted {len(payroll_records)} records.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error generating opex and payroll data: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

# Define Operator Tasks
seed_dim_task = PythonOperator(
    task_id="seed_dimensions_task",
    python_callable=seed_dimensions,
    dag=dag,
)

fix_keys_task = PythonOperator(
    task_id="fix_historical_keys_task",
    python_callable=fix_historical_keys,
    dag=dag,
)

gen_data_task = PythonOperator(
    task_id="generate_costs_task",
    python_callable=generate_cost_and_hr_data,
    dag=dag,
)

# Pipeline dependency order
seed_dim_task >> fix_keys_task >> gen_data_task
