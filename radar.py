import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import requests
import os
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# --- 1. AYARLAR (Telegram & Sayfa) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

st.set_page_config(page_title="VIP BIST RADAR", layout="wide")

# --- 2. KULLANICI LİSTESİ ---
users_db = {"admin@mail.com": "12345", "bora@mail.com": "bora2026"}

# --- 3. FONKSİYONLAR ---
def send_telegram_msg(message):
    if not TOKEN or not CHAT_ID: return # Token yoksa hata verme, geç
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def calculate_t3(src, length, vf, multiplier):
    ema1 = ta.ema(src, length=length)
    ema2 = ta.ema(ema1, length=length)
    ema3 = ta.ema(ema2, length=length)
    ema4 = ta.ema(ema3, length=length)
    ema5 = ta.ema(ema4, length=length)
    ema6 = ta.ema(ema5, length=length)
    vf3, vf2 = vf**3, vf**2
    if multiplier == 3:
        c1, c2, c3, c4 = -vf3, 3*vf2 + 3*vf3, -6*vf2 - 3*vf - 3*vf3, 1 + 3*vf + vf3 + 3*vf2
    else:
        c1, c2, c3, c4 = -vf3, 4*vf2 + 4*vf3, -8*vf2 - 4*vf - 4*vf3, 1 + 4*vf + vf3 + 4*vf2
    return c1 * ema6 + c2 * ema5 + c3 * ema4 + c4 * ema3

def check_formation(df, last_price):
    if len(df) < 100: return False
    src = (df['High'] + df['Low'] + df['Close']) / 3
    t_siyah = calculate_t3(src, 50, 0.70, 3).iloc[-1]
    t_mor   = calculate_t3(src, 87, 0.90, 4).iloc[-1]
    t_sari  = calculate_t3(src, 37, 0.90, 4).iloc[-1]
    return (t_sari < t_siyah < t_mor and last_price > t_sari)

def process_ticker(ticker, h_df, d_df):
    try:
        last_close = h_df['Close'].iloc[-1]
        daily_200_sma = d_df['Close'].rolling(window=200).mean().iloc[-1]
        df_2s = h_df.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = h_df.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s = check_formation(h_df, last_close)
        f2s = check_formation(df_2s, last_close)
        f4s = check_formation(df_4s, last_close)

        if any([f1s, f2s, f4s]):
            score = sum([f1s, f2s, f4s])
            if score < 2 and last_close <= daily_200_sma: return None
            status = "🔥 FULL" if score == 3 else "⭐ ÇİFT" if score == 2 else "TEK"
            return {"Hisse": ticker.replace(".IS",""), "Fiyat": round(last_close, 2), "Sinyal": status, "4S": f4s, "2S": f2s, "1S": f1s}
    except: return None

# --- 4. STREAMLIT ARAYÜZÜ ---
st.title("🎯 VIP BIST RADAR")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    email = st.text_input("E-Posta")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if email in users_db and users_db[email] == password:
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("Hatalı!")
else:
    if st.button("🚀 TARAMAYI BAŞLAT"):
        with st.spinner('Veriler çekiliyor...'):
            bist_raw = "ACSEL, ADEL, ADESE, AGHOL, AKBNK, AKSA, AKSEN, ALARK, ARCLK, ASELS, ASTOR, BIMAS, BRSAN, DOAS, DOHOL, EKGYO, ENJSA, ENKAI, EREGL, FROTO, GARAN, GUBRF, HALKB, HEKTS, ISCTR, KCHOL, KONTR, KOZAA, KOZAL, KRDMD, MGROS, ODAS, OYAKC, PETKM, PGSUS, SAHOL, SASA, SISE, SKBNK, SOKM, TAVHL, TCELL, THYAO, TOASO, TSKB, TTKOM, TTRAK, TUPRS, VAKBN, VESTL, YKBNK"
            stocks = [s.strip() + ".IS" for s in bist_raw.split(",")]
            h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
            d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
            
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(process_ticker, t, h_data[t], d_data[t]) for t in stocks if t in h_data]
                for f in as_completed(futures):
                    res = f.result(); 
                    if res: results.append(res)
            
            if results:
                df = pd.DataFrame(results)
                st.table(df)
                send_telegram_msg(f"✅ VIP Tarama Tamamlandı! {len(results)} sinyal bulundu.")
            else: st.warning("Sinyal yok.")
