from flask import Flask, request, jsonify
from webhook import app
from telegram_bot import send_position_size
import config

# Handle /size command from Telegram
@app.route('/telegram', methods=['POST'])
def telegram_update():
    data = request.json
    
    try:
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')

        # Handle /size command
        if text.startswith('/size'):
            parts = text.split()
            if len(parts) == 2:
                balance = float(parts[1])
                send_position_size(chat_id, balance)
            else:
                # Tell user correct format
                url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
                import requests
                requests.post(url, json={
                    "chat_id": chat_id,
                    "text": "⚠️ Please use the correct format:\n/size 1000",
                    "parse_mode": "Markdown"
                })

    except Exception as e:
        print(f"Error: {str(e)}")

    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    print("🚀 Forex Bot Server is running...")
    app.run(host=config.HOST, port=config.PORT)
