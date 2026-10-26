#!/usr/bin/env python3
"""One-shot read-only market check for OpenClaw automation. NO_REPLY suppresses delivery."""
import fcntl
import os
import sqlite3
import sys
import time
from decimal import Decimal
from pathlib import Path

from bot import PRODUCTS, price, money

STATE = Path(os.environ.get("CRYPTO_WATCH_MONITOR_DB", str(Path(__file__).resolve().parent / "monitor.sqlite3")))


def run():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(str(STATE) + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        conn = sqlite3.connect(STATE)
        conn.execute("CREATE TABLE IF NOT EXISTS observations(symbol TEXT, ts INTEGER, price TEXT, source_time TEXT)")
        conn.execute("CREATE INDEX IF NOT EXISTS obs_time ON observations(symbol,ts)")
        conn.execute("CREATE TABLE IF NOT EXISTS last_alert(symbol TEXT PRIMARY KEY, ts INTEGER)")
        now = int(time.time())
        alerts = []
        for sym in PRODUCTS:
            try:
                current, source_time = price(sym)
            except Exception:
                continue
            with conn:
                conn.execute("INSERT INTO observations VALUES(?,?,?,?)", (sym, now, str(current), source_time))
                conn.execute("DELETE FROM observations WHERE ts<?", (now-3600,))
            row = conn.execute("SELECT ts,price FROM observations WHERE symbol=? AND ts BETWEEN ? AND ? ORDER BY ts ASC LIMIT 1", (sym, now-1200, now-600)).fetchone()
            if not row:
                continue
            prior = Decimal(row[1]); change = (current/prior-1)*100
            last = conn.execute("SELECT ts FROM last_alert WHERE symbol=?", (sym,)).fetchone()
            if abs(change) < 2 or (last and now-last[0] < 3600):
                continue
            direction = "выросла" if change > 0 else "снизилась"
            alerts.append(f"🔔 Crypto Watch · {sym}/USD {direction} на {abs(change):.2f}% примерно за 15 минут.\nСейчас: {money(current)} · Coinbase Exchange · {source_time}.\n⚠️ Риск резкого разворота повышен. Не входи только из-за импульса: сначала проверь новости, стоимость сделки и допустимую потерю. Это не прогноз и не команда купить.")
            with conn:
                conn.execute("INSERT INTO last_alert(symbol,ts) VALUES(?,?) ON CONFLICT(symbol) DO UPDATE SET ts=excluded.ts", (sym, now))
        conn.close()
        print("\n\n".join(alerts) if alerts else "NO_REPLY")


if __name__ == "__main__":
    try:
        run()
    except BlockingIOError:
        print("NO_REPLY")
    except Exception as err:
        print("NO_REPLY")
        print(f"Crypto Watch monitor error: {type(err).__name__}", file=sys.stderr)
