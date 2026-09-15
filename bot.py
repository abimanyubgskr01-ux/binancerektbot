import time
import requests
import sys

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'
BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/allForceOrders"

def main():
    print("Bot polling loop started directly...", flush=True)
    processed_orders = set()

    while True:
        try:
            print("Fetching data from Binance...", flush=True)
            response = requests.get(BINANCE_API_URL, timeout=10)
            print(f"Binance HTTP Status: {response.status_code}", flush=True)
            
            if response.status_code == 200:
                orders = response.json()
                print(f"Checked Binance: {len(orders)} active orders found.", flush=True)

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

                    if total_value < 0:  # Filter minimal $10,000
                        continue

                    if side == "BUY":
                        emoji = "🟢😾"
                    else:
                        emoji = "🔴😾"

                    msg = f"{emoji} <b>{symbol}</b> {side} {int(qty):,} @ {price:.8f}".rstrip('0').rstrip('.')
                    print(f"Alert sent: {msg}", flush=True)
                    
                    # Kirim ke Telegram
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
                    requests.post(url, json=payload, timeout=5)

            time.sleep(3)

        except Exception as e:
            print(f"Error in main loop: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
