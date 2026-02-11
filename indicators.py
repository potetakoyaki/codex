from __future__ import annotations

import pandas as pd

import config


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=length).mean()


def _rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    atr = _atr(high, low, close, length)
    plus_di = 100 * (plus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr)

    di_sum = (plus_di + minus_di).replace(0, pd.NA)
    dx = ((plus_di - minus_di).abs() / di_sum) * 100
    return dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out

    out[f"EMA{config.EMA_FAST}"] = _ema(out["Close"], config.EMA_FAST)
    out[f"EMA{config.EMA_SLOW}"] = _ema(out["Close"], config.EMA_SLOW)
    out[f"ADX_{config.ADX_LENGTH}"] = _adx(
        out["High"], out["Low"], out["Close"], config.ADX_LENGTH
    )
    out[f"RSI_{config.RSI_LENGTH}"] = _rsi(out["Close"], config.RSI_LENGTH)
    out[f"ATR_{config.ATR_LENGTH}"] = _atr(
        out["High"], out["Low"], out["Close"], config.ATR_LENGTH
    )

    return out
