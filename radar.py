import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

# Takip listesi (Görseldeki tüm hisseler eklendi)
bist_raw = "PRZMA, AKSUE, SONME, USAK, SANFM, EYGYO, ESCAR, TDGYO, DERHL, GENTS, SELVA, ASELS, ATEKS, ATSYH, CASA, KUVVA, ALTNY, COSMO, DGATE, ECOGR, FORTE, FRIGO, FZLGY, INVES, IHAAS, IZFAS, LILAK, MANAS"
selected_stocks = [k.strip() + ".IS" for k in bist_raw.split(",")]

def calculate_t3(src, length, vf, multiplier):
    def ema(s, l): return s.ewm(span=l, adjust=False).mean()
    e1 = ema(src, length); e2 = ema(e1, length); e3 = ema(e2, length)
    e4 = ema(e3, length); e5 = ema(e4, length); e6 = ema(e5, length)
    vf3 = vf**3; vf2 = vf**2
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

def process_ticker(ticker):
    try:
        # Veri çekme hatalarını engellemek için daha sağlam çekim
        df_h = yf.download(ticker, period="60d", interval="1h", progress=False)
        df_d = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df_h.empty or df_d.empty: return None

        last_close = float(df_h['Close'].iloc[-1])
        daily_200_sma = df_d['Close'].rolling(window=200).mean().iloc[-1]
        
        f1s = check_formation(df_h, last_close)
        df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        f2s = check_formation(df_2s, last_close)
        df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        f4s = check_formation(df_4s, last_close)

        score = sum([f1s, f2s, f4s])
        
        # MANTIK: En az 1 sinyal varsa işleme al
        if score >= 1:
            t_name = ticker.replace(".IS","")
            # SMA 200 Durumu (Üstündeyse Yeşil, Altındaysa Kırmızı Daire)
            sma_icon = "🟢" if last_close > daily_200_sma else "🔴"
            
            sinyal_text = f"{'1S-' if f1s else ''}{'2S-' if f2s else ''}{'4S' if f4s else ''}".strip('-')
            
            line = (f"<b>{t_name}</b> | Fiyat: {last_close:.2f}\n"
                    f"BB Orta 200: {sma_icon} | Sinyal: {sinyal_text}")
            
            # Gruplandırma tipi
            g_type = "FULL" if score == 3 else ("CIFT" if score == 2 else "TEK")
            return {"type": g_type, "line": line}
    except: return None

# --- ÇALIŞTIRMA ---
full_kombo = []
cift_sinyal = []
tek_sinyal = []

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_ticker, t) for t in selected_stocks]
    for f in as_completed(futures):
        res = f.result()
        if res:
            if res["type"] == "FULL": full_kombo.append(res["line"])
            elif res["type"] == "CIFT": cift_sinyal.append(res["line"])
            else: tek_sinyal.append(res["line"])

# --- MESAJ OLUŞTURMA (Görsel örneğe göre düzenlendi) ---
final_msg = ""

if full_kombo:
    final_msg += "🔥 <b>FULL KOMBO (KRİTİK)</b> 🔥\n\n" + "\n\n".join(full_kombo) + "\n\n"

if cift_sinyal:
    final_msg += "⭐ <b>ÇİFT SİNYAL (TAKİP)</b> ⭐\n\n" + "\n\n".join(cift_sinyal) + "\n\n"

if tek_sinyal:
    final_msg += "🔍 <b>TEK SİNYAL</b> 🔍\n\n" + "\n\n".join(tek_sinyal) + "\n\n"

if final_msg:
    final_msg += "⚠️ <b>YASAL UYARI:</b>\n<i>Buradaki veriler indikatör bildirim sistemi olup yatırım tavsiyesi değildir.</i>"
    send_telegram_msg(final_msg)
else:
    send_telegram_msg("✅ Tarama yapıldı, kriterlere uyan yeni sinyal bulunamadı.")
