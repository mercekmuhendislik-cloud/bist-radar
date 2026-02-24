import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VIP BIST RADAR", page_icon="🎯", layout="wide")

# --- ŞİFRE KONTROLÜ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.title("🔒 VIP Giriş")
            # Giriş için hem e-posta hem şifre alanı (Görseldeki gibi)
            st.text_input("E-Posta") 
            pwd = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap"):
                if pwd == "12345": # Şifreni buradan değiştirebilirsin
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı Şifre!")
        return False
    return True

# --- HESAPLAMA MOTORU ---
def calculate_t3(src, length, vf, multiplier):
    def ema(s, l): return s.ewm(span=l, adjust=False).mean()
    e1 = ema(src, length); e2 = ema(e1, length); e3 = ema(e2, length)
    e4 = ema(e3, length); e5 = ema(e4, length); e6 = ema(e5, length)
    vf3, vf2 = vf**3, vf**2
    c1, c2, c3, c4 = (-vf3, 3*vf2 + 3*vf3, -6*vf2 - 3*vf - 3*vf3, 1 + 3*vf + vf3 + 3*vf2) if multiplier == 3 else (-vf3, 4*vf2 + 4*vf3, -8*vf2 - 4*vf - 4*vf3, 1 + 4*vf + vf3 + 4*vf2)
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

def check_formation(df, last_price):
    if len(df) < 100: return False
    src = (df['High'] + df['Low'] + df['Close']) / 3
    t_siyah = calculate_t3(src, 50, 0.70, 3).iloc[-1]
    t_mor = calculate_t3(src, 87, 0.90, 4).iloc[-1]
    t_sari = calculate_t3(src, 37, 0.90, 4).iloc[-1]
    return (t_sari < t_siyah < t_mor and last_price > t_sari)

# --- ANA EKRAN ---
if check_password():
    st.sidebar.title("Menü")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state["password_correct"] = False
        st.rerun()

    st.markdown("# 🎯 VIP BIST RADAR TERMINAL")
    
    if st.button("🔍 Tüm Hisseleri Analiz Et (Piyasa Taraması)"):
        BIST_RAW = "ACSEL, ADEL, ADESE, AGHOL, AGESA, AGROT, AKBNK, AKCNS, AKSA, AKSEN, ALARK, ALBRK, ALFAS, ARCLK, ASELS, ASTOR, BIMAS, BRSAN, CCOLA, DOAS, EREGL, FROTO, GARAN, HEKTS, ISCTR, KCHOL, KONTR, KOZAL, MGROS, PETKM, PGSUS, SAHOL, SASA, SISE, TCELL, THYAO, TOASO, TUPRS, VAKBN, YKBNK"
        stocks = [k.strip() + ".IS" for k in BIST_RAW.split(",") if k.strip()]
        
        with st.spinner('Piyasa taranıyor, lütfen bekleyin...'):
            h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
            d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
            
            results = []
            for t in stocks:
                try:
                    df_h = h_data.get(t).dropna()
                    df_d = d_data.get(t).dropna()
                    last_close = df_h['Close'].iloc[-1]
                    sma200 = df_d['Close'].rolling(window=200).mean().iloc[-1]
                    
                    # Resample işlemleri
                    df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
                    df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
                    
                    f1s = check_formation(df_h, last_close)
                    f2s = check_formation(df_2s, last_close)
                    f4s = check_formation(df_4s, last_close)
                    
                    score = sum([f1s, f2s, f4s])
                    if score >= 1:
                        if score < 2 and last_close <= sma200: continue
                        
                        status = "🔥 FULL KOMBO" if score == 3 else ("⭐ ÇİFT SİNYAL" if score == 2 else "TEK SİNYAL")
                        results.append({
                            "Hisse": t.replace(".IS",""),
                            "Fiyat": round(last_close, 2),
                            "Sinyal": status,
                            "SMA 200": round(sma200, 2),
                            "4S": "✅" if f4s else "-",
                            "2S": "✅" if f2s else "-",
                            "1S": "✅" if f1s else "-",
                            "Score": score
                        })
                except: continue
        
        if results:
            df_res = pd.DataFrame(results).sort_values(by="Score", ascending=False)
            
            # TradingView linki ekleme
            df_res['Grafik'] = df_res['Hisse'].apply(lambda x: f"https://www.tradingview.com/chart/?symbol=BIST%3A{x}")
            
            st.dataframe(
                df_res.drop(columns=['Score']), 
                column_config={"Grafik": st.column_config.LinkColumn("Grafiği Aç")},
                use_container_width=True
            )
            st.success(f"Tarama tamamlandı. {len(results)} potansiyel fırsat bulundu.")
        else:
            st.warning("Kriterlere uyan hisse bulunamadı.")
