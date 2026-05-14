import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Set

logger = logging.getLogger("f88-realtime-state")

def empty_snapshot() -> Dict[str, Any]:
    labels = [f"{h:02d}:00" for h in range(8, 22)]
    return {
        "stats": {"disbursement": 0.0, "collection": 0.0, "net_cashflow": 0.0, "par1": 0.0},
        "approval_bar": [0, 0, 0],
        "product_mix": [0, 0, 0, 0, 0],
        "hourly": {"labels": labels, "disbursement": [0.0 for _ in labels], "collection": [0.0 for _ in labels]},
        "risk_radar": [0, 0, 0, 0, 0, 0],
        "risk_radar_metrics": {
            "labels": ["Tỷ lệ điểm rủi ro chi nhánh", "Tỷ lệ nợ xấu (lũy kế)", "Tỷ lệ trả chậm", "Tỷ lệ từ chối do DTI", "Tỷ lệ từ chối do LTV", "Tỷ lệ nghi ngờ gian lận"],
            "values": [0, 0, 0, 0, 0, 0],
            "details": {}
        },
        "feed": [],
        "map": [],
        "radar_counts": {
            "repayment_total": 0,
            "repayment_late": 0,
            "reject_total": 0,
            "reject_dti": 0,
            "reject_ltv": 0,
            "reject_fraud": 0,
        },
        "risk_static": {"par_overdue_count": 0, "par_active_count": 0},
        "timestamp": datetime.now().isoformat(),
        "active_date": datetime.now().strftime("%Y-%m-%d"),
    }

class RealtimeState:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = empty_snapshot()
        self.lock = asyncio.Lock()
        self.current_date = datetime.now().date()
        self.seen_event_ids: Set[str] = set()

    def reset_seen_events(self):
        self.seen_event_ids.clear()

    def is_new_event(self, event_id: str) -> bool:
        if not event_id:
            return True
        if event_id in self.seen_event_ids:
            return False
        self.seen_event_ids.add(event_id)
        if len(self.seen_event_ids) > 2000:
            self.seen_event_ids.clear()
            self.seen_event_ids.add(event_id)
        return True

# To be shared across modules
state = RealtimeState()
