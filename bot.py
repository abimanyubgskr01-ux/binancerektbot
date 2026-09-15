import time
import requests
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- Mini Web Server agar Railway tidak mematikan kontainer ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Web server started on port {port}")
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
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_bot():
    print("Bot polling loop started...")
    processed_orders = set()
    
    # Tes kirim pesan penanda bot nyala
    send_telegram_message("🟢 <b>Bot Binance Liquidation berhasil aktif di Railway!</b>")
    
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

if __name__ == "__main__":
    # Jalankan web server di background thread agar kontainer tidak di-stop Railway
    threading.Thread(target=run_web_server, daemon=True).start()
    # Jalankan bot utama
    run_bot()