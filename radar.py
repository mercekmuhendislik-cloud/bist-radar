import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# --- AYARLAR ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# --- TÜM HİSSE LİSTESİ ---
bist_raw = "ACSEL, ADEL, ADESE, ADLVY, ADGYO, AFYON, AGHOL, AGESA, AGROT, AHSGY, AHGAZ, AKSFA, AKFK, AKMEN, AKCVR, AKBNK, AKCKM, AKCNS, AKDFA, AKYHO, AKENR, AKFGY, AKFIS, AKFYE, ATEKS, AKSGY, AKMGY, AKSA, AKSEN, AKGRT, AKSUE, AKTVK, ALCAR, ALGYO, ALARK, ALBRK, ALCTL, ALFAS, ALKIM, ALKA, AYCES, ALTNY, ALKLC, ALVES, ANSGR, AEFES, ANHYT, ASUZU, ANGEN, ANELE, ARCLK, ARDYZ, ARENA, ARFYE, ARMGD, ARSAN, ARSVY, ARTMS, ARZUM, ASGYO, ASELS, ASTOR, ATAGY, ATAVK, ATAKP, AGYO, ATLFA, ATSYH, ATLAS, ATATP, AVOD, AVGYO, AVTUR, AVHOL, AVPGY, AYDEM, AYEN, AYES, AYGAZ, AZTEK, BAGFS, BAHKM, BAKAB, BALAT, BALSU, BNTAS, BANVT, BARMA, BSRFK, BASGZ, BASCM, BEGYO, BTCIM, BSOKE, BYDNR, BAYRK, BERA, BRKT, BRKSN, BESLR, BJKAS, BEYAZ, BIENY, BIGTK, BLCYT, BLKOM, BIMAS, BINBN, BIOEN, BRKVY, BRKO, BIGEN, BRLSM, BRMEN, BIZIM, BLUME, BMSTL, BMSCH, BOBET, BORSK, BORLS, BRSAN, BRYAT, BFREN, BOSSA, BRISA, BULGS, BURCE, BURVA, BUCIM, BVSAN, BIGCH, CRFSA, CASA, CEMZY, CEOEM, CCOLA, CONSE, COSMO, CRDFA, CVKMD, CWENE, CGCAM, CAGFA, CMSAN, CANTE, CATES, CLEBI, CELHA, CLKMT, CEMAS, CEMTS, CMBTN, CMENT, CIMSA, CUSAN, DAGI, DAPGM, DARDL, DGATE, DCTTR, DGRVK, DMSAS, DENGE, DZGYO, DERIM, DERHL, DESA, DESPC, DEVA, DNISI, DIRIT, DITAS, DKVRL, DMRGD, DOCO, DOFER, DOHOL, DTRND, DGNMO, DOGVY, ARASE, DOGUB, DGGYO, DOAS, DOKTA, DURDO, DURKN, DUNYH, DNYVA, DYOBY, EBEBK, ECOGR, ECZYT, EDATA, EDIP, EFOR, EGEEN, EGGUB, EGPRO, EGSER, EPLAS, EGEGY, ECILC, EKER, EKIZ, EKOFA, EKOS, EKOVR, EKSUN, ELITE, EMKEL, EMNIS, EMIRV, EKGYO, EMVAR, ENJSA, ENERY, ENKAI, ENSRI, ERBOS, ERCB, EREGL, KIMMR, ERSU, ESCAR, ESCOM, ESEN, ETILR, EUKYO, EUYO, ETYAT, EUHOL, TEZOL, EUREN, EUPWR, EYGYO, FADE, FAIRF, FMIZP, FENER, FLAP, FONET, FROTO, FORMT, FRMPL, FORTE, FRIGO, FZLGY, GWIND, GSRAY, GARFA, GARFL, GRNYO, SNKRN, GEDIK, GEDZA, GLCVY, GENIL, GENTS, GEREL, GZNMI, GIPTA, GMTAS, GESAN, GLYHO, GOODY, GOKNR, GOLTS, GOZDE, GRTHO, GSDDE, GSDHO, GUBRF, GLRYH, GLRMK, GUNDG, GRSEL, SAHOL, HALKF, HLGYO, HLVKS, HRKET, HATEK, HATSN, HDFFL, HDFGS, HEDEF, HEKTS, HKTM, HTTBT, HOROZ, HUBVC, HUNER, HUZFA, HURGZ, ENTRA, ICBCT, ICUGS, INGRM, INVEO, INVES, ISKPL, IEYHO, IDGYO, IHEVA, IHLGM, IHGZT, IHAAS, IHLAS, IHYAY, IMASM, INALR, INDES, INFO, INTEK, INTEM, ISDMR, ISFAK, ISFIN, ISGYO, ISGSY, ISMEN, ISYAT, ISBIR, ISSEN, IZINV, IZENR, IZMDC, IZFAS, JANTS, KFEIN, KLKIM, KLSER, KAPLM, KRDMA, KRDMB, KRDMD, KAREL, KARSN, KRTEK, KARTN, KTLEV, KATMR, KAYSE, KENT, KRVGD, KERVN, KZBGY, KLGYO, KLRHO, KMPUR, KLMSN, KCAER, KCHOL, KOCMT, KLSYN, KNFRT, KONTR, KONYA, KONKA, KGYO, KORDS, KRPLS, KORTS, KOTON, KOPOL, KRGYO, KRSTL, KRONT, KSTUR, KUVVA, KUYAS, KBORU, KZGYO, KUTPO, KTSKR, LIDER, LIDFA, LILAK, LMKDC, LINK, LOGO, LKMNH, LRSHO, LUKSK, LYDHO, LYDYE, MACKO, MAKIM, MAKTK, MANAS, MAGEN, MARKA, MAALT, MRSHL, MRGYO, MARTI, MTRKS, MAVI, MZHLD, MEDTR, MEGMT, MEGAP, MEKAG, MNDRS, MEPET, MERCN, MERIT, MERKO, METRO, MTRYO, MEYSU, MHRGY, MIATK, MGROS, MSGYO, MPARK, MMCAS, MOBTL, MOGAN, MNDTR, MOPAS, EGEPO, NATEN, NTGAZ, NTHOL, NETAS, NIBAS, NUHCM, NUGYO, OBAMS, OBASE, ODAS, ODINE, OFSYM, ONCSM, ONRYT, ORCAY, ORGE, ORMA, OSMEN, OSTIM, OTKAR, OTTO, OYAKC, OYAYO, OYLUM, OZKGY, OZATD, OZGYO, OZRDN, OZSUB, OZYSR, PAMEL, PNLSN, PAGYO, PAPIL, PRFFK, PRDGS, PRKME, PARSN, PASEU, PSGYO, PAHOL, PATEK, PCILT, PGSUS, PEKGY, PENGD, PENTA, PSDTC, PETKM, PKENT, PETUN, PINSU, PNSUT, PKART, PLTUR, POLHO, POLTK, PRZMA, QFINF, QUAGR, RNPOL, RALYH, RAYSG, REEDR, RYGYO, RYSAS, RODRG, ROYAL, RGYAS, RTALB, RUBNS, SAFKR, SANEL, SNICA, SANFM, SANKO, SAMAT, SARKY, SARTN, SASA, SAYAS, SDTTR, SEGMN, SEKUR, SELEC, SELVA, SERNT, SRVGY, SEYKM, SILVR, SNGYO, SMRTG, SMART, SODSN, SOKE, SKTAS, SONME, SNPAM, SUMAS, SUNTK, SURGY, SUWEN, SEKFK, SEGYO, SKBNK, SOKM, TABGD, TNZTP, TARKM, TATGD, TATEN, TAVHL, TEKTU, TKFEN, TKNSA, TMPOL, TRHOL, TGSAS, TOASO, TRGYO, TRMET, TLMAN, TSPOR, TDGYO, TSGYO, TUCLK, TUKAS, TRCAS, TUREX, MARBL, TRILC, TCELL, TRKNT, TMSN, TUPRS, THYAO, PRKAB, TTKOM, TTRAK, TBORG, TURGG, GARAN, HALKB, ISCTR, TSKB, TURSG, SISE, VAKBN, UFUK, ULAS, ULUFA, ULUSE, ULUUN, USAK, ULKER, UNLU, VAKFN, VKGYO, VKFYO, VAKKO, VANGD, VBTYZ, VRGYO, VERUS, VERTU, VESBE, VESTL, VKING, YKBNK, YAPRK, YATAS, YYLGD, YAYLA, YGGYO, YEOTK, YGYO, YYAPI, YESIL, YBTAS, YIGIT, YONGA, YKSLN, YUNSA, ZGYO, ZEDUR, ZRGYO, ZOREN, BINHO"
selected_stocks = [k.strip() + ".IS" for k in bist_raw.split(",") if k.strip()]

# --- HESAPLAMA ---
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

def process_ticker(ticker):
    try:
        # Tek tek indirme GitHub bloklamasını önlemek için daha güvenlidir
        df_h = yf.download(ticker, period="60d", interval="1h", progress=False)
        df_d = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df_h.empty or df_d.empty: return None

        last_close = df_h['Close'].iloc[-1]
        daily_200_sma = df_d['Close'].rolling(window=200).mean().iloc[-1]

        f1s = check_formation(df_h, last_close)
        df_2s = df_h.resample('2h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        f2s = check_formation(df_2s, last_close)
        df_4s = df_h.resample('4h').agg({'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        f4s = check_formation(df_4s, last_close)

        score = sum([f1s, f2s, f4s])
        if score == 0: return None
        
        # FILTRE: Çift/Full Kombo ise SMA şartı yok. Tek sinyal ise SMA 200 üstü şart.
        if score < 2 and last_close <= daily_200_sma: return None

        t_name = ticker.replace(".IS","")
        sma_icon = "🟢" if last_close > daily_200_sma else "🔴"
        sinyal_notu = f"{'1S ' if f1s else ''}{'2S ' if f2s else ''}{'4S' if f4s else ''}".strip()
        
        line = f"<b>{t_name}</b> | Fiyat: {last_close:.2f}\nBB Orta 200: {sma_icon} | Sinyal: {sinyal_notu}"
        
        g_type = "FULL" if score == 3 else ("CIFT" if score == 2 else "TEK")
        return {"type": g_type, "line": line}
    except: return None

# --- CALISTIRMA ---
full_list, cift_list, tek_list = [], [], []

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_ticker, t) for t in selected_stocks]
    for f in as_completed(futures):
        res = f.result()
        if res:
            if res["type"] == "FULL": full_list.append(res["line"])
            elif res["type"] == "CIFT": cift_list.append(res["line"])
            else: tek_list.append(res["line"])

# --- MESAJ ---
msg = ""
if full_list:
    msg += "🔥 <b>FULL KOMBO (KRİTİK)</b> 🔥\n\n" + "\n\n".join(full_list) + "\n\n"
if cift_list:
    msg += "⭐ <b>ÇİFT SİNYAL (TAKİP)</b> ⭐\n\n" + "\n\n".join(cift_list) + "\n\n"
if tek_list:
    msg += "🔍 <b>TEK SİNYAL</b> 🔍\n\n" + "\n\n".join(tek_list) + "\n\n"

if msg:
    msg += "⚠️ <b>YASAL UYARI:</b>\n<i>Yatırım tavsiyesi değildir.</i>"
    send_telegram_msg(msg)
else:
    send_telegram_msg("✅ Tarama bitti, kriterlere uyan sinyal şu an yok.")
