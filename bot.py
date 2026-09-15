import time
import requests

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'
BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/allForceOrders"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def main():
    print("Bot started on Render cloud...")
    processed_orders = set()

    while True:
        try:
            response = requests.get(BINANCE_API_URL, timeout=10)
            if response.status_code == 200:
                orders = response.json()
                for order in orders:
                    order_id = f"{order.get('s')}_{order.get('T')}_{order.get('q')}"

                    if order_id in processed_orders:
                        continue

                    symbol = order.get('s')
                    side = order.get('S')
                    price = float(order.get('p'))
                    qty = float(order.get('q'))
                    total_value = price * qty

                    processed_orders.add(order_id)
                    if len(processed_orders) > 500:
                        processed_orders.pop()

                    # Atur filter minimal nilai likuidasi (misal $10,000)
                    if total_value < 0:
                        continue

                    if side == "BUY":
                        emoji = "🟢😾"
                    else:
                        emoji = "🔴😾"

                    msg = f"{emoji} <b>{symbol}</b> {side} {int(qty):,} @ {price:.8f}".rstrip('0').rstrip('.')
                    print(f"Alert sent: {msg}")
                    send_telegram_message(msg)

            time.sleep(3)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()