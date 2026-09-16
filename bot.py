import json
import websocket
import requests
import time

TELEGRAM_BOT_TOKEN = '8978692754:AAG_zOzdygCWBtibC0QPKGbmQvsqIas2xD4'
TELEGRAM_CHAT_ID = '@BinanceFuturesREKTbot'

def get_all_usdt_symbols():
    try:
        print("Mengambil daftar koin Binance Futures...", flush=True)
        res = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
        data = res.json()
        # LIMIT: Ambil 150 koin pertama aja, soalnya Binance cuma ngizinin maksimal 200 stream per koneksi!
        symbols = [s['symbol'].lower() for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'][:150]
        return symbols
    except Exception as e:
        print(f"Gagal mengambil daftar koin: {e}", flush=True)
        return ['btcusdt', 'ethusdt', 'solusdt']

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Tangkap pesan konfirmasi dari Binance kalau proses subscribe berhasil
        if 'result' in data or 'id' in data:
            print(f"System: {message}", flush=True)
            return
            
        if data.get('e') != 'aggTrade': 
            return

        symbol = data.get('s')
        price = float(data.get('p'))
        qty = float(data.get('q'))
        total_value = price * qty
        is_buyer_maker = data.get('m')

        # FILTER VOLUME (Diturunin ke $10,000 dulu buat ngetes biar datanya cepet keluar)
        if total_value < 10000:
            return

        side = "🔴 SELL" if is_buyer_maker else "🟢 BUY"
        emoji = "🐋" if total_value > 50000 else "🦈"
        
        msg = f"{emoji} <b>{symbol}</b> {side}\n💰 Value: ${total_value:,.2f}\n📦 Qty: {qty:,.2f} @ {price:.8f}"
        
        print(f"Alert sent: {symbol} {side} ${total_value:,.2f}", flush=True)
        send_telegram_message(msg)

    except Exception:
        pass

def on_error(ws, error):
    print(f"WebSocket error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed, reconnecting...", flush=True)

def on_open(ws):
    print("Connected to WebSocket! Memulai proses langganan...", flush=True)
    symbols = get_all_usdt_symbols()
    streams = [f"{s}@aggTrade" for s in symbols]
    
    chunk_size = 50
    for i in range(0, len(streams), chunk_size):
        chunk = streams[i:i + chunk_size]
        sub_msg = {
            "method": "SUBSCRIBE",
            "params": chunk,
            "id": i
        }
        ws.send(json.dumps(sub_msg))
        time.sleep(1) # Jeda aman biar ga ditolak server
        
    print(f"SUKSES! Bot sekarang memantau {len(streams)} koin secara real-time!", flush=True)

if __name__ == "__main__":
    websocket.enableTrace(False) 
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://fstream.binance.com/ws",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            print("Connecting to Binance Global Stream...", flush=True)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"Connection lost, retrying in 5 seconds...", flush=True)
            time.sleep(5)
