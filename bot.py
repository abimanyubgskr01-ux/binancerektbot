import time
import requests
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

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
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_bot():
    print("Bot polling loop started in background...")
    processed_orders = set()
    
    # Kirim pesan tanda aktif
    send_telegram_message("🟢 <b>Bot Binance Liquidation resmi 24/7 di Railway!</b>")
    
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
                        
                    # Filter minimal nilai likuidasi (ubah ke 0 dulu untuk tes awal)
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

# --- Web Server Utama (Foreground Process) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    # Jalankan bot polling di background thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Jalankan web server di proses utama (blocking agar Railway menganggap app terus hidup)
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Main web server running on port {port} (Keeping container alive)...")
    server.serve_forever()
