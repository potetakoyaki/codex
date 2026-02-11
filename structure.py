from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PivotPoints:
    highs: list[tuple[pd.Timestamp, float]]
    lows: list[tuple[pd.Timestamp, float]]


def detect_pivots(df: pd.DataFrame, k: int) -> PivotPoints:
    highs: list[tuple[pd.Timestamp, float]] = []
    lows: list[tuple[pd.Timestamp, float]] = []

    if df.empty or len(df) < (2 * k + 1):
        return PivotPoints(highs=highs, lows=lows)

    high_s = df["High"]
    low_s = df["Low"]
    for i in range(k, len(df) - k):
        window_high = high_s.iloc[i - k : i + k + 1]
        window_low = low_s.iloc[i - k : i + k + 1]

        center_high = high_s.iloc[i]
        center_low = low_s.iloc[i]

        if center_high == window_high.max() and (window_high == center_high).sum() == 1:
            highs.append((df.index[i], float(center_high)))

        if center_low == window_low.min() and (window_low == center_low).sum() == 1:
            lows.append((df.index[i], float(center_low)))

    return PivotPoints(highs=highs, lows=lows)


def detect_structure(df: pd.DataFrame, k: int) -> str:
    piv = detect_pivots(df, k)
    if len(piv.highs) < 2 or len(piv.lows) < 2:
        return "NONE"

    high_prev, high_last = piv.highs[-2][1], piv.highs[-1][1]
    low_prev, low_last = piv.lows[-2][1], piv.lows[-1][1]

    if high_last > high_prev and low_last > low_prev:
        return "UP"
    if high_last < high_prev and low_last < low_prev:
        return "DOWN"
    return "NONE"
