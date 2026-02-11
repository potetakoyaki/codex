from __future__ import annotations

import argparse
import logging
import time

import config
import data
import db
import engine
import indicators

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_cycle() -> None:
    db.init_db()
    for pair in config.PAIRS:
        try:
            m15 = data.fetch_m15(pair, config.DATA_PERIOD_DAYS)
            h1 = data.resample_ohlcv(m15, config.H1_RULE)
            h4 = data.resample_ohlcv(m15, config.H4_RULE)

            m15_i = indicators.add_indicators(m15)
            h1_i = indicators.add_indicators(h1)
            h4_i = indicators.add_indicators(h4)

            signal = engine.evaluate_signal(pair, m15_i, h1_i, h4_i)
            signal_id = db.insert_signal(signal)
            logger.info("pair=%s action=%s signal_id=%s reason=%s", pair, signal.action, signal_id, signal.reason)
        except Exception:
            logger.exception("pair=%s processing failed; continue safely with WAIT philosophy", pair)


def main() -> None:
    parser = argparse.ArgumentParser(description="FX signal runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Run one cycle")
    group.add_argument("--schedule", action="store_true", help="Run every 15 minutes")
    args = parser.parse_args()

    if args.once:
        run_cycle()
        return

    while True:
        try:
            run_cycle()
        except Exception:
            logger.exception("unhandled cycle error")
        time.sleep(config.SCHEDULE_SECONDS)


if __name__ == "__main__":
    main()
