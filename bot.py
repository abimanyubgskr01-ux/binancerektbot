import json
import websocket
import requests

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'

# 1. Tulis koin-koin yang mau lu pantau di sini (Wajib huruf kecil dan pakai 'usdt' di belakangnya)
COINS = ['btcusdt', 'ethusdt', 'solusdt', 'bnbusdt', 'dogeusdt', 'pepeusdt']

# 2. Format URL untuk gabungin banyak koin dalam 1 stream
STREAMS = '/'.join([f"{coin}@aggTrade" for coin in COINS])
WS_URL = f"fstream.binance.com/stream?streams={STREAMS}"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def on_message(ws, message):
    try:
        payload = json.loads(message)
        
        # Karena kita langganan banyak stream, datanya dibungkus di dalam key 'data'
        data = payload.get('data', {})
        
        if data.get('e') != 'aggTrade': 
            return

        symbol = data.get('s')
        price = float(data.get('p'))
        qty = float(data.get('q'))
        total_value = price * qty
        is_buyer_maker = data.get('m')

        # 3. FILTER VOLUME PAUS (Contoh: Notif hanya kalau ada transaksi di atas $50,000)
        # Lu bisa atur angka ini sesuai rasio risk-to-reward lu
        if total_value < 50000:
            return

        # Di sistem Binance: kalau Taker is Maker (True) = SELL. Kalau False = BUY.
        side = "🔴 SELL" if is_buyer_maker else "🟢 BUY"
        emoji = "🐋" if total_value > 100000 else "🦈"
        
        msg = f"{emoji} <b>{symbol}</b> {side}\n💰 Value: ${total_value:,.2f}\n📦 Qty: {qty:,.2f} @ {price:.8f}"
        
        print(f"Alert sent: {symbol} {side} ${total_value:,.2f}", flush=True)
        send_telegram_message(msg)

    except Exception as e:
        pass

def on_error(ws, error):
    print(f"WebSocket error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed, reconnecting...", flush=True)

def on_open(ws):
    print("Connected to Binance Whale Alert Stream!", flush=True)

if __name__ == "__main__":
    websocket.enableTrace(False) # Gue matiin trace-nya biar log lu nggak nyampah
    while True:
        try:
            ws = websocket.WebSocketApp(
                f"wss://{WS_URL}",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            print(f"Connecting to streams: {STREAMS}", flush=True)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"Connection lost, retrying in 5 seconds...", flush=True)
            import time
            time.sleep(5)
