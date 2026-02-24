name: BIST Radar Otomasyon

on:
  schedule:
    - cron: '0 8-15 * * 1-5' # Hafta içi her saat başı
  workflow_dispatch: # Manuel çalıştırma butonu

jobs:
  run-radar:
    runs-on: ubuntu-latest
    steps:
      - name: Kodu Cek
        uses: actions/checkout@v3

      - name: Python Kur
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Kutuphaneleri Yukle
        run: |
          pip install yfinance pandas requests pytz

      - name: Botu Calistir
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python telegram_bot.py
