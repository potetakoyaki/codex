from __future__ import annotations

import sqlite3
from contextlib import contextmanager

import config


@contextmanager
def get_conn(db_path: str = config.DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = config.DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,
                pair TEXT NOT NULL,
                action TEXT NOT NULL,
                score INTEGER NOT NULL,
                entry REAL,
                sl REAL,
                tp REAL,
                reason TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER NOT NULL,
                filled INTEGER NOT NULL DEFAULT 0,
                exit_price REAL,
                pnl_pips REAL,
                pnl_r REAL,
                closed_ts_utc TEXT,
                note TEXT,
                FOREIGN KEY(signal_id) REFERENCES signals(id)
            )
            """
        )


def insert_signal(signal: config.SignalResult, db_path: str = config.DB_PATH) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO signals (ts_utc, pair, action, score, entry, sl, tp, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.ts_utc,
                signal.pair,
                signal.action,
                signal.score,
                signal.entry,
                signal.sl,
                signal.tp,
                signal.reason,
            ),
        )
        return int(cur.lastrowid)


def insert_trade(
    signal_id: int,
    filled: int = 0,
    exit_price: float | None = None,
    pnl_pips: float | None = None,
    pnl_r: float | None = None,
    closed_ts_utc: str | None = None,
    note: str | None = None,
    db_path: str = config.DB_PATH,
) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO trades (signal_id, filled, exit_price, pnl_pips, pnl_r, closed_ts_utc, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (signal_id, filled, exit_price, pnl_pips, pnl_r, closed_ts_utc, note),
        )
        return int(cur.lastrowid)
