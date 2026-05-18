import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Mapping WMO Weather Codes to Vietnamese descriptions and risk levels
WMO_MAPPING = {
    0: {"desc": "Trời nắng", "risk": "low"},
    1: {"desc": "Ít mây", "risk": "low"},
    2: {"desc": "Nhiều mây", "risk": "low"},
    3: {"desc": "Trời u ám", "risk": "low"},
    45: {"desc": "Sương mù", "risk": "low"},
    48: {"desc": "Sương mù đóng băng", "risk": "low"},
    51: {"desc": "Mưa phùn nhẹ", "risk": "low"},
    53: {"desc": "Mưa phùn vừa", "risk": "low"},
    55: {"desc": "Mưa phùn đặc", "risk": "medium"},
    61: {"desc": "Mưa nhẹ", "risk": "medium"},
    63: {"desc": "Mưa vừa", "risk": "medium"},
    65: {"desc": "Mưa to", "risk": "high"},
    71: {"desc": "Tuyết rơi nhẹ", "risk": "medium"},
    73: {"desc": "Tuyết rơi vừa", "risk": "high"},
    75: {"desc": "Tuyết rơi mạnh", "risk": "high"},
    80: {"desc": "Mưa rào nhẹ", "risk": "medium"},
    81: {"desc": "Mưa rào vừa", "risk": "medium"},
    82: {"desc": "Mưa rào mạnh", "risk": "high"},
    95: {"desc": "Dông bão", "risk": "high"},
}

PROVINCES_API = [
    {"name": "Tuyên Quang", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.8233&longitude=105.2186&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Cao Bằng", "url": "https://api.open-meteo.com/v1/forecast?latitude=22.6667&longitude=106.2500&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Lai Châu", "url": "https://api.open-meteo.com/v1/forecast?latitude=22.3990&longitude=103.4569&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Lào Cai", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.7168&longitude=104.8986&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Thái Nguyên", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.5942&longitude=105.8482&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Điện Biên", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.3860&longitude=103.0230&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Lạng Sơn", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.8537&longitude=106.7615&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Sơn La", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.3270&longitude=103.9141&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Phú Thọ", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.3227&longitude=105.4021&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Bắc Ninh", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.2731&longitude=106.1946&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Quảng Ninh", "url": "https://api.open-meteo.com/v1/forecast?latitude=20.9712&longitude=107.0448&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Hà Nội", "url": "https://api.open-meteo.com/v1/forecast?latitude=21.0285&longitude=105.8542&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Hải Phòng", "url": "https://api.open-meteo.com/v1/forecast?latitude=20.8449&longitude=106.6881&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Hưng Yên", "url": "https://api.open-meteo.com/v1/forecast?latitude=20.6464&longitude=106.0511&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Ninh Bình", "url": "https://api.open-meteo.com/v1/forecast?latitude=20.2506&longitude=105.9745&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Thanh Hóa", "url": "https://api.open-meteo.com/v1/forecast?latitude=19.8067&longitude=105.7852&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Nghệ An", "url": "https://api.open-meteo.com/v1/forecast?latitude=18.6796&longitude=105.6813&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Hà Tĩnh", "url": "https://api.open-meteo.com/v1/forecast?latitude=18.3559&longitude=105.8877&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Quảng Trị", "url": "https://api.open-meteo.com/v1/forecast?latitude=17.4689&longitude=106.6223&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Huế", "url": "https://api.open-meteo.com/v1/forecast?latitude=16.4637&longitude=107.5909&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Đà Nẵng", "url": "https://api.open-meteo.com/v1/forecast?latitude=16.0544&longitude=108.2022&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Quảng Ngãi", "url": "https://api.open-meteo.com/v1/forecast?latitude=15.1205&longitude=108.7923&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Gia Lai", "url": "https://api.open-meteo.com/v1/forecast?latitude=13.7820&longitude=109.2190&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Đắk Lắk", "url": "https://api.open-meteo.com/v1/forecast?latitude=12.6667&longitude=108.0500&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Khánh Hòa", "url": "https://api.open-meteo.com/v1/forecast?latitude=12.2388&longitude=109.1967&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Lâm Đồng", "url": "https://api.open-meteo.com/v1/forecast?latitude=11.9404&longitude=108.4583&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Đồng Nai", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.9574&longitude=106.8427&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Tây Ninh", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.5359&longitude=106.4137&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Hồ Chí Minh", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.8231&longitude=106.6297&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Đồng Tháp", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.3600&longitude=106.3600&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "An Giang", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.0125&longitude=105.0809&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Vĩnh Long", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.2537&longitude=105.9722&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "TP. Cần Thơ", "url": "https://api.open-meteo.com/v1/forecast?latitude=10.0452&longitude=105.7469&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
    {"name": "Cà Mau", "url": "https://api.open-meteo.com/v1/forecast?latitude=9.1769&longitude=105.1524&current=temperature_2m,wind_speed_10m,weather_code,precipitation&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"},
]

class WeatherService:
    def __init__(self):
        self.session = requests.Session()

    def fetch_all_weather(self) -> List[Dict]:
        results = []
        for prov in PROVINCES_API:
            try:
                resp = self.session.get(prov["url"], timeout=10)
                resp.raise_for_status()
                data = resp.json()
                parsed = self.parse_response(prov["name"], data)
                if parsed:
                    results.append(parsed)
            except Exception as e:
                logger.error(f"Error fetching weather for {prov['name']}: {e}")
        return results

    def parse_response(self, province_name: str, data: Dict) -> Optional[Dict]:
        try:
            current = data.get("current", {})
            code = current.get("weather_code", 0)
            mapping = WMO_MAPPING.get(code, {"desc": "Không xác định", "risk": "low"})
            
            return {
                "KhuVuc": province_name,
                "TenKhuVuc": province_name,
                "MoTaThoiTiet_VN": mapping["desc"],
                "risk": mapping["risk"],
                "LuongMua": current.get("precipitation", 0.0),
                "TocDoGio_10m": current.get("wind_speed_10m", 0.0),
                "NhietDo": current.get("temperature_2m", 25.0),
            }
        except Exception as e:
            logger.error(f"Error parsing weather for {province_name}: {e}")
            return None
