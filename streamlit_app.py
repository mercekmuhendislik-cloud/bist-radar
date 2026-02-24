import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VIP BIST Radar", layout="wide")

# --- TELEGRAM FONKSİYONU ---
def send_telegram_msg(message):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=HTML"
        requests.get(url)
    except:
        pass

# --- GİRİŞ PANELİ ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 VIP BIST Radar Giriş")
    email = st.text_input("E-posta")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if email in st.secrets["users"] and st.secrets["users"][email] == password:
            st.session_state["auth"] = True
            send_telegram_msg(f"✅ <b>{email}</b> sisteme giriş yaptı.")
            st.rerun()
        else:
            st.error("Hatalı kullanıcı bilgisi!")
    st.stop() # Giriş yapılmadıysa kodun geri kalanını çalıştırma

# --- BURADAN SONRASI SENİN ALGORİTMAN (Giriş Başarılıysa Çalışır) ---

# T3 Hesaplama Motoru (Senin fonksiyonun)
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
        last_close = df_h['Close'].iloc[-1]
        daily_200_sma = df_d['Close'].rolling(window=200).mean().iloc[-1]
        df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s = check_formation(df_h, last_close)
        f2s = check_formation(df_2s, last_close)
        f4s = check_formation(df_4s, last_close)

        if any([f1s, f2s, f4s]):
            score = sum([f1s, f2s, f4s])
            if score < 2 and last_close <= daily_200_sma: return None
            
            t_name = ticker.replace(".IS","")
            return {
                "Hisse": t_name, "Kapanış": round(last_close, 2),
                "Sinyal": "🔥 FULL" if score==3 else ("⭐ ÇİFT" if score==2 else "TEK"),
                "SMA200": round(daily_200_sma, 2), "4S": f4s, "2S": f2s, "1S": f1s,
                "weight": (score * 1000) + (int(f4s)*100) + (int(f2s)*10) + (int(f1s))
            }
    except: return None

# --- UI ARAYÜZÜ ---
st.title("🎯 BIST VIP Radar Tarama")
if st.button("Taramayı Başlat"):
    # Hisse listesini burada bist_raw'dan çekebilirsin (Senin listen çok uzun olduğu için kısalttım, orayı yapıştır)
    bist_raw = "ACSEL, ADEL, AGHOL, AKBNK, ASELS, THYAO, TUPRS, EREGL" # Buraya tüm listeni koy
    stocks = [k.strip() + ".IS" for k in bist_raw.split(",") if k.strip()]
    
    with st.spinner("Veriler analiz ediliyor..."):
        h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
        d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
        
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_ticker, t, h_data.get(t), d_data.get(t)) for t in stocks]
            for f in as_completed(futures):
                res = f.result()
                if res: results.append(res)
        
        if results:
            df = pd.DataFrame(results).sort_values("weight", ascending=False)
            st.dataframe(df.drop(columns=["weight"]))
            
            # Bulunan hisseleri kanala özet olarak at
            found_list = ", ".join([r["Hisse"] for r in results[:5]])
            send_telegram_msg(f"🚀 Tarama Tamamlandı!\nÖne Çıkanlar: {found_list}")
        else:
            st.warning("Uygun hisse bulunamadı.")
