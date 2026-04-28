import requests
import config

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
