#!/usr/bin/env python3
"""Daily public-market digest for owner delivery through OpenClaw automation."""
from decimal import Decimal

from bot import PRODUCTS, money, price, request_json


def line(symbol):
    current, source_time = price(symbol)
    product = PRODUCTS[symbol]
    stats = request_json(f"https://api.exchange.coinbase.com/products/{product}/stats", timeout=8)
    opened = Decimal(str(stats["open"]))
    if opened <= 0:
        raise ValueError("invalid 24h open")
    change = (current / opened - 1) * 100
    high = Decimal(str(stats["high"]))
    low = Decimal(str(stats["low"]))
    if low <= 0 or high < low:
        raise ValueError("invalid daily range")
    day_range = (high / low - 1) * 100
    sign = "+" if change >= 0 else ""
    if abs(change) >= 5 or day_range >= 8:
        label = "⚠️ Повышенная осторожность"
        reason = "Сильное суточное движение/широкий диапазон: вероятность резкого разворота выше; не входить только из-за новости или роста."
    elif abs(change) >= 2 or day_range >= 4:
        label = "🟡 Наблюдать"
        reason = "Рынок заметно двигался; проверь причину, комиссии и допустимую потерю до любого решения."
    else:
        label = "🔎 Спокойнее по этой метрике, но не безопасно"
        reason = "Суточный диапазон меньше выбранного порога; это не говорит о завтрашней цене и не делает актив безрисковым."
    return (f"{symbol}/USD: {money(current)} · {sign}{change:.2f}% за ~24 ч · диапазон {day_range:.2f}%\n"
            f"{label}. {reason}\nИсточник: Coinbase Exchange · {source_time}")


def main():
    items = []
    for symbol in PRODUCTS:
        try:
            items.append(line(symbol))
        except Exception:
            items.append(f"{symbol}/USD: данные недоступны или устарели; цену не показываю.")
    print("📊 Crypto Watch · утренняя сводка и карта риска\n" + "\n\n".join(items)
          + "\n\nПравило оценки: повышенный риск при движении ≥5% или диапазоне ≥8% за сутки; наблюдение при ≥2% или ≥4%. Это простые пороги, не прогноз."
          + "\nВывод: ни BTC, ни ETH нельзя назвать безопасным вложением по одной сводке. Если не определены цель и сумма допустимой потери, лучший следующий шаг — пауза и обучение, не сделка. Реальные сделки бот не совершает.")


if __name__ == "__main__":
    main()
