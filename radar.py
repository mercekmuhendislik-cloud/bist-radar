import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import time # Limitleri aşmak için gerekli

# --- AYARLAR ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# Hisse listesi
bist_raw = "PRZMA, AKSUE, SONME, USAK, SANFM, EYGYO, ESCAR, TDGYO, DERHL, GENTS, SELVA, ASELS, ATEKS, ATSYH, CASA, KUVVA, ALTNY, COSMO, DGATE, ECOGR, FORTE, FRIGO, FZLGY, INVES, IHAAS, IZFAS, LILAK, MANAS"
selected_stocks = [k.strip() + ".IS" for k in bist_raw.split(",")]

def calculate_t3(src, length=50, vf=0.7):
    # T3 hesaplama mantığı aynı kalıyor
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

def process_ticker(ticker):
    # Limitleri aşmak için 'Ticker' nesnesi üzerinden veri çekiyoruz
    try:
        t = yf.Ticker(ticker)
        df_h = t.history(period="60d", interval="1h")
        df_d = t.history(period="2y", interval="1d")
        
        if df_h.empty or df_d.empty: return None

        last_close = df_h['Close'].iloc[-1]
        daily_200_sma = df_d['Close'].rolling(window=200).mean().iloc[-1]
        
        # Sinyal kontrolü (Basit T3 örneği)
        t3_val = calculate_t3(df_h['Close']).iloc[-1]
        
        if last_close > t3_val:
            sma_icon = "🟢" if last_close > daily_200_sma else "🔴"
            return f"<b>{ticker.replace('.IS','')}</b> | Fiyat: {last_close:.2f}\nBB Orta 200: {sma_icon}\n"
    except Exception as e:
        print(f"{ticker} hatası: {e}")
    return None

# --- SIRALI ÇALIŞTIRMA (Limit Dostu) ---
results = []
for ticker in selected_stocks:
    res = process_ticker(ticker)
    if res:
        results.append(res)
    time.sleep(1.5) # Her hisse arasında 1.5 saniye bekle (Limiti aşmanın anahtarı budur)

if results:
    send_telegram_msg("🎯 <b>BIST Radar Sonuçları</b>\n\n" + "\n".join(results))
else:
    send_telegram_msg("✅ Tarama bitti, kriterlere uyan sinyal yok.")
