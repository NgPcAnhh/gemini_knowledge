"""
simulator/distributions.py

Engine xác suất cho mô phỏng nghiệp vụ.
"""

import numpy as np
from datetime import datetime

from simulator.config import (
    TIER_WEIGHT, AREA_WEIGHT, HOUR_FACTOR, WEEKDAY_FACTOR,
    LOAN_AMOUNT_RANGE, INTEREST_RATE_RANGE, LOAN_TERM_OPTIONS,
    REPAYMENT_BEHAVIOR, WEATHER_CODES,
)


class DistributionEngine:
    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    def weighted_choice(self, options: list, weights: list):
        w = np.array(weights, dtype=float)
        total = w.sum()
        if total <= 0:
            w = np.ones(len(options), dtype=float)
            total = w.sum()
        w = w / total
        return options[int(self.rng.choice(len(options), p=w))]

    def weighted_choices(self, options: list, weights: list, size: int):
        w = np.array(weights, dtype=float)
        total = w.sum()
        if total <= 0:
            w = np.ones(len(options), dtype=float)
            total = w.sum()
        w = w / total
        idxs = self.rng.choice(len(options), size=size, p=w)
        return [options[int(i)] for i in idxs]

    def poisson_count(self, lam: float) -> int:
        if lam <= 0:
            return 0
        return max(0, int(self.rng.poisson(lam)))

    def bounded_normal_int(self, mean: float, sd: float, lo: int, hi: int) -> int:
        return int(np.clip(round(self.rng.normal(mean, sd)), lo, hi))

    def gen_loan_amount(self, loan_type: str) -> float:
        """Số tiền vay, đơn vị VND."""
        min_m, max_m = LOAN_AMOUNT_RANGE[loan_type]
        median = max(min_m, (min_m + max_m) / 2.8)
        mu = np.log(median)
        sigma = 0.55
        amt_m = float(np.clip(self.rng.lognormal(mu, sigma), min_m, max_m))
        return round(amt_m, 0) * 1_000_000

    def gen_asset_value(self, loan_amount_vnd: float, loan_type: str) -> float:
        if "tín chấp" in loan_type.lower():
            return 0.0
        ltv = float(self.rng.uniform(0.35, 0.70))
        value = loan_amount_vnd / max(ltv, 0.01)
        noise = float(self.rng.uniform(0.92, 1.10))
        return round(max(value * noise, loan_amount_vnd * 1.15), 0)

    def gen_interest_rate(self, loan_type: str) -> float:
        min_r, max_r = INTEREST_RATE_RANGE[loan_type]
        return round(float(self.rng.uniform(min_r, max_r)), 2)

    def gen_loan_term(self, loan_type: str) -> int:
        return int(self.rng.choice(LOAN_TERM_OPTIONS[loan_type]))

    def gen_credit_score(self) -> int:
        return int(np.clip(self.rng.normal(620, 105), 300, 850))

    def gen_income(self, min_income_m: float, max_income_m: float) -> float:
        if max_income_m <= 0:
            return 0.0
        median = max(0.1, (min_income_m + max_income_m) / 2.25)
        income_m = self.rng.lognormal(np.log(median), 0.42)
        return round(float(np.clip(income_m, min_income_m, max_income_m)) * 1_000_000, 0)

    def calc_approval_probability(
        self,
        credit_score: int,
        dti: float,
        ltv: float,
        loan_type: str,
        is_returning_customer: bool = False,
        weather_risk: str = "low",
        is_shipper: bool = False,
    ) -> float:
        credit_norm = (credit_score - 575) / 137.5
        dti_effect = -1.5 * dti if dti > 0 else 0.0
        ltv_effect = -0.8 * ltv if ltv > 0 else -0.1

        product_risk = {
            "Vay tín chấp (Theo lương)": -0.4,
            "Vay tín chấp (Hộ kinh doanh)": -0.5,
            "Cầm đồ Điện thoại/Laptop": -0.15,
            "Cầm đồ Bất động sản/Sổ đỏ": -0.05,
        }.get(loan_type, 0.0)

        returning_bonus = 0.65 if is_returning_customer else 0.0
        shipper_weather_penalty = 0.0
        if is_shipper and weather_risk == "medium":
            shipper_weather_penalty = -0.1
        elif is_shipper and weather_risk == "high":
            shipper_weather_penalty = -0.2

        z = 1.25 + 1.5 * credit_norm + dti_effect + ltv_effect + product_risk + returning_bonus + shipper_weather_penalty
        return float(1.0 / (1.0 + np.exp(-z)))

    def decide_approval(self, probability: float) -> bool:
        return bool(self.rng.random() < probability)

    def gen_repayment_behavior(self, credit_score: int, dti: float, is_shipper: bool = False, weather_risk: str = "low") -> str:
        behaviors = list(REPAYMENT_BEHAVIOR.keys())
        probs = np.array([(a + b) / 2 for a, b in REPAYMENT_BEHAVIOR.values()], dtype=float)

        credit_factor = (credit_score - 300) / 550
        probs[0] *= (1 + 0.30 * credit_factor)
        probs[1] *= (1 + 0.18 * credit_factor)
        for i in range(2, len(probs)):
            probs[i] *= (1 - 0.25 * credit_factor)

        if dti > 0.50:
            probs[0] *= 0.78
            probs[2] *= 1.30
            probs[3] *= 1.35
            probs[4] *= 1.45

        if is_shipper and weather_risk in ("medium", "high"):
            factor = 1.20 if weather_risk == "medium" else 1.55
            probs[0] *= 0.92
            probs[2] *= factor
            probs[3] *= factor
            probs[4] *= factor

        probs = probs / probs.sum()
        return self.weighted_choice(behaviors, probs.tolist())

    def calc_store_weight(self, store: dict, dt: datetime, weather_risk: str = "low") -> float:
        tier = store.get("Tier") or store.get("HangCuaHang") or "C"
        area = store.get("KhuVuc") or store.get("TenKhuVuc") or "default"
        # lấy phần trước dấu " - " để match Hà Nội/TP.HCM
        city = str(area).split(" - ")[0].strip()

        tw = TIER_WEIGHT.get(tier, 1.0)
        aw = AREA_WEIGHT.get(city, AREA_WEIGHT.get(area, AREA_WEIGHT["default"]))
        hf = HOUR_FACTOR.get(dt.hour, 0.3)
        wf = WEEKDAY_FACTOR.get(dt.weekday(), 1.0)
        hotness = float(store.get("TrafficHotness", 1.0))
        weather_boost = 1.0
        if weather_risk == "medium":
            weather_boost = 1.08
        elif weather_risk == "high":
            weather_boost = 1.16

        noise = float(self.rng.uniform(0.85, 1.18))
        return max(0.001, tw * aw * hf * wf * hotness * weather_boost * noise)

    def gen_weather(self, store: dict) -> dict:
        # Khu vực metro có xác suất mưa/ảnh hưởng cao hơn một chút.
        area = (store.get("KhuVuc") or "").split(" - ")[0]
        if area in ("TP.HCM", "TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng"):
            weights = [0.34, 0.16, 0.16, 0.14, 0.11, 0.06, 0.03]
        else:
            weights = [0.44, 0.18, 0.16, 0.10, 0.07, 0.035, 0.015]
        item = self.weighted_choice(WEATHER_CODES, weights)
        risk = item["risk"]
        rain = 0.0
        wind = float(self.rng.uniform(4, 20))
        temp = float(self.rng.uniform(24, 35))

        if risk == "medium":
            rain = float(self.rng.uniform(3, 25))
            wind = float(self.rng.uniform(12, 35))
            temp = float(self.rng.uniform(24, 31))
        elif risk == "high":
            rain = float(self.rng.uniform(25, 75))
            wind = float(self.rng.uniform(25, 65))
            temp = float(self.rng.uniform(23, 29))

        return {
            "Weather_Code": item["code"],
            "MoTaThoiTiet_VN": item["desc"],
            "risk": risk,
            "NhietDo_2m": round(temp, 1),
            "LuongMua": round(rain, 1),
            "TocDoGio_10m": round(wind, 1),
        }
