import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="VIP BIST RADAR", layout="wide")

# Şifre Ekranı
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Şifre Giriniz", type="password")
    if st.button("Giriş"):
        if pwd == "12345": # Şifren bu
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Hatalı!")
else:
    st.title("🎯 VIP BIST RADAR TERMINAL")
    if st.button("TARAMAYI BAŞLAT"):
        # Buraya radar.py'deki analiz mantığını tablo olarak ekleyeceğiz
        st.write("Veriler çekiliyor...")
        # ... (Analiz kodları buraya gelecek, şimdilik arayüzü kuruyoruz)
        st.success("Tarama sonuçları aşağıda listelenecektir.")
