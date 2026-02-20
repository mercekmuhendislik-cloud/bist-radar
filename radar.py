import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
import os

warnings.filterwarnings('ignore')

# Gizli kasadan (Secrets) bilgileri alıyoruz
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print(f"Mesaj gönderilemedi: {e}")

# ŞİRKET LİSTESİ
bist_raw = "ACSEL, ADEL, ADESE, AGHOL, AGESA, AGROT, AHGAZ, AKBNK, AKCNS, AKSA, AKSEN, ALARK, ALBRK, ALFAS, ARCLK, ARDYZ, ASELS, ASTOR, AYDEM, BAGFS, BIMAS, BRSAN, BRYAT, CANTE, CCOLA, CIMSA, CWENE, DOAS, DOHOL, EGEEN, EKGYO, ENJSA, ENKAI, EREGL, EUHOL, EUPWR, FROTO, GARAN, GESAN, GUBRF, HALKB, HEKTS, ISCTR, ISMEN, KCAER, KCHOL, KONTR, KONYA, KORDS, KOZAA, KOZAL, KRDMD, MAVI, MIATK, MGROS, ODAS, OTKAR, OYAKC, PETKM, PGSUS, SAHOL, SASA, SISE, SKBNK, SOKM, TARKM, TAVHL, TCELL, THYAO, TKFEN, TOASO, TSKB, TTKOM, TTRAK, TUPRS, VAKBN, VESBE, VESTL, YKBNK, ZOREN" # Örnek kısaltılmış liste
selected_stocks = [k.strip() + ".IS" for k in bist_raw.split(",") if k.strip()]

def calculate_ars(src_series):
    ema1 = src_series.ewm(span=3, adjust=False).mean()
    band = 1.23 / 100
    ars_values = np.zeros(len(ema1))
    ars_values[0] = ema1.iloc[0]
    for i in range(1, len(ema1)):
        prev_out = ars_values[i-1]
        curr_ema = ema1.iloc[i]
        if (curr_ema * (1 - band)) > prev_out: ars_values[i] = curr_ema * (1 - band)
        elif (curr_ema * (1 + band)) < prev_out: ars_values[i] = curr_ema * (1 + band)
        else: ars_values[i] = prev_out
    return pd.Series(ars_values, index=src_series.index)

def calculate_t3_custom(src, length, vf, multiplier):
    def ema(s, l): return s.ewm(span=l, adjust=False).mean()
    e1 = ema(src, length); e2 = ema(e1, length); e3 = ema(e2, length)
    e4 = ema(e3, length); e5 = ema(e4, length); e6 = ema(e5, length)
    vf3, vf2 = vf**3, vf**2
    if multiplier == 3:
        c1, c2, c3, c4 = -vf3, 3*vf2 + 3*vf3, -6*vf2 - 3*vf - 3*vf3, 1 + 3*vf + vf3 + 3*vf2
    else:
        c1, c2, c3, c4 = -vf3, 4*vf2 + 4*vf3, -8*vf2 - 4*vf - 4*vf3, 1 + 4*vf + vf3 + 4*vf2
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

def check_formation(df_resampled, last_price):
    if len(df_resampled) < 100: return False
    src = (df_resampled['High'] + df_resampled['Low'] + 2 * df_resampled['Close']) / 4
    t_siyah = calculate_t3_custom(src, 50, 0.70, 3).iloc[-1]
    t_mor   = calculate_t3_custom(src, 87, 0.90, 4).iloc[-1]
    t_sari  = calculate_t3_custom(src, 37, 0.90, 4).iloc[-1]
    return (t_sari < t_siyah < t_mor and last_price > t_sari)

all_results = []
for ticker in selected_stocks:
    try:
        data = yf.download(ticker, period="1y", interval="1h", progress=False)
        if data.empty: continue
        
        last_close = float(data['Close'].iloc[-1])
        df_2s = data.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = data.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s, f2s, f4s = check_formation(data, last_close), check_formation(df_2s, last_close), check_formation(df_4s, last_close)
        
        if (f1s and f2s and f4s):
            all_results.append(f"🔥 *FULL KOMBO:* {ticker.replace('.IS','')}")
        elif (sum([f1s, f2s, f4s]) >= 2):
            all_results.append(f"⭐ *ÇİFT SİNYAL:* {ticker.replace('.IS','')}")
    except: continue

if all_results:
    msg = "🚨 *BIST RADAR RAPORU* 🚨\n\n" + "\n".join(all_results)
    send_telegram_msg(msg)
