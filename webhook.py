from flask import Flask, request, jsonify, render_template_string
from telegram_bot import send_signal
import logging
import config
import csv
import os
import json
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

JOURNAL_PATH = 'logs/trade_journal.csv'


def read_trades():
    if not os.path.isfile(JOURNAL_PATH):
        return [], []
    with open(JOURNAL_PATH, newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return fieldnames, rows


@app.route('/update-result', methods=['POST'])
def update_result():
    data = request.json or {}
    try:
        row_index = int(data['index'])
    except (KeyError, ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid index"}), 400

    new_result = data.get('result', '').upper()
    if new_result not in ('WIN', 'LOSS', 'BREAKEVEN'):
        return jsonify({"status": "error", "message": "Invalid result"}), 400

    fieldnames, rows = read_trades()
    if not rows:
        return jsonify({"status": "error", "message": "Journal not found"}), 404
    if row_index < 0 or row_index >= len(rows):
        return jsonify({"status": "error", "message": "Row index out of range"}), 400

    rows[row_index]['Result'] = new_result

    with open(JOURNAL_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return jsonify({"status": "success"}), 200


@app.route('/dashboard/data', methods=['GET'])
def dashboard_data():
    fieldnames, trades = read_trades()
    indexed = [{'index': i, **t} for i, t in enumerate(trades)]
    stats = {
        'total':     len(trades),
        'win':       sum(1 for t in trades if t.get('Result', '').upper() == 'WIN'),
        'loss':      sum(1 for t in trades if t.get('Result', '').upper() == 'LOSS'),
        'breakeven': sum(1 for t in trades if t.get('Result', '').upper() == 'BREAKEVEN'),
        'pending':   sum(1 for t in trades if t.get('Result', '').upper() == 'PENDING'),
    }
    return jsonify({'trades': indexed, 'stats': stats})


@app.route('/dashboard', methods=['GET'])
def dashboard():
    fieldnames, trades = read_trades()
    indexed_trades = list(enumerate(trades))

    stats = {
        'total': len(trades),
        'win': sum(1 for t in trades if t.get('Result', '').upper() == 'WIN'),
        'loss': sum(1 for t in trades if t.get('Result', '').upper() == 'LOSS'),
        'pending': sum(1 for t in trades if t.get('Result', '').upper() == 'PENDING'),
        'breakeven': sum(1 for t in trades if t.get('Result', '').upper() == 'BREAKEVEN'),
    }

    DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PbaTrades — Trade Journal</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0d0f14;
    color: #c9d1d9;
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    padding: 2rem 1.5rem;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
  }
  .brand { display: flex; align-items: center; gap: .75rem; }
  .brand-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #00c875;
    box-shadow: 0 0 8px #00c875;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .35; }
  }
  h1 { font-size: 1.5rem; font-weight: 700; color: #e6edf3; letter-spacing: .02em; }
  .subtitle { font-size: .8rem; color: #6e7681; margin-top: .15rem; }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  .stat-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.25rem;
  }
  .stat-label { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: #6e7681; }
  .stat-value { font-size: 1.9rem; font-weight: 700; margin-top: .25rem; }
  .stat-total  .stat-value { color: #58a6ff; }
  .stat-win    .stat-value { color: #3fb950; }
  .stat-loss   .stat-value { color: #f85149; }
  .stat-pending .stat-value { color: #d29922; }

  .table-wrap {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    overflow: auto;
  }
  table { width: 100%; border-collapse: collapse; font-size: .86rem; }
  thead tr { background: #1c2128; }
  th {
    padding: .75rem 1rem;
    text-align: left;
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: #6e7681;
    white-space: nowrap;
    border-bottom: 1px solid #21262d;
  }
  td {
    padding: .7rem 1rem;
    border-bottom: 1px solid #161b22;
    white-space: nowrap;
    color: #c9d1d9;
  }
  tbody tr { transition: background .15s; }
  tbody tr:hover { background: #1c2128; }
  tbody tr:last-child td { border-bottom: none; }

  .badge {
    display: inline-block;
    padding: .2rem .55rem;
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
  }
  .badge-buy       { background: #0f3d2e; color: #3fb950; border: 1px solid #238636; }
  .badge-sell      { background: #3d1b1b; color: #f85149; border: 1px solid #da3633; }
  .badge-win       { background: #0f3d2e; color: #3fb950; border: 1px solid #238636; }
  .badge-loss      { background: #3d1b1b; color: #f85149; border: 1px solid #da3633; }
  .badge-pending   { background: #2d2008; color: #d29922; border: 1px solid #9e6a03; }
  .badge-breakeven { background: #0d2137; color: #58a6ff; border: 1px solid #1f6feb; }
  .badge-unknown   { background: #1c2128; color: #6e7681; border: 1px solid #30363d; }

  .result-actions { display: flex; gap: .35rem; align-items: center; }
  .btn-result {
    padding: .18rem .5rem;
    border-radius: 999px;
    font-size: .68rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
    cursor: pointer;
    border: 1px solid transparent;
    transition: opacity .15s, transform .1s;
  }
  .btn-result:hover  { opacity: .8; }
  .btn-result:active { transform: scale(.95); }
  .btn-result:disabled { opacity: .4; cursor: not-allowed; }
  .btn-win       { background: #0f3d2e; color: #3fb950; border-color: #238636; }
  .btn-loss      { background: #3d1b1b; color: #f85149; border-color: #da3633; }
  .btn-breakeven { background: #0d2137; color: #58a6ff; border-color: #1f6feb; }

  .pair { font-weight: 600; color: #e6edf3; }
  .mono { font-family: 'SF Mono', 'Fira Code', monospace; color: #b3b9c4; }

  .empty {
    text-align: center;
    padding: 3rem;
    color: #6e7681;
    font-size: .9rem;
  }

  .filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: .5rem;
    margin-bottom: 1.25rem;
  }
  .btn-filter {
    padding: .3rem .85rem;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 600;
    letter-spacing: .04em;
    cursor: pointer;
    border: 1px solid #30363d;
    background: #161b22;
    color: #8b949e;
    transition: background .15s, color .15s, border-color .15s;
  }
  .btn-filter:hover { border-color: #58a6ff; color: #c9d1d9; }
  .btn-filter.active {
    background: #0f3d2e;
    border-color: #238636;
    color: #3fb950;
  }

  footer {
    margin-top: 2rem;
    text-align: center;
    font-size: .75rem;
    color: #30363d;
  }

  .refresh-status {
    display: flex;
    align-items: center;
    gap: .4rem;
    font-size: .75rem;
    color: #6e7681;
    user-select: none;
  }
  .refresh-icon {
    font-size: .85rem;
    transition: transform .4s ease;
  }
  .refresh-icon.spinning {
    animation: spin .6s linear;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  .refresh-count {
    font-variant-numeric: tabular-nums;
    min-width: 2ch;
    text-align: right;
  }
  .refresh-flash {
    color: #3fb950;
    transition: color 1s ease;
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="brand-dot"></div>
    <div>
      <h1>PbaTrades</h1>
      <div class="subtitle">Trade Journal Dashboard</div>
    </div>
  </div>
  <div class="refresh-status">
    <span class="refresh-icon" id="refreshIcon">↻</span>
    <span>Refreshing in <span class="refresh-count" id="refreshCount">30</span>s</span>
  </div>
</header>

<div class="stats">
  <div class="stat-card stat-total">
    <div class="stat-label">Total Signals</div>
    <div class="stat-value">{{ stats.total }}</div>
  </div>
  <div class="stat-card stat-win">
    <div class="stat-label">Wins</div>
    <div class="stat-value">{{ stats.win }}</div>
  </div>
  <div class="stat-card stat-loss">
    <div class="stat-label">Losses</div>
    <div class="stat-value">{{ stats.loss }}</div>
  </div>
  <div class="stat-card stat-pending">
    <div class="stat-label">Pending</div>
    <div class="stat-value">{{ stats.pending }}</div>
  </div>
  <div class="stat-card stat-breakeven">
    <div class="stat-label">Breakeven</div>
    <div class="stat-value" style="color:#58a6ff">{{ stats.breakeven }}</div>
  </div>
</div>

<div class="filter-bar" id="filterBar">
  <button class="btn-filter active" onclick="setFilter('ALL')">ALL</button>
  <button class="btn-filter" onclick="setFilter('GBPUSD')">GBPUSD</button>
  <button class="btn-filter" onclick="setFilter('AUDUSD')">AUDUSD</button>
  <button class="btn-filter" onclick="setFilter('GBPJPY')">GBPJPY</button>
  <button class="btn-filter" onclick="setFilter('BTCUSD')">BTCUSD</button>
  <button class="btn-filter" onclick="setFilter('US30')">US30</button>
  <button class="btn-filter" onclick="setFilter('NASDAQ')">NASDAQ</button>
  <button class="btn-filter" onclick="setFilter('XAUUSD')">XAUUSD</button>
</div>

<div class="table-wrap">
  {% if trades %}
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Date</th>
        <th>Time</th>
        <th>Pair</th>
        <th>Direction</th>
        <th>Timeframe</th>
        <th>Entry</th>
        <th>SL</th>
        <th>TP1</th>
        <th>TP2</th>
        <th>Result</th>
      </tr>
    </thead>
    <tbody>
      {% for csv_index, t in indexed_trades|reverse %}
      {% set result = t.Result|upper %}
      {% set direction = t.Direction|upper %}
      <tr>
        <td class="mono" style="color:#30363d">{{ loop.index }}</td>
        <td class="mono">{{ t.Date }}</td>
        <td class="mono">{{ t.Time }}</td>
        <td class="pair">{{ t.Pair }}</td>
        <td>
          <span class="badge {% if direction == 'BUY' %}badge-buy{% elif direction == 'SELL' %}badge-sell{% else %}badge-unknown{% endif %}">
            {{ t.Direction }}
          </span>
        </td>
        <td class="mono">{{ t.Timeframe }}</td>
        <td class="mono">{{ t.Entry }}</td>
        <td class="mono">{{ t.SL }}</td>
        <td class="mono">{{ t.TP1 }}</td>
        <td class="mono">{{ t.TP2 }}</td>
        <td class="result-cell">
          {% if result == 'PENDING' %}
          <div class="result-actions">
            <button class="btn-result btn-win"       onclick="setResult(this, {{ csv_index }}, 'WIN')">Win</button>
            <button class="btn-result btn-loss"      onclick="setResult(this, {{ csv_index }}, 'LOSS')">Loss</button>
            <button class="btn-result btn-breakeven" onclick="setResult(this, {{ csv_index }}, 'BREAKEVEN')">BE</button>
          </div>
          {% else %}
          <span class="badge {% if result == 'WIN' %}badge-win{% elif result == 'LOSS' %}badge-loss{% elif result == 'BREAKEVEN' %}badge-breakeven{% else %}badge-unknown{% endif %}">
            {{ t.Result }}
          </span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">No trades logged yet.</div>
  {% endif %}
</div>

<footer>PbaTrades Forex Signal Bot</footer>

<script>
const BADGE = {
  WIN:       'badge-win',
  LOSS:      'badge-loss',
  BREAKEVEN: 'badge-breakeven',
};

// --- result update ---

async function setResult(btn, index, result) {
  const cell = btn.closest('.result-cell');
  const btns = cell.querySelectorAll('button');
  btns.forEach(b => b.disabled = true);

  try {
    const res = await fetch('/update-result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index, result }),
    });
    if (!res.ok) throw new Error('Server error');
    cell.innerHTML = `<span class="badge ${BADGE[result]}">${result}</span>`;
    resetCountdown();
  } catch {
    btns.forEach(b => b.disabled = false);
    cell.style.outline = '1px solid #f85149';
    setTimeout(() => cell.style.outline = '', 2000);
  }
}

// --- pair filter ---

let activeFilter = 'ALL';
let allTrades = {{ indexed_trades_json | safe }};

function setFilter(pair) {
  activeFilter = pair;
  document.querySelectorAll('.btn-filter').forEach(b => {
    b.classList.toggle('active', b.textContent === pair);
  });
  rebuildTable(allTrades);
}

// --- auto-refresh ---

const INTERVAL = 30;
let countdown = INTERVAL;
let refreshPending = false;

function resultCell(t) {
  const result = (t.Result || '').toUpperCase();
  if (result === 'PENDING') {
    return `<div class="result-actions">
      <button class="btn-result btn-win"       onclick="setResult(this,${t.index},'WIN')">Win</button>
      <button class="btn-result btn-loss"      onclick="setResult(this,${t.index},'LOSS')">Loss</button>
      <button class="btn-result btn-breakeven" onclick="setResult(this,${t.index},'BREAKEVEN')">BE</button>
    </div>`;
  }
  const cls = BADGE[result] || 'badge-unknown';
  return `<span class="badge ${cls}">${t.Result}</span>`;
}

function directionBadge(dir) {
  const d = (dir || '').toUpperCase();
  const cls = d === 'BUY' ? 'badge-buy' : d === 'SELL' ? 'badge-sell' : 'badge-unknown';
  return `<span class="badge ${cls}">${dir}</span>`;
}

function rebuildTable(trades) {
  allTrades = trades;
  const visible = activeFilter === 'ALL' ? trades : trades.filter(t => t.Pair === activeFilter);
  const wrap = document.querySelector('.table-wrap');
  if (!visible.length) {
    wrap.innerHTML = '<div class="empty">No trades found.</div>';
    return;
  }

  const rows = [...visible].reverse().map((t, i) => `
    <tr>
      <td class="mono" style="color:#30363d">${i + 1}</td>
      <td class="mono">${t.Date}</td>
      <td class="mono">${t.Time}</td>
      <td class="pair">${t.Pair}</td>
      <td>${directionBadge(t.Direction)}</td>
      <td class="mono">${t.Timeframe}</td>
      <td class="mono">${t.Entry}</td>
      <td class="mono">${t.SL}</td>
      <td class="mono">${t.TP1}</td>
      <td class="mono">${t.TP2}</td>
      <td class="result-cell">${resultCell(t)}</td>
    </tr>`).join('');

  wrap.innerHTML = `
    <table>
      <thead><tr>
        <th>#</th><th>Date</th><th>Time</th><th>Pair</th><th>Direction</th>
        <th>Timeframe</th><th>Entry</th><th>SL</th><th>TP1</th><th>TP2</th><th>Result</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function rebuildStats(s) {
  document.querySelector('.stat-total   .stat-value').textContent = s.total;
  document.querySelector('.stat-win     .stat-value').textContent = s.win;
  document.querySelector('.stat-loss    .stat-value').textContent = s.loss;
  document.querySelector('.stat-pending .stat-value').textContent = s.pending;
  const be = document.querySelector('.stat-breakeven .stat-value');
  if (be) be.textContent = s.breakeven;
}

async function refresh() {
  if (refreshPending) return;
  if (document.querySelector('.btn-result:disabled')) return; // setResult in flight

  refreshPending = true;
  const icon = document.getElementById('refreshIcon');
  icon.classList.add('spinning');

  try {
    const res = await fetch('/dashboard/data');
    if (!res.ok) throw new Error();
    const { trades, stats } = await res.json();
    rebuildTable(trades);
    rebuildStats(stats);
    icon.classList.add('refresh-flash');
    setTimeout(() => icon.classList.remove('refresh-flash'), 1000);
  } catch {
    // silently skip — try again next cycle
  } finally {
    refreshPending = false;
    icon.classList.remove('spinning');
  }
}

function resetCountdown() {
  countdown = INTERVAL;
  document.getElementById('refreshCount').textContent = countdown;
}

setInterval(() => {
  countdown -= 1;
  if (countdown <= 0) {
    refresh();
    countdown = INTERVAL;
  }
  document.getElementById('refreshCount').textContent = countdown;
}, 1000);
</script>

</body>
</html>"""

    return render_template_string(
        DASHBOARD_HTML,
        trades=trades,
        indexed_trades=indexed_trades,
        indexed_trades_json=json.dumps(indexed_trades),
        stats=stats,
    )


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "server is running"}), 200
