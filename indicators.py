from __future__ import annotations

import pandas as pd
import pandas_ta as ta

import config


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out

    out[f"EMA{config.EMA_FAST}"] = ta.ema(out["Close"], length=config.EMA_FAST)
    out[f"EMA{config.EMA_SLOW}"] = ta.ema(out["Close"], length=config.EMA_SLOW)

    adx_df = ta.adx(out["High"], out["Low"], out["Close"], length=config.ADX_LENGTH)
    if adx_df is not None and not adx_df.empty:
        adx_col = f"ADX_{config.ADX_LENGTH}"
        out[adx_col] = adx_df.get(adx_col)
    else:
        out[f"ADX_{config.ADX_LENGTH}"] = pd.NA

    out[f"RSI_{config.RSI_LENGTH}"] = ta.rsi(out["Close"], length=config.RSI_LENGTH)
    out[f"ATR_{config.ATR_LENGTH}"] = ta.atr(
        out["High"], out["Low"], out["Close"], length=config.ATR_LENGTH
    )

    return out
