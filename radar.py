name: BIST Radar Otomasyon

on:
  schedule:
    # Türkiye Saati (UTC+3) ile hafta içi her saat başı:
    # 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00
    - cron: '0 7-15 * * 1-5'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Kodları Çek
        uses: actions/checkout@v2
      - name: Python Kur
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Kütüphaneleri Yükle
        run: pip install yfinance pandas numpy requests
      - name: Radarı Çalıştır
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python radar.py
