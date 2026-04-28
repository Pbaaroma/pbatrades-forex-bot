# PbaTrades Forex Signal Bot 🚀

A Smart Money Concepts (SMC) based forex signal bot that automatically detects trading setups and sends alerts to a Telegram group.

## What It Does
- Detects liquidity sweeps on TradingView charts
- Identifies Fair Value Gaps (FVG) after sweeps
- Sends BUY/SELL signals to Telegram with Entry, SL, TP1 and TP2
- Position size calculator for each trader based on their account balance
- Auto logs every signal to a trade journal (CSV)

## Strategy
- **Session:** NY Killzone (9:00am - 11:30am EST)
- **Timeframes:** 15min and 5min
- **Entry:** Liquidity sweep + FVG formation + retracement into FVG
- **Risk/Reward:** 1:2 (TP1) and 1:3 (TP2)
- **Pairs:** GBPUSD, AUDUSD, GBPJPY, US30, NASDAQ, BTCUSD, XAUUSD

## Tech Stack
- Python + Flask (server)
- Gunicorn (production server)
- Nginx (reverse proxy)
- Pine Script v5 (TradingView strategy)
- Telegram Bot API
- DigitalOcean VPS
- DuckDNS + Let's Encrypt SSL

## Setup
1. Clone the repo
2. Copy `config.example.py` to `config.py` and fill in your values
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python3 main.py`

## Project Structure
- `main.py` — starts the server
- `webhook.py` — receives TradingView alerts
- `telegram_bot.py` — sends signals to Telegram
- `config.example.py` — configuration template

## Disclaimer
This bot is for educational purposes only. Trade at your own risk.
