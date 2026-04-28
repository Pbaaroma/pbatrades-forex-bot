# PbaTrades Forex Signal Bot — Codebase Guide

## Project Overview

A Flask-based webhook server that receives TradingView alerts, logs trades to a CSV journal, sends signals to a Telegram group, and serves a live trade journal dashboard.

**Entry point:** `main.py` — starts the Flask server and handles Telegram commands  
**Webhook + dashboard:** `webhook.py` — all Flask routes  
**Telegram helpers:** `telegram_bot.py` — `send_signal`, `send_stats`, `send_journal`  
**Config:** `config.py` (live) / `config.example.py` (template)  
**Journal:** `logs/trade_journal.csv`

### Routes
| Route | Method | Purpose |
|---|---|---|
| `/webhook` | POST | Receive TradingView signal, log + forward to Telegram |
| `/dashboard` | GET | Live trade journal UI |
| `/dashboard/data` | GET | JSON feed used by dashboard auto-refresh |
| `/update-result` | POST | Update a trade result (WIN/LOSS/BREAKEVEN) from dashboard |
| `/telegram` | POST | Handle Telegram bot commands (`/size`, `/stats`, `/journal`) |
| `/health` | GET | Health check |

---

## Gabriel's SMC Trading Strategy

### Philosophy
Smart Money Concepts (SMC) — trade with institutional order flow by identifying liquidity grabs followed by Fair Value Gap (FVG) or Order Block reactions. Only trade during the NY Killzone. Never chase; wait for the full setup to confirm.

---

### Session Schedule (CST / Minnesota time)

| Session | CST | EST | Role |
|---|---|---|---|
| Pre-Asian | 5:00 pm – 7:00 pm | 6:00 pm – 8:00 pm | Mark-up only. No trading. |
| Asian | 7:00 pm – 2:00 am | 8:00 pm – 3:00 am | Consolidation. Mark range H/L. |
| London | 2:00 am – 5:00 am | 3:00 am – 6:00 am | Watch for liquidity grabs of Asian H/L. Sets NY direction. |
| **NY Killzone** | **8:00 am – 10:30 am** | **9:00 am – 11:30 am** | **PRIME TRADING WINDOW — only time to take entries.** |
| Post-NY | 11:00 am + | 12:00 pm + | Take profit, journal trades. No new entries. |

---

### Pairs Traded
`GBPUSD` `AUDUSD` `GBPJPY` `US30` `NASDAQ` `BTCUSD` `XAUUSD`

**Max 3 pairs open simultaneously.**  
Never hold a position past 11:30 am EST.

---

### Timeframes
- **15-minute** — setup confirmation (bias, sweep, FVG location)
- **5-minute** — entry trigger (close inside FVG)

---

### Pre-Session Mark-Up (5–7 pm CST)

Before trading begins, mark the following on Daily, 4H, and 1H charts:

1. **Bias** — determine bullish or bearish for the session
2. **Order Blocks (OB)** — last bearish candle before a bullish move (demand OB) or last bullish candle before a bearish move (supply OB)
3. **Liquidity Pools** — mark with horizontal lines:
   - Previous swing highs and lows
   - Equal highs / equal lows
   - Session highs and lows (Asian, London, previous NY)
   - Trendline liquidity

---

### Asian Session (7 pm – 2 am CST)

- Price consolidates — do not trade
- Mark the **Asian range high** and **Asian range low**
- These become the primary liquidity targets for London and NY sessions

---

### London Session (2–5 am CST)

- Watch for a **liquidity grab** of the Asian range high or low
- Identify the first FVG or OB reaction
- Use this to **set the directional bias** for the NY Killzone
- Do not take entries during London — observation only

---

### Liquidity Pool Identification

Liquidity sits above swing highs and below swing lows where stop-losses cluster. Mark:

- **Buyside liquidity (BSL)** — above equal highs, previous session highs, swing highs
- **Sellside liquidity (SSL)** — below equal lows, previous session lows, swing lows

Price will run to these levels to grab liquidity before reversing.

---

### Sweep Detection Rules

A liquidity sweep is confirmed when:

1. Price **crosses above** a previous high (bearish sweep / BSL grab) **or below** a previous low (bullish sweep / SSL grab)
2. The cross can be a **wick OR a candle close** beyond the level
3. Price must **close back past the level** on the same or next candle to confirm the sweep is complete
4. A sweep without a close-back is not confirmed — wait

---

### FVG Formation Rules

A Fair Value Gap (FVG) is a 3-candle imbalance that forms after a confirmed sweep. It must form **within 5 candles** of the sweep candle.

#### Bullish FVG (after a low sweep / SSL grab)
- Candle 1 low and Candle 3 high do **not** overlap — gap between them is the FVG zone
- Candle 2 (the middle candle) must be **bullish** (blue / green)
- The entire FVG must form **above** the sweep candle
- Mark the FVG zone as a demand area (entry zone for buys)

#### Bearish FVG (after a high sweep / BSL grab)
- Candle 1 high and Candle 3 low do **not** overlap — gap between them is the FVG zone
- Candle 2 (the middle candle) must be **bearish** (black / red)
- The entire FVG must form **below** the sweep candle
- Mark the FVG zone as a supply area (entry zone for sells)

---

### Entry Conditions

All four conditions must be met before entering:

1. **Killzone** — current time is within NY Killzone (8:00–10:30 am CST / 9:00–11:30 am EST)
2. **Sweep confirmed** — a liquidity level has been swept with a close-back past the level
3. **FVG formed** — a valid FVG has appeared within 5 candles of the sweep, on the correct side
4. **Price closes inside the FVG** — wait for a **5-minute candle to fully close** inside the FVG box before entering. Do not enter on a wick touch — bar close only.

---

### Stop Loss Placement

- **BUY trade** — SL below the wick low of the sweep candle + 5 pip buffer
- **SELL trade** — SL above the wick high of the sweep candle + 5 pip buffer

The sweep candle wick defines the invalidation point. If price returns beyond it, the setup is void.

---

### Take Profit Levels

| Target | Rule |
|---|---|
| **TP1** | 1:2 Risk/Reward from entry |
| **TP2** | 1:3 Risk/Reward from entry |

Move SL to breakeven after TP1 is hit. Let the remainder run to TP2.

---

### DXY Confluence (Gold / XAUUSD)

Use DXY to confirm Gold direction before entering:

| DXY condition | Gold condition | Signal |
|---|---|---|
| DXY in **premium** (overbought / supply zone) | Gold in **discount / OTE zone** | Look for **Gold buys** |
| DXY in **discount** (oversold / demand zone) | Gold in **premium** | Look for **Gold sells** |
| DXY shows **liquidity sweep + CHoCH** | — | Confirms directional bias for the session |

CHoCH (Change of Character) = price breaks the most recent swing high (in a downtrend) or swing low (in an uptrend), signalling a potential reversal.

---

### Trade Management Rules

- **Max 3 pairs** open at the same time
- **Hard stop at 11:30 am EST** — close all positions regardless of outcome
- No new entries after 10:30 am CST
- After TP1 hit: move SL to breakeven, target TP2
- After session: log result in journal (WIN / LOSS / BREAKEVEN)

---

### Full Setup Checklist

```
[ ] Pre-session mark-up done (bias, OBs, liquidity pools)
[ ] Asian range high and low marked
[ ] London sweep observed — directional bias set
[ ] NY Killzone active (8:00–10:30 am CST)
[ ] Liquidity level swept (wick or close, confirmed close-back)
[ ] Valid FVG formed within 5 candles of sweep, on correct side
[ ] Middle candle of FVG correct colour (bullish = green, bearish = red)
[ ] FVG on correct side of sweep candle
[ ] DXY confluence checked (XAUUSD trades)
[ ] Fewer than 3 pairs currently open
[ ] 5-min candle CLOSES inside FVG before entry
[ ] SL placed beyond sweep candle wick + 5 pip buffer
[ ] TP1 at 1:2 RR, TP2 at 1:3 RR set on entry
```
