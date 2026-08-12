import sqlite3
import uuid
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)
DB_FILE = "analytics.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('SUCCESS', 'FAILED')),
            reason TEXT DEFAULT 'N/A'
        )
    ''')
    conn.commit()
    conn.close()


init_db()


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM call_logs")
    total_calls = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM call_logs WHERE status = 'SUCCESS'")
    successful_calls = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM call_logs WHERE status = 'FAILED'")
    failed_calls = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls
    })


@app.route("/api/log_test_call", methods=["POST"])
def log_test_call():
    data = request.json or {}
    status = data.get("status", "SUCCESS").upper()
    reason = data.get("reason", "Manual Test Trigger")
    room_name = f"room-{uuid.uuid4().hex[:6]}"

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO call_logs (room_name, status, reason) VALUES (?, ?, ?)",
        (room_name, status, reason)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Call logged successfully", "status": status}), 200


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AshaAssist - Call Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px; }
        .header { text-align: center; margin-bottom: 30px; }
        .grid { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 30px; }
        .card { background: #1e293b; border-radius: 12px; padding: 25px; width: 200px; text-align: center; border: 1px solid #334155; }
        .card h3 { margin: 0; color: #94a3b8; font-size: 14px; }
        .card .number { font-size: 40px; font-weight: bold; margin-top: 10px; color: #38bdf8; }
        .card.success .number { color: #4ade80; }
        .card.failed .number { color: #f87171; }
        .chart-box { width: 320px; margin: 0 auto; background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        .controls { text-align: center; margin-top: 25px; }
        button { background: #0284c7; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; margin: 5px; font-weight: bold; }
        button.fail-btn { background: #dc2626; }
        .privacy-tag { background: #059669; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; display: inline-block; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 AshaAssist Call Analytics Dashboard</h1>
        <p>Real-Time Health Access Telemetry | Powered by Murf Falcon TTS</p>
        <span class="privacy-tag">🔒 Privacy Preserved (No PII / No Transcripts)</span>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Total Calls</h3>
            <div class="number" id="total-calls">0</div>
        </div>
        <div class="card success">
            <h3>Successful Calls</h3>
            <div class="number" id="successful-calls">0</div>
        </div>
        <div class="card failed">
            <h3>Failed Calls</h3>
            <div class="number" id="failed-calls">0</div>
        </div>
    </div>

    <div class="chart-box">
        <canvas id="metricsChart"></canvas>
    </div>

    <div class="controls">
        <button onclick="triggerCall('SUCCESS')">➕ Log Successful Call</button>
        <button class="fail-btn" onclick="triggerCall('FAILED')">➕ Log Failed Call</button>
    </div>

    <script>
        let chart;

        function renderChart(success, failed) {
            const ctx = document.getElementById('metricsChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Successful', 'Failed'],
                    datasets: [{
                        data: [success, failed],
                        backgroundColor: ['#4ade80', '#f87171'],
                        borderWidth: 0
                    }]
                },
                options: { plugins: { legend: { labels: { color: '#f8fafc' } } } }
            });
        }

        async function fetchMetrics() {
            const res = await fetch('/api/metrics');
            const data = await res.json();
            
            document.getElementById('total-calls').innerText = data.total_calls;
            document.getElementById('successful-calls').innerText = data.successful_calls;
            document.getElementById('failed-calls').innerText = data.failed_calls;

            if (!chart) {
                renderChart(data.successful_calls, data.failed_calls);
            } else {
                chart.data.datasets[0].data = [data.successful_calls, data.failed_calls];
                chart.update();
            }
        }

        async function triggerCall(status) {
            await fetch('/api/log_test_call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: status })
            });
            fetchMetrics();
        }

        fetchMetrics();
        setInterval(fetchMetrics, 3000);
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


if __name__ == "__main__":
    app.run(port=5000, debug=True)