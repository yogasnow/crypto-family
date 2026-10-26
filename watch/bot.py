#!/usr/bin/env python3
"""Owner-only Telegram bot for read-only market observations."""
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal

TOKEN = os.environ.get("CRYPTO_WATCH_BOT_TOKEN", "")
OWNER = os.environ.get("CRYPTO_WATCH_OWNER_ID", "")
DB_PATH = os.environ.get("CRYPTO_WATCH_DB", "crypto-watch.sqlite3")
API = f"https://api.telegram.org/bot{TOKEN}/"
PRODUCTS = {"BTC": "BTC-USD", "ETH": "ETH-USD"}


def request_json(url, data=None, timeout=25):
    headers = {"User-Agent": "CryptoWatchEducationalBot/0.1", "Accept": "application/json"}
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, body, headers), timeout=timeout) as r:
        return json.load(r)


def telegram(method, **params):
    result = request_json(API + method, params)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {result.get('description', 'unknown')}")
    return result["result"]


def send(chat_id, message):
    telegram("sendMessage", chat_id=chat_id, text=message[:4000], disable_web_page_preview="true")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS observations(symbol TEXT, ts INTEGER, price TEXT)")
    conn.execute("CREATE INDEX IF NOT EXISTS obs_symbol_ts ON observations(symbol,ts)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT OR IGNORE INTO settings VALUES('alerts_on','0')")
    conn.commit()
    return conn


def setting(conn, key):
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def set_setting(conn, key, value):
    conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
    conn.commit()


def price(symbol):
    product = PRODUCTS[symbol]
    data = request_json(f"https://api.exchange.coinbase.com/products/{product}/ticker", timeout=8)
    value = Decimal(str(data["price"]))
    if value <= 0:
        raise ValueError("non-positive price")
    observed = data.get("time")
    if not observed:
        raise ValueError("source timestamp missing")
    parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - parsed).total_seconds()
    if age < -30 or age > 120:
        raise ValueError("stale or future quote")
    return value, observed


def money(x):
    return f"${x:,.2f}"


def quote(symbol):
    p, observed = price(symbol)
    return p, f"{symbol}/USD: {money(p)}\nИсточник: Coinbase Exchange public ticker\nВремя источника: {observed}\nКотировка может измениться; это не рекомендация купить."


HELP = ("Crypto Watch · учебный бот\n"
        "/market — BTC и ETH сейчас\n"
        "/why — как читать событие\n"
        "/alerts_on и /alerts_off — оповещения о движении ≥2% за ~15 мин\n"
        "/learn — краткий урок риска\n"
        "/stop — выключить оповещения\n\n"
        "Бот только показывает данные и не совершает сделки.")


def handle(conn, message):
    user = message.get("from", {})
    chat = message.get("chat", {})
    # Private chat only, independently of which group mentions the bot.
    if str(user.get("id")) != OWNER or chat.get("type") != "private":
        return
    text = message.get("text", "").strip()
    parts = text.split()
    cmd = parts[0].split("@")[0].lower() if parts else ""
    chat_id = chat["id"]
    try:
        if cmd in ("/start", "/help"):
            reply = HELP
        elif cmd == "/market":
            results = []
            for sym in PRODUCTS:
                try:
                    results.append(quote(sym)[1])
                except Exception:
                    results.append(f"{sym}/USD: данные сейчас недоступны; прежнюю цену не показываю как новую.")
            reply = "\n\n".join(results)
        elif cmd == "/why":
            reply = ("Движение цены — наблюдение, не прогноз. Смотри время и источник, объём, "
                     "ликвидность, комиссии и сценарий потери. Новости не доказывают причину движения. "
                     "Если данные устарели — решение откладываем.")
        elif cmd == "/learn":
            reply = ("Урок 1/3: сначала назови сумму, потеря которой допустима. "
                     "Урок 2/3: spot без плеча и futures — разные риски; стоп-лосс не гарантирует предел убытка. "
                     "Урок 3/3: проверь источник котировки и полную стоимость сделки. "
                     "Сравни время источника и текущую цену через /market.")
        elif cmd == "/alerts_on":
            set_setting(conn, "alerts_on", "1")
            reply = "Оповещения включены: BTC/ETH, порог 2% за примерно 15 минут. Источник — публичные данные; отсутствие сообщения не означает отсутствие риска."
        elif cmd in ("/alerts_off", "/stop"):
            set_setting(conn, "alerts_on", "0")
            reply = "Оповещения выключены."
        else:
            reply = "Не поняла команду. Открой /help. Финансовые поручения свободным текстом не исполняются."
    except Exception:
        reply = "Источник или расчёт сейчас недоступен. Никаких ордеров не отправляла; попробуй позже."
    send(chat_id, reply)


def poll_market(conn):
    now = int(time.time())
    for sym in PRODUCTS:
        try:
            p, observed = price(sym)
        except Exception:
            continue
        with conn:
            conn.execute("INSERT INTO observations VALUES(?,?,?)", (sym, now, str(p)))
            conn.execute("DELETE FROM observations WHERE ts<?", (now-3600,))
        if setting(conn, "alerts_on") != "1":
            continue
        row = conn.execute("SELECT ts,price FROM observations WHERE symbol=? AND ts BETWEEN ? AND ? ORDER BY ts ASC LIMIT 1", (sym, now-1200, now-600)).fetchone()
        if not row:
            continue
        old = Decimal(row[1]); movement = (p/old-1)*100
        cooldown = int(setting(conn, f"last_alert_{sym}") or 0)
        if abs(movement) >= 2 and now-cooldown >= 3600:
            direction = "выросла" if movement > 0 else "снизилась"
            msg = (f"🔔 {sym}/USD: цена {direction} на {abs(movement):.2f}% за ~15 мин.\n"
                   f"Сейчас: {money(p)} · источник Coinbase Exchange · {observed}\n"
                   "Это наблюдение, не сигнал к покупке/продаже. Проверь причину и риск: /why")
            send(int(OWNER), msg)
            set_setting(conn, f"last_alert_{sym}", now)


def main():
    if not TOKEN or not OWNER.isdigit():
        sys.exit("Set CRYPTO_WATCH_BOT_TOKEN and CRYPTO_WATCH_OWNER_ID in a private environment.")
    conn = db(); offset = None; next_market = 0
    print("Crypto Watch started: owner-only, read-only market observations.", flush=True)
    while True:
        try:
            if time.monotonic() >= next_market:
                poll_market(conn); next_market = time.monotonic()+60
            params = {"timeout": 20, "allowed_updates": json.dumps(["message"])}
            if offset is not None:
                params["offset"] = offset
            updates = telegram("getUpdates", **params)
            for item in updates:
                offset = item["update_id"]+1
                if "message" in item:
                    handle(conn, item["message"])
        except KeyboardInterrupt:
            break
        except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, ValueError) as err:
            print(f"Temporary service error: {type(err).__name__}", file=sys.stderr, flush=True)
            time.sleep(5)
    conn.close()


if __name__ == "__main__":
    main()
