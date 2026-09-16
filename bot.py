import json
import websocket
import requests
import time

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'

def get_top_100_streams():
    try:
        print("Mengambil daftar Top 100 koin Binance Futures...", flush=True)
        res = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
        data = res.json()
        # Ambil 100 koin teratas aja biar panjang URL-nya nggak ditolak server (aman dari limit)
        symbols = [s['symbol'].lower() for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'][:100]
        streams = [f"{s}@aggTrade" for s in symbols]
        return streams
    except Exception as e:
        print(f"Gagal mengambil daftar koin: {e}", flush=True)
        return ['btcusdt@aggTrade', 'ethusdt@aggTrade', 'solusdt@aggTrade']

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
        
        # Karena kita gabungin banyak stream di URL, datanya dibungkus di key 'data'
        data = payload.get('data')
        if not data or data.get('e') != 'aggTrade': 
            return

        symbol = data.get('s')
        price = float(data.get('p'))
        qty = float(data.get('q'))
        total_value = price * qty
        is_buyer_maker = data.get('m')

        # FILTER VOLUME (Masih gue pasang di $1 biar lu bisa liat buktinya langsung ngalir)
        if total_value < 1:
            return

        side = "🔴 SELL" if is_buyer_maker else "🟢 BUY"
        emoji = "🐋" if total_value > 50000 else "🦈"
        
        msg = f"{emoji} <b>{symbol}</b> {side}\n💰 Value: ${total_value:,.2f}\n📦 Qty: {qty:,.2f} @ {price:.8f}"
        
        print(f"Alert sent: {symbol} {side} ${total_value:,.2f}", flush=True)
        send_telegram_message(msg)

    except Exception as e:
        print(f"BONGKAR ERROR: {e}", flush=True)

def on_error(ws, error):
    print(f"WebSocket error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed, reconnecting...", flush=True)

def on_open(ws):
    print("Connected to Binance Combined Stream! Data harusnya langsung mancur...", flush=True)

if __name__ == "__main__":
    websocket.enableTrace(False) 
    while True:
        try:
            # Kita rakit URL-nya langsung di sini
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
