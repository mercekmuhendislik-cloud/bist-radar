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

# --- 1. VIP KULLANICI LİSTESİ ---
users_db = {
    "admin@mail.com": "bora2026",
    "vip01@bist.com": "vipy921", "vip02@bist.com": "vipy832", "vip03@bist.com": "vipy743",
    "vip04@bist.com": "vipy654", "vip05@bist.com": "vipy565", "vip06@bist.com": "vipy476",
    "vip07@bist.com": "vipy387", "vip08@bist.com": "vipy298", "vip09@bist.com": "vipy109",
    "vip10@bist.com": "gold2026", "vip11@bist.com": "gold2027", "user12@mail.com": "user9911",
    "user13@mail.com": "user9912", "user14@mail.com": "user9913", "user15@mail.com": "user9914",
    "user16@mail.com": "user9915", "user17@mail.com": "user9916", "user18@mail.com": "user9917",
    "user19@mail.com": "user9918", "user20@mail.com": "user9919"
}

# --- 2. AYARLAR ---
st.set_page_config(page_title="VIP BIST RADAR", page_icon="🎯", layout="wide")

# --- 3. FONKSİYONLAR ---
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
            status = "🔥 FULL KOMBO" if score == 3 else ("⭐ ÇİFT SİNYAL" if score == 2 else "TEK SİNYAL")
            return {"Hisse": ticker.replace(".IS",""), "Fiyat": round(last_close, 2), "Sinyal": status, "4S": "✅" if f4s else "-", "2S": "✅" if f2s else "-", "1S": "✅" if f1s else "-", "Score": score}
    except: return None

# --- 4. GİRİŞ KONTROLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🎯 VIP BIST RADAR")
    with st.form("login_form"):
        email = st.text_input("📧 E-Posta")
        password = st.text_input("🔑 Şifre", type="password")
        if st.form_submit_button("Sisteme Giriş Yap"):
            if email in users_db and users_db[email] == password:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Hatalı bilgiler!")
else:
    # --- 5. ANA PANEL ---
    st.sidebar.title(f"Hoş Geldin VIP")
    if st.sidebar.button("🚪 Güvenli Çıkış"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🚀 Tüm Borsa İstanbul (600+) VIP Tarama")
    
    if st.button("🔍 Tüm Hisseleri Analiz Et (Piyasa Taraması)"):
        with st.spinner('Tüm piyasa verileri çekiliyor... Bu işlem 30-45 saniye sürebilir.'):
            # TÜM BIST LİSTESİNİ ÇEKME (Sembol oluşturucu)
            # Not: Yfinance ile tüm listeyi tek seferde çekmek için sembol listesini genişlettim.
            all_stocks_url = "https://raw.githubusercontent.com/mercekmuhendislik-cloud/bist-radar/main/all_stocks.txt"
            try:
                # Kendi oluşturduğun veya genel bir listeden 600+ hisseyi buraya çekebilirsin
                # Şimdilik manuel genişletilmiş liste (Hepsini tek tek yazmak yerine yfinance query de atılabilir)
                stocks_list = ["ACSEL","ADEL","ADESE","AGHOL","AKBNK","AKSA","AKSEN","ALARK","ALBRK","ALCTL","ALGYO","ALKA","ALKIM","ANELE","ARCLK","ARENA","ARSAN","ASELS","AYGAZ","BAGFS","BAKAB","BANVT","BERA","BEYAZ","BIMAS","BIZIM","BMSCH","BNTAS","BOYP","BRISA","BRSAN","BRYAT","BSOKE","BUCIM","BURCE","BURVA","CANTE","CCOLA","CELHA","CEMAS","CEMTS","CIMSA","CLEBI","CONSE","CRDFA","DAGI","DARDL","DENGE","DERIM","DESA","DESPC","DEVA","DGATE","DGGYO","DITAS","DMSAS","DOAS","DOCO","DOGUB","DOHOL","DOKTA","DURDO","DYOBY","ECILC","ECZYT","EDATA","EGEEN","EGGUB","EGPRO","EGSER","EKGYO","EKIZ","ENJSA","ENKAI","ERBOS","EREGL","ERSU","ESCOM","ESEN","ETILR","EUREN","FLAP","FMIZP","FONET","FROTO","GARAN","GEDIK","GEDZA","GENTS","GEREL","GLBMD","GLRYH","GLYHO","GOZDE","GSDHO","GSDDE","GUHRE","GUBRF","GWIND","HALKB","HATEK","HDFGS","HEKTS","HLGYO","HTTBT","HUBVC","HUNER","IEYHO","IHEVA","IHGZT","IHLAS","IHLGM","IHMAD","INDES","INFO","INTEM","IPEKE","ISATR","ISBTR","ISCTR","ISFIN","ISGYO","ISMEN","ISSEN","ITTFH","IZFAS","IZMDC","JANTS","KAPLM","KAREL","KARSN","KARTN","KARYE","KATMR","KCHOL","KENT","KERVT","KFEIN","KGYO","KIMMR","KLGYO","KLMSN","KLRHO","KLSYN","KMPUR","KNFRT","KONTR","KORDS","KOZAA","KOZAL","KRDMA","KRDMB","KRDMD","KRONT","KRSTL","KRVGD","KSTUR","KUTPO","KUYAS","KZBGY","LIDER","LKMNH","LOGO","MAALT","MAGEN","MAKTK","MANAS","MARTI","MAVI","MEDTR","MEGAP","MEPET","METRO","METUR","MGROS","MIATK","MIPAZ","MMCAS","MNDRS","MOBTL","MPARK","MSGYO","MTRKS","MUDO","MZHLD","NETAS","NIBAS","NTGAZ","NTHOL","NUGYO","NUHCM","ODAS","ONCSM","ORCAY","ORGE","OTKAR","OYAKC","OYLUM","OYYAT","OZGYO","OZKGY","OZLGY","PAGYO","PAMEL","PAPIL","PARSN","PASEU","PENGD","PENTA","PETKM","PETUN","PGSUS","PINSU","PKART","PKENT","PNLSN","PNSUT","POLHO","POLTK","PRKAB","PRKME","PRZMA","PSDTC","QUAGR","RALYH","RAYSG","REEDR","RHEAG","RTALB","SAHOL","SAMAT","SANEL","SANFO","SANKO","SARKY","SASA","SAYAS","SEKFK","SEKUR","SELEC","SELVA","SEYKM","SILVR","SISE","SKBNK","SKTAS","SMRTGY","SNGYO","SNICA","SNKRT","SOKM","SONME","SRVGY","SUMAS","SUNTK","SURGY","SUWEN","TATGD","TAVHL","TCELL","TDGYO","TEKTU","TETMT","TGSAS","THYAO","TKFEN","TKNSA","TMPOL","TMSN","TOASO","TRCAS","TRGYO","TRILC","TSKB","TSPOR","TTKOM","TTRAK","TUCLK","TUKAS","TUPRS","TUREX","TURSG","UFUK","ULAS","ULUSE","ULUUN","UMPAS","USAK","VAKBN","VAKFN","VAKKO","VANGD","VERTU","VERUS","VESBE","VESTL","VKGYO","VKING","YAPRK","YATAS","YAYLA","YBTAS","YEOTK","YESIL","YGGYO","YGYO","YKBNK","YONGA","YUNSA","ZEDUR","ZRGYO"] # Örnek geniş liste, buraya istediğin kadar ekle
                stocks = [s + ".IS" for s in stocks_list]
                
                # Veri İndirme (Batch Mode)
                h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
                d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
                
                results = []
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(process_ticker, t, h_data[t], d_data[t]) for t in stocks if t in h_data and not h_data[t].empty]
                    for f in as_completed(futures):
                        res = f.result()
                        if res: results.append(res)
                
                if results:
                    df = pd.DataFrame(results).sort_values(by="Score", ascending=False).drop(columns=["Score"])
                    st.subheader(f"📊 Tarama Sonuçları ({len(df)} Hisse)")
                    
                    def color_sinyal(val):
                        if val == "🔥 FULL KOMBO": return 'background-color: #ff4b4b; color: white'
                        if val == "⭐ ÇİFT SİNYAL": return 'background-color: #ffa500; color: black'
                        return ''

                    st.dataframe(df.style.applymap(color_sinyal, subset=['Sinyal']), use_container_width=True)
                else:
                    st.warning("Kriterlere uygun hisse bulunamadı.")
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
