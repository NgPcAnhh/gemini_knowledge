import os
os.environ["PG_HOST"] = "localhost"
from fastapi.database import execute_read_query
data = execute_read_query("SELECT DiemTinDung FROM Dim_KhachHang LIMIT 2")
print(data)
