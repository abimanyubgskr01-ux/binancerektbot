import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# --- Dummy Web Server untuk Render Free Tier ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- Konfigurasi Bot Telegram & Binance ---
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

def run_bot():
    print("Bot loop started...")
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
                        
                    # Filter minimal nilai (atur ke 0 atau sesuai kebutuhan)
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
    # Jalankan web server di background thread agar Render mendeteksi port aktif
    threading.Thread(target=run_web_server, daemon=True).start()
    # Jalankan bot utama
    run_bot()