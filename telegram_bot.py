import requests
import config
import csv
import os

JOURNAL_PATH = 'logs/trade_journal.csv'

def send_stats(chat_id):
    trades = []
    if os.path.isfile(JOURNAL_PATH):
        with open(JOURNAL_PATH, newline='') as f:
            trades = list(csv.DictReader(f))

    total     = len(trades)
    wins      = sum(1 for t in trades if t.get('Result', '').upper() == 'WIN')
    losses    = sum(1 for t in trades if t.get('Result', '').upper() == 'LOSS')
    breakeven = sum(1 for t in trades if t.get('Result', '').upper() == 'BREAKEVEN')
    pending   = sum(1 for t in trades if t.get('Result', '').upper() == 'PENDING')

    closed    = wins + losses + breakeven
    win_rate  = (wins / closed * 100) if closed > 0 else 0.0

    message = f"""📊 *PbaTrades — Journal Stats*

📈 Total Signals: *{total}*
✅ Wins: *{wins}*
❌ Losses: *{losses}*
➖ Breakeven: *{breakeven}*
⏳ Pending: *{pending}*

🎯 Win Rate: *{win_rate:.1f}%* _(of {closed} closed trades)_

_Trade at your own risk. Manage your risk properly._"""

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    })
    return response.json()


def send_journal(chat_id):
    trades = []
    if os.path.isfile(JOURNAL_PATH):
        with open(JOURNAL_PATH, newline='') as f:
            trades = list(csv.DictReader(f))

    if not trades:
        requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "📭 No trades in the journal yet."}
        )
        return

    result_icons = {
        'WIN':       '✅',
        'LOSS':      '❌',
        'BREAKEVEN': '➖',
        'PENDING':   '⏳',
    }

    lines = ["📒 *Last 5 Trades*"]
    for i, t in enumerate(reversed(trades[-5:]), 1):
        result    = t.get('Result', 'UNKNOWN').upper()
        direction = t.get('Direction', '').upper()
        dir_icon  = '🟢' if direction == 'BUY' else '🔴'

        lines.append(
            f"\n{i}. {dir_icon} *{t.get('Pair')}* | {t.get('Date')}\n"
            f"Direction: {direction}\n"
            f"Entry: {t.get('Entry')} | SL: {t.get('SL')}\n"
            f"TP1: {t.get('TP1')} | TP2: {t.get('TP2')}\n"
            f"Result: {result_icons.get(result, '❓')} {result}"
        )

    requests.post(
        f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"}
    )


def send_signal(pair, direction, entry, sl, tp1, tp2, timeframe):
    
    if direction.upper() == "BUY":
        emoji = "📈"
        color = "🟢"
    else:
        emoji = "📉"
        color = "🔴"

    message = f"""
🚨 *SIGNAL ALERT* 🚨

{color} *{direction.upper()}* {emoji}
💱 *Pair:* {pair}
⏱ *Timeframe:* {timeframe}
📍 *Entry:* {entry}
🛑 *Stop Loss:* {sl}
🎯 *TP1 (1:2):* {tp1}
🎯 *TP2 (1:3):* {tp2}

💰 *Want your position size?*
Reply with /size <your balance>
Example: /size 1000

⚠️ _Trade at your own risk. Manage your risk properly._
    """

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_GROUP_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)
    return response.json()


def send_position_size(chat_id, balance):
    
    risk_amount = balance * (config.DEFAULT_RISK_PERCENT / 100)
    
    message = f"""
💰 *Position Size Calculator*

Account Balance: ${balance:,.2f}
Risk ({config.DEFAULT_RISK_PERCENT}%): ${risk_amount:,.2f}

📊 *Suggested Lot Sizes:*
🔹 Conservative (0.5%): ${balance * 0.005:,.2f} risk
🔹 Normal (1%): ${risk_amount:,.2f} risk
🔹 Aggressive (2%): ${balance * 0.02:,.2f} risk

⚠️ _Never risk more than you can afford to lose._
    """

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)
    return response.json()
