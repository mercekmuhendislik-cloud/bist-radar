import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
import os
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# --- TELEGRAM AYARLARI ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

# --- 1. ŞİRKET LİSTESİ (Loglardaki hataları azaltmak için temizlenmiş liste) ---
bist_raw = "ACSEL, ADEL, ADESE, AGHOL, AGESA, AGROT, AKBNK, AKCNS, AKSA, AKSEN, ALARK, ALBRK, ALFAS, ARCLK, ARDYZ, ASELS, ASTOR, BIMAS, BRISA, CANTE, CCOLA, CWENE, DOAS, DOHOL, EGEEN, EKGYO, ENJSA, ENKAI, EREGL, FROTO, GARAN, GUBRF, HALKB, HEKTS, ISCTR, KCHOL, KONTR, KOZAA, KOZAL, KRDMD, MAVI, MGROS, MIATK, ODAS, OTKAR, OYAKC, PGSUS, PETKM, SAHOL, SASA, SISE, SKBNK, SOKM, TAVHL, TCELL, THYAO, TKFEN, TOASO, TSKB, TTKOM, TTRAK, TUPRS, VAKBN, VESBE, VESTL, YKBNK"
selected_stocks = [k.strip() + ".IS" for k in bist_raw.split(",") if k.strip()]

# --- 2. HESAPLAMA MOTORU ---
def calculate_t3(src, length, vf, multiplier):
    def ema(s, l): return s.ewm(span=l, adjust=False).mean()
    e1 = ema(src, length); e2 = ema(e1, length); e3 = ema(e2, length)
    e4 = ema(e3, length); e5 = ema(e4, length); e6 = ema(e5, length)
    vf3, vf2 = vf**3, vf**2
    if multiplier == 3:
        c1, c2, c3, c4 = -vf3, 3*vf2 + 3*vf3, -6*vf2 - 3*vf - 3*vf3, 1 + 3*vf + vf3 + 3*vf2
    else:
        c1, c2, c3, c4 = -vf3, 4*vf2 + 4*vf3, -8*vf2 - 4*vf - 4*vf3, 1 + 4*vf + vf3 + 4*vf2
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

def check_formation(df, last_price):
    if len(df) < 100: return False
    src = (df['High'] + df['Low'] + df['Close']) / 3
    t_siyah = calculate_t3(src, 50, 0.70, 3).iloc[-1]
    t_mor   = calculate_t3(src, 87, 0.90, 4).iloc[-1]
    t_sari  = calculate_t3(src, 37, 0.90, 4).iloc[-1]
    return (t_sari < t_siyah < t_mor and last_price > t_sari)

# --- 3. ANALİZ FONKSİYONU ---
def process_ticker(ticker, df_h, df_d):
    try:
        if df_h is None or df_h.empty or df_d is None or df_d.empty: return None
        last_close = df_h['Close'].iloc[-1]
        daily_200_sma = df_d['Close'].rolling(window=200).mean().iloc[-1]
        df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s = check_formation(df_h, last_close)
        f2s = check_formation(df_2s, last_close)
        f4s = check_formation(df_4s, last_close)

        if any([f1s, f2s, f4s]):
            t_name = ticker.replace(".IS","")
            sma_status = "🟢" if last_close > daily_200_sma else "🔴"
            msg = f"<b>{t_name}</b> | Fiyat: {last_close:.2f}\nSMA 200: {sma_status} | Sinyal: {'1S ' if f1s else ''}{'2S ' if f2s else ''}{'4S' if f4s else ''}\n"
            return msg
    except: return None

# --- 4. ÇALIŞTIRMA ---
h_data = yf.download(selected_stocks, period="60d", interval="1h", group_by='ticker', progress=False)
d_data = yf.download(selected_stocks, period="2y", interval="1d", group_by='ticker', progress=False)

results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_ticker, t, h_data.get(t), d_data.get(t)) for t in selected_stocks]
    for f in as_completed(futures):
        res = f.result()
        if res: results.append(res)

# --- 5. GÖNDERİM ---
if results:
    final_msg = "🎯 <b>BIST Radar Sinyalleri</b>\n\n" + "\n".join(results)
    send_telegram_msg(final_msg)
else:
    send_telegram_msg("✅ Tarama tamamlandı: Şu an kriterlere uyan hisse bulunamadı.")
