import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="VIP BIST RADAR", layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 VIP Giriş")
    pwd = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if pwd == "12345":
            st.session_state.auth = True
            st.rerun()
else:
    st.title("🎯 VIP BIST RADAR TERMINAL")
    if st.button("TARAMAYI BAŞLAT"):
        st.info("Piyasa taranıyor, tablo hazırlanıyor...")
        # Analiz ve Tablo kodları buraya otomatik gelecek
        st.success("Tarama Bitti!")
