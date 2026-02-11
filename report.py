from __future__ import annotations

import sqlite3

import pandas as pd

import config
import db


def _max_drawdown(cumulative: pd.Series) -> float:
    if cumulative.empty:
        return 0.0
    running_peak = cumulative.cummax()
    drawdown = running_peak - cumulative
    return float(drawdown.max())


def main() -> None:
    db.init_db()
    conn = sqlite3.connect(config.DB_PATH)
    try:
        trades = pd.read_sql_query(
            """
            SELECT t.*, s.entry, s.sl, s.tp
            FROM trades t
            LEFT JOIN signals s ON s.id = t.signal_id
            WHERE t.filled = 1
            ORDER BY COALESCE(t.closed_ts_utc, ''), t.id
            """,
            conn,
        )

        total = int(len(trades))
        if total == 0:
            print("総トレード数: 0")
            print("勝率: 0.00%")
            print("平均RR: 0.000")
            print("最大DD(R): 0.000")
            print("累積R: 0.000")
            return

        wins = int((trades["pnl_r"] > 0).sum())
        win_rate = (wins / total) * 100

        rr_values = (
            (trades["tp"] - trades["entry"]).abs() / (trades["entry"] - trades["sl"]).abs()
        ).replace([pd.NA, float("inf")], pd.NA)
        avg_rr = float(rr_values.dropna().mean()) if not rr_values.dropna().empty else 0.0

        pnl_r = trades["pnl_r"].fillna(0.0)
        cumulative_r = pnl_r.cumsum()
        max_dd = _max_drawdown(cumulative_r)

        print(f"総トレード数: {total}")
        print(f"勝率: {win_rate:.2f}%")
        print(f"平均RR: {avg_rr:.3f}")
        print(f"最大DD(R): {max_dd:.3f}")
        print(f"累積R: {float(cumulative_r.iloc[-1]):.3f}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
