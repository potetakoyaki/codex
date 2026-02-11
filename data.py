from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_m15(pair: str, period_days: int) -> pd.DataFrame:
    period = f"{period_days}d"
    df = yf.download(
        tickers=pair,
        period=period,
        interval="15m",
        progress=False,
        auto_adjust=False,
        threads=False,
    )
    if df is None or df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    keep_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in keep_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[keep_cols].copy()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    return df.sort_index()


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    agg = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }
    out = df.resample(rule).agg(agg)
    out = out.dropna(subset=["Open", "High", "Low", "Close"], how="any")
    return out
