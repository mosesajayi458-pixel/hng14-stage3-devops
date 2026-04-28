import time
import psutil
from flask import Flask, jsonify

app = Flask(__name__)

start_time = time.time()

detector_ref = None
baseline_ref = None


@app.route("/")
def home():
    uptime = int(time.time() - start_time)
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent

    global_rate = detector_ref.global_rate() if detector_ref else 0
    top_ips = detector_ref.get_top_ips() if detector_ref else []
    banned = detector_ref.blocker.banned if detector_ref else {}

    top_ip_text = "\n".join([f"{ip} -> {rate:.2f} req/s" for ip, rate in top_ips])

    return f"""
    <html>
    <head>
        <title>HNG Anomaly Detection Dashboard</title>
        <meta http-equiv="refresh" content="3">
    </head>
    <body style="font-family: Arial;">
        <h2>HNG Stage 3 - Live Metrics</h2>

        <p><b>Uptime:</b> {uptime} seconds</p>
        <p><b>Global Req/s:</b> {global_rate:.2f}</p>
        <p><b>Baseline Mean:</b> {baseline_ref.global_mean:.2f}</p>
        <p><b>Baseline Std:</b> {baseline_ref.global_std:.2f}</p>
        <p><b>CPU Usage:</b> {cpu}%</p>
        <p><b>Memory Usage:</b> {mem}%</p>

        <h3>Top 10 Source IPs</h3>
        <pre>{top_ip_text}</pre>

        <h3>Banned IPs</h3>
        <pre>{banned}</pre>
    </body>
    </html>
    """


@app.route("/metrics")
def metrics():
    data = {
        "uptime": int(time.time() - start_time),
        "global_req_per_s": detector_ref.global_rate() if detector_ref else 0,
        "baseline_mean": baseline_ref.global_mean if baseline_ref else 0,
        "baseline_std": baseline_ref.global_std if baseline_ref else 0,
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "banned_ips": detector_ref.blocker.banned if detector_ref else {},
        "top_ips": detector_ref.get_top_ips() if detector_ref else []
    }
    return jsonify(data)


def run_dashboard(config, detector, baseline_mgr):
    global detector_ref, baseline_ref
    detector_ref = detector
    baseline_ref = baseline_mgr

    host = config["dashboard"]["host"]
    port = config["dashboard"]["port"]

    app.run(host=host, port=port)
