from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

import config
import structure


def _is_nan(value: float | None) -> bool:
    return value is None or pd.isna(value)


def _environment(h4_last: pd.Series) -> str:
    ema_fast = h4_last.get(f"EMA{config.EMA_FAST}")
    ema_slow = h4_last.get(f"EMA{config.EMA_SLOW}")
    adx = h4_last.get(f"ADX_{config.ADX_LENGTH}")

    if _is_nan(ema_fast) or _is_nan(ema_slow) or _is_nan(adx):
        return "RANGE"

    if ema_fast > ema_slow and adx >= config.ADX_THRESHOLD:
        return "UP"
    if ema_fast < ema_slow and adx >= config.ADX_THRESHOLD:
        return "DOWN"
    return "RANGE"


def _score(action: str, env: str, struct_h1: str, rr: float | None, adx: float | None) -> int:
    if action == "WAIT":
        return 0
    base = 50
    if env in {"UP", "DOWN"}:
        base += 20
    if struct_h1 in {"UP", "DOWN"}:
        base += 15
    if rr is not None and not pd.isna(rr):
        base += min(10, int((rr - config.MIN_RR) * 5))
    if adx is not None and not pd.isna(adx):
        base += min(5, int((adx - config.ADX_THRESHOLD) // 2))
    return int(max(0, min(100, base)))


def evaluate_signal(pair: str, m15: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame) -> config.SignalResult:
    ts_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if m15.empty or h1.empty or h4.empty:
        return config.SignalResult(ts_utc, pair, "WAIT", 0, None, None, None, "data=insufficient")

    m15_last = m15.iloc[-1]
    h1_last = h1.iloc[-1]
    h4_last = h4.iloc[-1]

    env = _environment(h4_last)
    if env == "RANGE":
        return config.SignalResult(ts_utc, pair, "WAIT", 0, None, None, None, "env=RANGE")

    struct_h1 = structure.detect_structure(h1, config.PIVOT_K_H1)
    _ = structure.detect_structure(m15, config.PIVOT_K_M15)

    close = m15_last.get("Close")
    ema21_m15 = m15_last.get(f"EMA{config.EMA_FAST}")
    atr_h1 = h1_last.get(f"ATR_{config.ATR_LENGTH}")
    adx_h4 = h4_last.get(f"ADX_{config.ADX_LENGTH}")

    if _is_nan(close) or _is_nan(ema21_m15) or _is_nan(atr_h1):
        return config.SignalResult(
            ts_utc,
            pair,
            "WAIT",
            0,
            None,
            None,
            None,
            f"env={env};struct={struct_h1};reason=nan",
        )

    action = "WAIT"
    if env == "UP" and struct_h1 == "UP" and close > ema21_m15:
        action = "BUY"
    elif env == "DOWN" and struct_h1 == "DOWN" and close < ema21_m15:
        action = "SELL"

    if action == "WAIT":
        return config.SignalResult(
            ts_utc,
            pair,
            "WAIT",
            0,
            None,
            None,
            None,
            f"env={env};struct={struct_h1};entry=blocked",
        )

    pip = config.pip_size(pair)
    sl_distance = config.SL_ATR_MULTIPLIER * float(atr_h1)
    tp_distance = max(config.MIN_TP_PIPS * pip, config.TP_ATR_MULTIPLIER * float(atr_h1))
    if sl_distance <= 0:
        return config.SignalResult(
            ts_utc,
            pair,
            "WAIT",
            0,
            None,
            None,
            None,
            f"env={env};struct={struct_h1};reason=bad_sl",
        )

    rr = tp_distance / sl_distance
    if rr < config.MIN_RR:
        return config.SignalResult(
            ts_utc,
            pair,
            "WAIT",
            0,
            None,
            None,
            None,
            f"env={env};struct={struct_h1};rr={rr:.3f}<2.0",
        )

    entry = float(close)
    if action == "BUY":
        sl = entry - sl_distance
        tp = entry + tp_distance
    else:
        sl = entry + sl_distance
        tp = entry - tp_distance

    score = _score(action, env, struct_h1, rr, adx_h4)
    reason = f"env={env};struct={struct_h1};rr={rr:.3f};adx={float(adx_h4):.3f}"

    return config.SignalResult(ts_utc, pair, action, score, entry, sl, tp, reason)
