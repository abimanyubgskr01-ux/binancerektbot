import json
import websocket
import requests

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'
WS_URL = "fstream.binance.com/ws/!forceOrder@arr"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}", flush=True)

def on_message(ws, message):
    print(f"RAW DATA: {message}", flush=True)
    try:
        data = json.loads(message)
        order = data.get('o', {})
        symbol = order.get('s')
        if not symbol: return

        side = order.get('S')
        price = float(order.get('p'))
        qty = float(order.get('q'))
        total_value = price * qty

        if total_value < 0:  # Ubah ke 10000 kalau udah bener
            return

        emoji = "🟢😾" if side == "BUY" else "🔴😾"
        msg = f"{emoji} <b>{symbol}</b> {side} {int(qty):,} @ {price:.8f}".rstrip('0').rstrip('.')
        
        send_telegram_message(msg)
    except Exception as e:
        pass

def on_error(ws, error):
    print(f"WebSocket error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed! Code: {close_status_code}, Msg: {close_msg}", flush=True)

def on_open(ws):
    print("Connected to WebSocket!", flush=True)

if __name__ == "__main__":
    # INI YANG BAKAL BONGKAR SEMUANYA
    websocket.enableTrace(True) 
    
    while True:
        try:
            ws = websocket.WebSocketApp(
                f"wss://{WS_URL}",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            print("Connecting directly to Binance (No Proxy)...", flush=True)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"Fatal error: {e}", flush=True)
            import time
            time.sleep(5)
