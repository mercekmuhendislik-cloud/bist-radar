import yfinance as yf
import pandas as pd
import requests

# --- AYARLAR ---
TOKEN = "BURAYA_BOT_TOKENINI_YAZ" # Kendi tokenini buraya yapıştır
CHAT_ID = "-1003749853988" 

BIST_LIST = "ACSEL, ADEL, ADESE, AGHOL, AGESA, AGROT, AKBNK, AKCNS, AKSA, AKSEN, ALARK, ALBRK, ALFAS, ARCLK, ASELS, ASTOR, BIMAS, BRSAN, CCOLA, DOAS, EREGL, FROTO, GARAN, HEKTS, ISCTR, KCHOL, KONTR, KOZAL, MGROS, PETKM, PGSUS, SAHOL, SASA, SISE, TCELL, THYAO, TOASO, TUPRS, VAKBN, YKBNK"
stocks = [k.strip() + ".IS" for k in BIST_LIST.split(",") if k.strip()]

def calculate_t3(src, length, vf, multiplier):
    def ema(s, l): return s.ewm(span=l, adjust=False).mean()
    e1 = ema(src, length); e2 = ema(e1, length); e3 = ema(e2, length)
    e4 = ema(e3, length); e5 = ema(e4, length); e6 = ema(e5, length)
    vf3, vf2 = vf**3, vf**2
    c1, c2, c3, c4 = (-vf3, 3*vf2 + 3*vf3, -6*vf2 - 3*vf - 3*vf3, 1 + 3*vf + vf3 + 3*vf2) if multiplier == 3 else (-vf3, 4*vf2 + 4*vf3, -8*vf2 - 4*vf - 4*vf3, 1 + 4*vf + vf3 + 4*vf2)
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

def check_signal(df):
    if len(df) < 100: return False
    src = (df['High'] + df['Low'] + df['Close']) / 3
    t_siyah = calculate_t3(src, 50, 0.70, 3).iloc[-1]
    t_mor = calculate_t3(src, 87, 0.90, 4).iloc[-1]
    t_sari = calculate_t3(src, 37, 0.90, 4).iloc[-1]
    return (t_sari < t_siyah < t_mor and df['Close'].iloc[-1] > t_sari)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
    except Exception as e:
        print(f"Hata: {e}")

# --- ANALİZ ---
print("Tarama Başladı...")
h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
results = []

for t in stocks:
    try:
        df = h_data.get(t).dropna()
        if check_signal(df):
            results.append(t.replace(".IS", ""))
    except: continue

if results:
    msg = "🎯 <b>BIST RADAR SİNYAL</b>\n\n" + "\n".join([f"✅ {s}" for s in results])
else:
    msg = "🔔 Tarama yapıldı, şu an kriterlere uyan hisse bulunamadı."

send_telegram(msg)
print("İşlem Başarıyla Tamamlandı.")
