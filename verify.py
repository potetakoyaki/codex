from __future__ import annotations

import argparse
import logging
from datetime import datetime

import pandas as pd

import config
import data
import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def _parse_ts(ts_utc: str) -> pd.Timestamp:
    ts = pd.Timestamp(ts_utc)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


def _simulate_exit(action: str, entry: float, sl: float, tp: float, future: pd.DataFrame) -> tuple[int, float | None, float | None, float | None, str | None]:
    if future.empty:
        return 0, None, None, None, "no_future_data"

    sl_dist = abs(entry - sl)
    tp_dist = abs(tp - entry)
    rr = (tp_dist / sl_dist) if sl_dist > 0 else 0.0

    for ts, row in future.iterrows():
        high = float(row["High"])
        low = float(row["Low"])

        if action == "BUY":
            hit_sl = low <= sl
            hit_tp = high >= tp
            if hit_sl and hit_tp:
                # 安全側: 同一足で両方ヒット時はSL優先
                pnl_r = -1.0
                return 1, sl, (sl - entry), pnl_r, f"both_hit_same_bar_sl_first@{ts.isoformat()}"
            if hit_sl:
                return 1, sl, (sl - entry), -1.0, f"sl_hit@{ts.isoformat()}"
            if hit_tp:
                return 1, tp, (tp - entry), rr, f"tp_hit@{ts.isoformat()}"
        else:
            hit_sl = high >= sl
            hit_tp = low <= tp
            if hit_sl and hit_tp:
                pnl_r = -1.0
                return 1, sl, (entry - sl), pnl_r, f"both_hit_same_bar_sl_first@{ts.isoformat()}"
            if hit_sl:
                return 1, sl, (entry - sl), -1.0, f"sl_hit@{ts.isoformat()}"
            if hit_tp:
                return 1, tp, (entry - tp), rr, f"tp_hit@{ts.isoformat()}"

    return 0, None, None, None, "still_open"


def run_verify(limit: int | None = None) -> None:
    db.init_db()

    with db.get_conn() as conn:
        signals = pd.read_sql_query(
            """
            SELECT s.id, s.ts_utc, s.pair, s.action, s.entry, s.sl, s.tp
            FROM signals s
            LEFT JOIN trades t ON t.signal_id = s.id
            WHERE s.action IN ('BUY', 'SELL')
              AND t.id IS NULL
            ORDER BY s.id ASC
            """,
            conn,
        )

    if signals.empty:
        logger.info("no pending BUY/SELL signals to verify")
        return

    if limit is not None:
        signals = signals.head(limit)

    pair_data: dict[str, pd.DataFrame] = {}
    for pair in signals["pair"].unique():
        m15 = data.fetch_m15(pair, config.DATA_PERIOD_DAYS)
        pair_data[pair] = m15

    inserted = 0
    for _, sig in signals.iterrows():
        signal_id = int(sig["id"])
        pair = str(sig["pair"])
        action = str(sig["action"])
        entry = float(sig["entry"])
        sl = float(sig["sl"])
        tp = float(sig["tp"])
        ts = _parse_ts(str(sig["ts_utc"]))

        candles = pair_data.get(pair, pd.DataFrame())
        if candles.empty:
            db.insert_trade(signal_id=signal_id, filled=0, note="no_data_for_pair")
            inserted += 1
            continue

        future = candles[candles.index > ts]
        filled, exit_price, pnl_price, pnl_r, note = _simulate_exit(action, entry, sl, tp, future)

        pnl_pips = None
        if filled and exit_price is not None and pnl_price is not None:
            pnl_pips = pnl_price / config.pip_size(pair)

        closed_ts = None
        if filled and note and "@" in note:
            closed_ts = note.split("@", 1)[1]

        db.insert_trade(
            signal_id=signal_id,
            filled=filled,
            exit_price=exit_price,
            pnl_pips=pnl_pips,
            pnl_r=pnl_r,
            closed_ts_utc=closed_ts,
            note=note,
        )
        inserted += 1

    logger.info("verification finished: inserted trades=%s", inserted)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify signals and populate trades table")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of signals to verify")
    args = parser.parse_args()

    try:
        run_verify(limit=args.limit)
    except Exception:
        logger.exception("verification failed")


if __name__ == "__main__":
    main()
