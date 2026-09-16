import json
import websocket
import requests
import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'

# ====================================================
# INI OBATNYA BIAR RAILWAY NGGAK NGE-RESTART BOT LU
# ====================================================
def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running mantap!")
            
    # Railway otomatis ngasih environment variable PORT
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Dummy web server jalan di port {port} buat ngakalin Railway...", flush=True)
    server.serve_forever()

def get_top_100_streams():
    try:
        res = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
        data = res.json()
        symbols = [s['symbol'].lower() for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'][:100]
        return [f"{s}@aggTrade" for s in symbols]
    except Exception:
        return ['btcusdt@aggTrade']

def send_telegram_message(text):
    def _send():
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass
    threading.Thread(target=_send).start()

def on_message(ws, message):
    try:
        payload = json.loads(message)
        data = payload.get('data')
        
        if not data or data.get('e') != 'aggTrade': 
            return

        symbol = data.get('s')
        price = float(data.get('p'))
        qty = float(data.get('q'))
        total_value = price * qty

        # Tahan di $50,000 ya, biar telegram lu ga meledak
        if total_value < 50000:
            return

        is_buyer_maker = data.get('m')
        side = "🔴 SELL" if is_buyer_maker else "🟢 BUY"
        emoji = "🐋" if total_value > 100000 else "🦈"
        
        msg = f"{emoji} <b>{symbol}</b> {side}\n💰 Value: ${total_value:,.2f}\n📦 Qty: {qty:,.2f} @ {price:.8f}"
        
        print(f"PAUS DETECTED: {symbol} {side} ${total_value:,.2f}", flush=True)
        send_telegram_message(msg)

    except Exception:
        pass

def on_error(ws, error):
    print(f"WebSocket error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed, reconnecting...", flush=True)

def on_open(ws):
    print("Connected! Radar paus aktif, menunggu transaksi di atas $50,000...", flush=True)

if __name__ == "__main__":
    websocket.enableTrace(False) 
    
    # NYALAKAN SERVER BOHONGAN DI BACKGROUND
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    while True:
        try:
            streams = get_top_100_streams()
            stream_string = '/'.join(streams)
            ws_url = f"wss://fstream.binance.com/stream?streams={stream_string}"
            
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            print("Connecting directly with 100 streams in URL...", flush=True)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"Connection lost, retrying in 5 seconds...", flush=True)
            time.sleep(5)
