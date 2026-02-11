from __future__ import annotations

from dataclasses import dataclass

PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "USDCHF=X",
    "USDCAD=X",
    "AUDUSD=X",
    "NZDUSD=X",
    "EURJPY=X",
    "GBPJPY=X",
    "EURGBP=X",
    "AUDJPY=X",
]

INTERVAL = "15m"
DATA_PERIOD_DAYS = 30

H1_RULE = "1h"
H4_RULE = "4h"

EMA_FAST = 21
EMA_SLOW = 50
ADX_LENGTH = 14
RSI_LENGTH = 14
ATR_LENGTH = 14
ADX_THRESHOLD = 18.0

PIVOT_K_H1 = 2
PIVOT_K_M15 = 3

SL_ATR_MULTIPLIER = 1.2
TP_ATR_MULTIPLIER = 2.0
MIN_TP_PIPS = 50
MIN_RR = 2.0

DB_PATH = "signals.db"
SCHEDULE_SECONDS = 15 * 60


@dataclass(frozen=True)
class SignalResult:
    ts_utc: str
    pair: str
    action: str
    score: int
    entry: float | None
    sl: float | None
    tp: float | None
    reason: str


def pip_size(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001
