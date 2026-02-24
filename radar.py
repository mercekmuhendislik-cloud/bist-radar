import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="VIP BIST RADAR", page_icon="🎯", layout="wide")

# --- 2. KULLANICI VERİTABANI (Burayı istediğin gibi çoğalt) ---
users_db = {
    "admin@mail.com": "12345",
    "bora@mail.com": "bora2026",
    "vip@mail.com": "vip2026"
}

# BIST 50 Listesi (Etiketleme için)
BIST50 = ["AKBNK", "AKSEN", "ALARK", "ARCLK", "ASELS", "ASTOR", "BIMAS", "BRSAN", "DOAS", "DOHOL", "EKGYO", "ENJSA", "ENKAI", "EREGL", "FROTO", "GARAN", "GUBRF", "HALKB", "HEKTS", "ISCTR", "KCHOL", "KONTR", "KOZAA", "KOZAL", "KRDMD", "MGROS", "ODAS", "OYAKC", "PETKM", "PGSUS", "SAHOL", "SASA", "SISE", "SKBNK", "SOKM", "TAVHL", "TCELL", "THYAO", "TOASO", "TSKB", "TTKOM", "TTRAK", "TUPRS", "VAKBN", "VESTL", "YKBNK"]

# --- 3. HESAPLAMA FONKSİYONLARI ---
def calculate_t3(src, length, vf, multiplier):
    # pandas_ta kullanarak T3 hesaplama
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

# --- 4. ANALİZ MOTORU ---
def process_ticker(ticker, h_df, d_df):
    try:
        last_close = h_df['Close'].iloc[-1]
        daily_200_sma = d_df['Close'].rolling(window=200).mean().iloc[-1]
        
        # Resampling
        df_2s = h_df.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = h_df.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s = check_formation(h_df, last_close)
        f2s = check_formation(df_2s, last_close)
        f4s = check_formation(df_4s, last_close)

        if any([f1s, f2s, f4s]):
            score = sum([f1s, f2s, f4s])
            # Tek sinyal ise SMA 200 üstü şartı, çift/full ise serbest
            if score < 2 and last_close <= daily_200_sma: return None
            
            t_name = ticker.replace(".IS","")
            label = " 🔥B50" if t_name in BIST50 else ""
            status = "🔥 FULL KOMBO" if score == 3 else ("⭐ ÇİFT SİNYAL" if score == 2 else "TEK SİNYAL")
            weight = (score * 1000) + (int(f4s)*100) + (int(f2s)*10) + (int(f1s)*1)
            
            return {
                "Hisse": f"{t_name}{label}",
                "Fiyat": round(last_close, 2),
                "Sinyal": status,
                "Günlük 200 SMA": round(daily_200_sma, 2),
                "4S Sinyal": "✅ POZİTİF" if f4s else "-",
                "2S Sinyal": "✅ POZİTİF" if f2s else "-",
                "1S Sinyal": "✅ POZİTİF" if f1s else "-",
                "Weight": weight
            }
    except: return None

# --- 5. STREAMLIT ARAYÜZÜ ---
st.title("🎯 BIST VIP Teknik Radar")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Giriş Ekranı
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🔐 Üye Girişi")
            email_input = st.text_input("📧 E-Posta")
            pass_input = st.text_input("🔑 Şifre", type="password")
            if st.button("Giriş Yap"):
                if email_input in users_db and users_db[email_input] == pass_input:
                    st.session_state.logged_in = True
                    st.success("Giriş Başarılı! Sayfa yükleniyor...")
                    st.rerun()
                else:
                    st.error("Hatalı Mail veya Şifre!")
else:
    # VIP Panel İçeriği
    st.sidebar.success(f"Hoş geldin VIP Üye")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.logged_in = False
        st.rerun()

    if st.button("🚀 Piyasayı Tara (Taramayı Başlat)"):
        with st.spinner('BIST Verileri Analiz Ediliyor...'):
            bist_raw = "ACSEL, ADEL, ADESE, AGHOL, AKBNK, AKSA, AKSEN, ALARK, ARCLK, ASELS, ASTOR, BIMAS, BRSAN, DOAS, DOHOL, EKGYO, ENJSA, ENKAI, EREGL, FROTO, GARAN, GUBRF, HALKB, HEKTS, ISCTR, KCHOL, KONTR, KOZAA, KOZAL, KRDMD, MGROS, ODAS, OYAKC, PETKM, PGSUS, SAHOL, SASA, SISE, SKBNK, SOKM, TAVHL, TCELL, THYAO, TOASO, TSKB, TTKOM, TTRAK, TUPRS, VAKBN, VESTL, YKBNK"
            stocks = [s.strip() + ".IS" for s in bist_raw.split(",")]
            
            # Veri Çekme
            h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
            d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
            
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(process_ticker, t, h_data[t], d_data[t]) for t in stocks if t in h_data]
                for f in as_completed(futures):
                    res = f.result()
                    if res: results.append(res)
            
            if results:
                df = pd.DataFrame(results).sort_values(by="Weight", ascending=False).drop(columns=["Weight"])
                
                # Tabloyu Renklendirme ve Gösterme
                st.subheader("📊 VIP Tarama Sonuçları")
                
                def color_rows(val):
                    if val == "🔥 FULL KOMBO": return 'background-color: #FF4500; color: white'
                    if val == "⭐ ÇİFT SİNYAL": return 'background-color: #FFD700; color: black'
                    return ''

                st.dataframe(df.style.applymap(color_rows, subset=['Sinyal']), use_container_width=True)
                st.info("💡 Not: TradingView linkleri için hisse koduna tıklayabilirsiniz (Geliştirme aşamasında).")
                st.caption("⚠️ YASAL UYARI: Bu veriler otomatik indikatör sonuçlarıdır, yatırım tavsiyesi değildir.")
            else:
                st.warning("Şu an kriterlere uygun hisse bulunamadı.")
