import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# --- 1. AYARLAR ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

def process_ticker(ticker, df_h, df_d):
    try:
        if df_h is None or df_h.empty or df_d is None or df_d.empty: return None
        last_close = df_h['Close'].iloc[-1]
        daily_200_sma = df_d['Close'].rolling(window=200).mean().iloc[-1]
        df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s = check_formation(df_h, last_close); f2s = check_formation(df_2s, last_close); f4s = check_formation(df_4s, last_close)

        if any([f1s, f2s, f4s]):
            score = sum([f1s, f2s, f4s])
            if score < 2 and last_close <= daily_200_sma: return None
            status = "🔥 FULL KOMBO" if score == 3 else ("⭐ ÇİFT SİNYAL" if score == 2 else "TEK SİNYAL")
            return {"Hisse": ticker.replace(".IS",""), "Kapanış": round(last_close, 2), "Sinyal": status, "Score": score}
    except: return None
    return None

def run_scan():
    bist_list = "ACSEL, ADEL, ADESE, AGHOL, AGROT, AKBNK, AKSA, ASELS, ASTOR, BIMAS, BRSAN, DOAS, EREGL, FROTO, GARAN, HEKTS, ISCTR, KCHOL, KONTR, MIATK, REEDR, SASA, SISE, TCELL, THYAO, TUPRS, YKBNK" # Listeyi buraya ekle
    stocks = [k.strip() + ".IS" for k in bist_list.split(",") if k.strip()]
    h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
    d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker, t, h_data.get(t), d_data.get(t)) for t in stocks]
        for f in as_completed(futures):
            res = f.result()
            if res: results.append(res)
    return results

# --- 3. OTOMASYON MU? ARAYÜZ MÜ? AYRIMI ---
if __name__ == "__main__":
    # Eğer GitHub Actions (Otomatik Mesaj) çalışıyorsa
    if os.getenv("GITHUB_ACTIONS") == "true":
        results = run_scan()
        if results and TOKEN and CHAT_ID:
            msg = "🚀 *VIP OTOMATİK TARAMA TAMAMLANDI*\n\n" + "\n".join([f"✅ {r['Hisse']} ({r['Sinyal']})" for r in results])
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    
    # Eğer Web Arayüzü (Streamlit) çalışıyorsa
    else:
        st.set_page_config(page_title="VIP BIST RADAR", page_icon="🎯", layout="wide")
        # Senin mevcut Giriş Paneli kodlarını buraya ekleyebilirsin...
        st.title("🎯 VIP BIST RADAR TERMINAL")
        if st.button("🔍 TARAMAYI BAŞLAT"):
            res = run_scan()
            st.write(pd.DataFrame(res))
