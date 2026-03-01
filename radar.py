import yfinance as yf
import pandas as pd
import requests
import os
import time

# --- AYARLAR ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if not TOKEN or not CHAT_ID:
        print("Hata: Token veya Chat ID bulunamadı!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hatası: {e}")

# Sinyal veren ana listeni buraya aldım
stocks = ["PRZMA", "AKSUE", "SONME", "USAK", "SANFM", "EYGYO", "ESCAR", "TDGYO", "DERHL", "GENTS", "SELVA", "ASELS"]

def calculate_t3(src, length=50, vf=0.7):
    ema1 = src.ewm(span=length, adjust=False).mean()
    ema2 = ema1.ewm(span=length, adjust=False).mean()
    ema3 = ema2.ewm(span=length, adjust=False).mean()
    ema4 = ema3.ewm(span=length, adjust=False).mean()
    ema5 = ema4.ewm(span=length, adjust=False).mean()
    ema6 = ema5.ewm(span=length, adjust=False).mean()
    c1 = -vf**3
    c2 = 3*vf**2 + 3*vf**3
    c3 = -6*vf**2 - 3*vf - 3*vf3 if 'vf3' in locals() else -6*vf**2 - 3*vf - 3*vf**3
    c4 = 1 + 3*vf + vf**3 + 3*vf**2
    return c1 * ema6 + c2 * ema5 + c3 * ema4 + c4 * ema3

def check_logic(ticker):
    try:
        # GitHub engeline takılmamak için tekil ve yavaş çekim
        data = yf.Ticker(f"{ticker}.IS")
        df = data.history(period="60d", interval="1h")
        if df.empty or len(df) < 50: return None
        
        last_price = df['Close'].iloc[-1]
        t3_val = calculate_t3(df['Close']).iloc[-1]
        
        # Basit bir sinyal kontrolü (T3 altındaysa veya üstündeyse)
        if last_price > t3_val:
            return f"<b>{ticker}</b>: {last_price:.2f} 🟢"
    except:
        return None
    return None

# --- ANA ÇALIŞTIRICI ---
print("Tarama başlatıldı...")
results = []
for s in stocks:
    res = check_logic(s)
    if res:
        results.append(res)
    time.sleep(1) # Banlanmamak için her hisse arası 1 saniye bekle

if results:
    msg = "🎯 <b>BIST Radar Sinyalleri</b>\n\n" + "\n".join(results)
    send_telegram_msg(msg)
else:
    # Boş gitmesin, çalıştığını anlayalım
    send_telegram_msg("✅ Tarama yapıldı: Şu an listedeki hisselerde sinyal yok.")
