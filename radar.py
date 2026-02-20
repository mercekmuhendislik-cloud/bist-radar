import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
import os
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings('ignore')

# --- 1. TELEGRAM AYARLARI (GitHub Secrets'dan çekilir) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True # Link önizlemelerini kapatır, kalabalığı önler
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Hata: {e}")

# --- 2. HESAPLAMA MOTORU ---
def calculate_t3(src, length, vf, multiplier):
    def ema(s, l): return s.ewm(span=l, adjust=False).mean()
    e1 = ema(src, length); e2 = ema(e1, length); e3 = ema(e2, length)
    e4 = ema(e3, length); e5 = ema(e4, length); e6 = ema(e5, length)
    vf3, vf2 = vf**3, vf**2
    c1, c2, c3, c4 = -vf3, 3*vf2 + 3*vf3, -6*vf2 - 3*vf - 3*vf3, 1 + 3*vf + vf3 + 3*vf2
    if multiplier != 3:
        c2, c3, c4 = 4*vf2 + 4*vf3, -8*vf2 - 4*vf - 4*vf3, 1 + 4*vf + vf3 + 4*vf2
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

def check_formation(df_res, last_price):
    if len(df_res) < 100: return False
    src = (df_res['High'] + df_res['Low'] + 2 * df_res['Close']) / 4
    t_siyah = calculate_t3(src, 50, 0.70, 3).iloc[-1]
    t_mor   = calculate_t3(src, 87, 0.90, 4).iloc[-1]
    t_sari  = calculate_t3(src, 37, 0.90, 4).iloc[-1]
    return (t_sari < t_siyah < t_mor and last_price > t_sari)

# --- 3. ANALİZ FONKSİYONU ---
def process_ticker(ticker, data):
    try:
        df_h = data[ticker].dropna()
        if len(df_h) < 200: return None
        
        last_close = df_h['Close'].iloc[-1]
        bb_mid_val = df_h['Close'].rolling(window=200).mean().iloc[-1]

        df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()

        f1s, f2s, f4s = check_formation(df_h, last_close), check_formation(df_2s, last_close), check_formation(df_4s, last_close)
        
        if any([f1s, f2s, f4s]):
            t_name = ticker.replace(".IS","")
            # Skor ve Emoji Belirleme
            skor = sum([f1s, f2s, f4s])
            label = "🔥 *FULL KOMBO*" if skor == 3 else ("⭐ *ÇİFT SİNYAL*" if skor == 2 else "🔹 *TEK SİNYAL*")
            bb_durum = "🟢 Üstünde" if last_close > bb_mid_val else "🔴 Altında"
            
            # TradingView Linki
            tv_link = f"[ {t_name} ](https://www.tradingview.com/chart/?symbol=BIST%3A{t_name})"
            
            return {
                "msg": f"{label}\n{tv_link} | Fiyat: {last_close:.2f}\nBB Orta 200: {bb_durum}\nSinyaller: {'1S ' if f1s else ''}{'2S ' if f2s else ''}{'4S' if f4s else ''}\n",
                "weight": (skor * 100) + (10 if last_close > bb_mid_val else 0)
            }
    except: return None

# --- 4. ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    bist_raw = "ACSEL, ADEL, ADESE, AGHOL, AGESA, AGROT, AHGAZ, AKBNK, AKCNS, AKSA, AKSEN, ALARK, ALBRK, ALFAS, ARCLK, ARDYZ, ASELS, ASTOR, AYDEM, BAGFS, BIMAS, BRSAN, BRYAT, CANTE, CCOLA, CIMSA, CWENE, DOAS, DOHOL, EGEEN, EKGYO, ENJSA, ENKAI, EREGL, EUHOL, EUPWR, FROTO, GARAN, GESAN, GUBRF, HALKB, HEKTS, ISCTR, ISMEN, KCAER, KCHOL, KONTR, KONYA, KORDS, KOZAA, KOZAL, KRDMD, MAVI, MIATK, MGROS, ODAS, OTKAR, OYAKC, PETKM, PGSUS, SAHOL, SASA, SISE, SKBNK, SOKM, TARKM, TAVHL, TCELL, THYAO, TKFEN, TOASO, TSKB, TTKOM, TTRAK, TUPRS, VAKBN, VESBE, VESTL, YKBNK, ZOREN" # ... Listeyi buraya tam haliyle yapıştır
    selected_stocks = [k.strip() + ".IS" for k in bist_raw.split(",") if k.strip()]

    print("Veriler indiriliyor...")
    full_data = yf.download(selected_stocks, period="60d", interval="1h", group_by='ticker', progress=False)

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker, t, full_data) for t in selected_stocks]
        for future in futures:
            res = future.result()
            if res: results.append(res)

    if results:
        # Ağırlığa göre sırala (En güçlüler üstte)
        results.sort(key=lambda x: x['weight'], reverse=True)
        
        final_msg = "🚀 *BIST TURBO RADAR RAPORU* 🚀\n\n"
        for item in results[:15]: # Telegram mesaj sınırı için en iyi 15 sinyali gönderir
            final_msg += item['msg'] + "------------------\n"
        
        send_telegram_msg(final_msg)
    else:
        print("Sinyal bulunamadı.")
