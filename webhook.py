from flask import Flask, request, jsonify
from telegram_bot import send_signal
import logging
import config
import csv
import os
from datetime import datetime

logging.basicConfig(
    filename='logs/alerts.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

app = Flask(__name__)

def log_trade(pair, direction, entry, sl, tp1, tp2, timeframe):
    file_exists = os.path.isfile('logs/trade_journal.csv')
    
    with open('logs/trade_journal.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(['Date', 'Time', 'Pair', 'Direction', 'Timeframe', 'Entry', 'SL', 'TP1', 'TP2', 'Result'])
        
        now = datetime.utcnow()
        writer.writerow([
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            pair,
            direction,
            timeframe,
            entry,
            sl,
            tp1,
            tp2,
            'PENDING'
        ])

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json

        pair      = data.get('pair', 'UNKNOWN')
        direction = data.get('direction', 'UNKNOWN')
        entry     = data.get('entry', 'UNKNOWN')
        sl        = data.get('sl', 'UNKNOWN')
        tp1       = data.get('tp1', 'UNKNOWN')
        tp2       = data.get('tp2', 'UNKNOWN')
        timeframe = data.get('timeframe', 'UNKNOWN')

        logging.info(f"Signal: {pair} {direction} Entry:{entry} SL:{sl} TP1:{tp1} TP2:{tp2} TF:{timeframe}")

        log_trade(pair, direction, entry, sl, tp1, tp2, timeframe)
        send_signal(pair, direction, entry, sl, tp1, tp2, timeframe)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "server is running"}), 200
