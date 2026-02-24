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

# --- 1. VIP KULLANICI VERİTABANI ---
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
st.set_page_config(page_title="VIP BIST RADAR TERMINAL", page_icon="🎯", layout="wide")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- 3. HESAPLAMA MOTORU (Colab ile Birebir) ---
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

        f1s = check_formation(df_h, last_close)
        f2s = check_formation(df_2s, last_close)
        f4s = check_formation(df_4s, last_close)

        if any([f1s, f2s, f4s]):
            score = sum([f1s, f2s, f4s])
            if score < 2 and last_close <= daily_200_sma: return None
            
            status = "🔥 FULL KOMBO" if score == 3 else ("⭐ ÇİFT SİNYAL" if score == 2 else "TEK SİNYAL")
            t_name = ticker.replace(".IS","")
            # TradingView Linki (Streamlit uyumlu)
            tv_link = f"https://www.tradingview.com/chart/?symbol=BIST%3A{t_name}"
            
            return {
                "Hisse": t_name,
                "Link": tv_link,
                "Kapanış": round(last_close, 2),
                "KOMBO SİNYAL": status,
                "Günlük 200 SMA": round(daily_200_sma, 2),
                "4S (T3)": "POZİTİF" if f4s else "-",
                "2S (T3)": "POZİTİF" if f2s else "-",
                "1S (T3)": "POZİTİF" if f1s else "-",
                "Weight": (score * 1000) + (int(f4s)*100) + (int(f2s)*10) + (int(f1s)*1)
            }
    except: return None

# --- 4. GİRİŞ KONTROLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛡️ BIST VIP RADAR LOGIN")
    with st.form("login"):
        user_mail = st.text_input("E-Posta")
        user_pass = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
            if user_mail in users_db and users_db[user_mail] == user_pass:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Yetkisiz Giriş!")
else:
    # --- 5. ANA EKRAN ---
    st.sidebar.title(f"VIP PANEL")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🎯 VIP BIST Radar (612 Hisse)")
    
    if st.button("🔍 TÜM PİYASAYI TARA (COLAB GÜCÜNDE)"):
        with st.spinner('Tüm Borsa İstanbul verileri indiriliyor... (Yaklaşık 45 saniye)'):
            bist_raw = "ACSEL, ADEL, ADESE, ADLVY, ADGYO, AFYON, AGHOL, AGESA, AGROT, AHSGY, AHGAZ, AKSFA, AKFK, AKMEN, AKCVR, AKBNK, AKCKM, AKCNS, AKDFA, AKYHO, AKENR, AKFGY, AKFIS, AKFYE, ATEKS, AKSGY, AKMGY, AKSA, AKSEN, AKGRT, AKSUE, AKTVK, ALCAR, ALGYO, ALARK, ALBRK, ALCTL, ALFAS, ALKIM, ALKA, AYCES, ALTNY, ALKLC, ALVES, ANSGR, AEFES, ANHYT, ASUZU, ANGEN, ANELE, ARCLK, ARDYZ, ARENA, ARFYE, ARMGD, ARSAN, ARSVY, ARTMS, ARZUM, ASGYO, ASELS, ASTOR, ATAGY, ATAVK, ATAKP, AGYO, ATLFA, ATSYH, ATLAS, ATATP, AVOD, AVGYO, AVTUR, AVHOL, AVPGY, AYDEM, AYEN, AYES, AYGAZ, AZTEK, BAGFS, BAHKM, BAKAB, BALAT, BALSU, BNTAS, BANVT, BARMA, BSRFK, BASGZ, BASCM, BEGYO, BTCIM, BSOKE, BYDNR, BAYRK, BERA, BRKT, BRKSN, BESLR, BJKAS, BEYAZ, BIENY, BIGTK, BLCYT, BLKOM, BIMAS, BINBN, BIOEN, BRKVY, BRKO, BIGEN, BRLSM, BRMEN, BIZIM, BLUME, BMSTL, BMSCH, BOBET, BORSK, BORLS, BRSAN, BRYAT, BFREN, BOSSA, BRISA, BULGS, BURCE, BURVA, BUCIM, BVSAN, BIGCH, CRFSA, CASA, CEMZY, CEOEM, CCOLA, CONSE, COSMO, CRDFA, CVKMD, CWENE, CGCAM, CAGFA, CMSAN, CANTE, CATES, CLEBI, CELHA, CLKMT, CEMAS, CEMTS, CMBTN, CMENT, CIMSA, CUSAN, DAGI, DAPGM, DARDL, DGATE, DCTTR, DGRVK, DMSAS, DENGE, DZGYO, DERIM, DERHL, DESA, DESPC, DEVA, DNISI, DIRIT, DITAS, DKVRL, DMRGD, DOCO, DOFER, DOHOL, DTRND, DGNMO, DOGVY, ARASE, DOGUB, DGGYO, DOAS, DOKTA, DURDO, DURKN, DUNYH, DNYVA, DYOBY, EBEBK, ECOGR, ECZYT, EDATA, EDIP, EFOR, EGEEN, EGGUB, EGPRO, EGSER, EPLAS, EGEGY, ECILC, EKER, EKIZ, EKOFA, EKOS, EKOVR, EKSUN, ELITE, EMKEL, EMNIS, EMIRV, EKGYO, EMVAR, ENJSA, ENERY, ENKAI, ENSRI, ERBOS, ERCB, EREGL, KIMMR, ERSU, ESCAR, ESCOM, ESEN, ETILR, EUKYO, EUYO, ETYAT, EUHOL, TEZOL, EUREN, EUPWR, EYGYO, FADE, FAIRF, FMIZP, FENER, FLAP, FONET, FROTO, FORMT, FRMPL, FORTE, FRIGO, FZLGY, GWIND, GSRAY, GARFA, GARFL, GRNYO, SNKRN, GEDIK, GEDZA, GLCVY, GENIL, GENTS, GEREL, GZNMI, GIPTA, GMTAS, GESAN, GLYHO, GOODY, GOKNR, GOLTS, GOZDE, GRTHO, GSDDE, GSDHO, GUBRF, GLRYH, GLRMK, GUNDG, GRSEL, SAHOL, HALKF, HLGYO, HLVKS, HRKET, HATEK, HATSN, HDFFL, HDFGS, HEDEF, HEKTS, HKTM, HTTBT, HOROZ, HUBVC, HUNER, HUZFA, HURGZ, ENTRA, ICBCT, ICUGS, INGRM, INVEO, INVES, ISKPL, IEYHO, IDGYO, IHEVA, IHLGM, IHGZT, IHAAS, IHLAS, IHYAY, IMASM, INALR, INDES, INFO, INTEK, INTEM, ISDMR, ISFAK, ISFIN, ISGYO, ISGSY, ISMEN, ISYAT, ISBIR, ISSEN, IZINV, IZENR, IZMDC, IZFAS, JANTS, KFEIN, KLKIM, KLSER, KAPLM, KRDMA, KRDMB, KRDMD, KAREL, KARSN, KRTEK, KARTN, KTLEV, KATMR, KAYSE, KENT, KRVGD, KERVN, KZBGY, KLGYO, KLRHO, KMPUR, KLMSN, KCAER, KCHOL, KOCMT, KLSYN, KNFRT, KONTR, KONYA, KONKA, KGYO, KORDS, KRPLS, KORTS, KOTON, KOPOL, KRGYO, KRSTL, KRONT, KSTUR, KUVVA, KUYAS, KBORU, KZGYO, KUTPO, KTSKR, LIDER, LIDFA, LILAK, LMKDC, LINK, LOGO, LKMNH, LRSHO, LUKSK, LYDHO, LYDYE, MACKO, MAKIM, MAKTK, MANAS, MAGEN, MARKA, MAALT, MRSHL, MRGYO, MARTI, MTRKS, MAVI, MZHLD, MEDTR, MEGMT, MEGAP, MEKAG, MNDRS, MEPET, MERCN, MERIT, MERKO, METRO, MTRYO, MEYSU, MHRGY, MIATK, MGROS, MSGYO, MPARK, MMCAS, MOBTL, MOGAN, MNDTR, MOPAS, EGEPO, NATEN, NTGAZ, NTHOL, NETAS, NIBAS, NUHCM, NUGYO, OBAMS, OBASE, ODAS, ODINE, OFSYM, ONCSM, ONRYT, ORCAY, ORGE, ORMA, OSMEN, OSTIM, OTKAR, OTTO, OYAKC, OYAYO, OYLUM, OZKGY, OZATD, OZGYO, OZRDN, OZSUB, OZYSR, PAMEL, PNLSN, PAGYO, PAPIL, PRFFK, PRDGS, PRKME, PARSN, PASEU, PSGYO, PAHOL, PATEK, PCILT, PGSUS, PEKGY, PENGD, PENTA, PSDTC, PETKM, PKENT, PETUN, PINSU, PNSUT, PKART, PLTUR, POLHO, POLTK, PRZMA, QFINF, QUAGR, RNPOL, RALYH, RAYSG, REEDR, RYGYO, RYSAS, RODRG, ROYAL, RGYAS, RTALB, RUBNS, SAFKR, SANEL, SNICA, SANFM, SANKO, SAMAT, SARKY, SARTN, SASA, SAYAS, SDTTR, SEGMN, SEKUR, SELEC, SELVA, SERNT, SRVGY, SEYKM, SILVR, SNGYO, SMRTG, SMART, SODSN, SOKE, SKTAS, SONME, SNPAM, SUMAS, SUNTK, SURGY, SUWEN, SEKFK, SEGYO, SKBNK, SOKM, TABGD, TNZTP, TARKM, TATGD, TATEN, TAVHL, TEKTU, TKFEN, TKNSA, TMPOL, TRHOL, TGSAS, TOASO, TRGYO, TRMET, TLMAN, TSPOR, TDGYO, TSGYO, TUCLK, TUKAS, TRCAS, TUREX, MARBL, TRILC, TCELL, TRKNT, TMSN, TUPRS, THYAO, PRKAB, TTKOM, TTRAK, TBORG, TURGG, GARAN, HALKB, ISCTR, TSKB, TURSG, SISE, VAKBN, UFUK, ULAS, ULUFA, ULUSE, ULUUN, USAK, ULKER, UNLU, VAKFN, VKGYO, VKFYO, VAKKO, VANGD, VBTYZ, VRGYO, VERUS, VERTU, VESBE, VESTL, VKING, YKBNK, YAPRK, YATAS, YYLGD, YAYLA, YGGYO, YEOTK, YGYO, YYAPI, YESIL, YBTAS, YIGIT, YONGA, YKSLN, YUNSA, ZGYO, ZEDUR, ZRGYO, ZOREN, BINHO"
            stocks = [k.strip() + ".IS" for k in bist_raw.split(",") if k.strip()]
            
            h_data = yf.download(stocks, period="60d", interval="1h", group_by='ticker', progress=False)
            d_data = yf.download(stocks, period="2y", interval="1d", group_by='ticker', progress=False)
            
            results = []
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = [executor.submit(process_ticker, t, h_data.get(t), d_data.get(t)) for t in stocks]
                for f in as_completed(futures):
                    res = f.result()
                    if res: results.append(res)
            
            if results:
                df_res = pd.DataFrame(results).sort_values(by="Weight", ascending=False).drop(columns=["Weight"])
                
                # --- RENKLENDİRME FONKSİYONU (Colab Stili) ---
                def style_table(row):
                    styles = [''] * len(row)
                    # Kombo Sinyal Renkleri
                    if row['KOMBO SİNYAL'] == "🔥 FULL KOMBO": styles[3] = 'background-color: #FF4500; color: white; font-weight: bold'
                    elif row['KOMBO SİNYAL'] == "⭐ ÇİFT SİNYAL": styles[3] = 'background-color: #FFD700; color: black; font-weight: bold'
                    # SMA 200 Renkleri
                    if row['Kapanış'] > row['Günlük 200 SMA']: styles[4] = 'background-color: #C6EFCE; color: #006100'
                    else: styles[4] = 'background-color: #FFC7CE; color: #9C0006'
                    # T3 Pozitif Renkleri
                    for i in [5, 6, 7]:
                        if row.iloc[i] == "POZİTİF": styles[i] = 'background-color: #00008B; color: white; font-weight: bold'
                    return styles

                # Link Kolonunu Tıklanabilir Yap
                st.write("### 🎯 Tarama Sonuçları")
                st.dataframe(
                    df_res.style.apply(style_table, axis=1),
                    column_config={
                        "Link": st.column_config.LinkColumn("Grafik", display_text="Grafiği Aç")
                    },
                    use_container_width=True,
                    height=600
                )
                
                # Telegram Bildirimi (Opsiyonel)
                if TOKEN and CHAT_ID:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": CHAT_ID, "text": f"✅ VIP Web Tarama Tamamlandı! {len(results)} sinyal bulundu."})
            else:
                st.warning("❌ Kriterlere uyan hisse bulunamadı.")
