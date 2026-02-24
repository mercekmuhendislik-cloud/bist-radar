import yfinance as yf
import pandas as pd
import requests
import os
import warnings

warnings.filterwarnings('ignore')

# GitHub Secrets'tan gelen bilgiler
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if not message.strip(): return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Hata: {e}")

def calculate_t3(src, length, vf, multiplier):
    ema1 = src.ewm(span=length, adjust=False).mean()
    ema2 = ema1.ewm(span=length, adjust=False).mean()
    ema3 = ema2.ewm(span=length, adjust=False).mean()
    ema4 = ema3.ewm(span=length, adjust=False).mean()
    ema5 = ema4.ewm(span=length, adjust=False).mean()
    ema6 = ema5.ewm(span=length, adjust=False).mean()
    c1 = -(vf**3)
    c2 = 3*(vf**2) + 3*(vf**3)
    c3 = -6*(vf**2) - 3*vf - 3*(vf**3)
    c4 = 1 + 3*vf + (vf**3) + 3*(vf**2)
    return c1 * ema6 + c2 * ema5 + c3 * ema4 + c4 * ema3

def check_signal(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if len(df) < 50: return None
        src = (df['High'] + df['Low'] + df['Close']) / 3
        # 4S, 2S ve 1S Kontrolleri (Basit versiyon)
        t3_val = calculate_t3(src, 50, 0.7, 3).iloc[-1]
        if df['Close'].iloc[-1] > t3_val:
            return ticker.replace(".IS", "")
    except: return None
    return None

# Ana Çalıştırma
if __name__ == "__main__":
    hisseler = ["ESCAR.IS", "FORTE.IS", "ASELS.IS", "THYAO.IS"] # Buraya taranmasını istediğin ana listeyi ekleyebilirsin
    pozitifler = []
    for h in hisseler:
        res = check_signal(h)
        if res: pozitifler.append(res)
    
    if pozitifler:
        msg = "🚀 *VIP RADAR SİNYAL ÇAKTI!*\n\n" + "\n".join([f"✅ {h}" for h in pozitifler])
        send_telegram_msg(msg)
