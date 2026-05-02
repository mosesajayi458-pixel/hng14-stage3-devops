```md
# HNG Stage 3 - Anomaly Detection / DDoS Detection Tool (DevSecOps)

This project is a real-time anomaly detection engine built to monitor incoming HTTP traffic for a Nextcloud deployment. It continuously tails Nginx JSON access logs, learns normal traffic behavior, detects abnormal spikes (per-IP and global), and automatically responds by banning suspicious IPs using `iptables`.

The tool also provides a live dashboard for monitoring system health, request rates, baseline metrics, and banned IPs.

---

## 🚀 Live Deployment Details

- **Server IP:** `100.27.253.179`
- **Nextcloud URL:** `http://100.27.253.179:8080`
- **Live Metrics Dashboard (Submission URL):** `http://hngmetrics.duckdns.org`

---

## 🛠️ Language Choice

This project was implemented in **Python** because:
- Python provides fast development speed for security tooling.
- Built-in data structures like `deque` make sliding-window tracking efficient.
- It integrates easily with Slack notifications and system commands like `iptables`.

---

## 🏗️ Architecture Overview

The system runs as 3 Docker containers:

1. **Nextcloud Container**
   - Uses the prebuilt image: `kefaslungu/hng-nextcloud`
   - Runs the Nextcloud application

2. **Nginx Reverse Proxy**
   - Fronts Nextcloud
   - Logs all requests in JSON format to a shared named volume

3. **Detector Daemon**
   - Continuously tails Nginx logs
   - Maintains sliding windows and baselines
   - Detects anomalies
   - Blocks malicious IPs using iptables
   - Sends Slack alerts
   - Serves a live dashboard

All logs are written to the named Docker volume:

`HNG-nginx-logs`

---

## 📌 Key Features Implemented

✅ Real-time Nginx log monitoring  
✅ Sliding window (60 seconds) tracking global + per-IP traffic  
✅ Rolling baseline learning (30 minutes) with mean/stddev recalculation every 60 seconds  
✅ Z-score anomaly detection (z > 3.0) OR multiplier rule (> 5× baseline mean)  
✅ Error surge tightening (4xx/5xx spike increases sensitivity)  
✅ Per-IP blocking using `iptables DROP` rules  
✅ Global anomaly alert (Slack only)  
✅ Auto-unban schedule: **10 mins → 30 mins → 2 hours → Permanent**  
✅ Slack alerts for bans, unbans, and global spikes  
✅ Live metrics dashboard refreshing every 3 seconds  
✅ Structured audit logs (ban/unban/baseline recalculation events)  
✅ Baseline graph generation showing hourly slot changes

---

# 📊 How the Sliding Window Works (Deque)

The detector maintains a **60-second sliding window** using `collections.deque`.

### Global Window
- A `deque()` stores timestamps of all requests globally.
- Every request adds `time.time()` to the deque.
- Old timestamps older than 60 seconds are removed from the left.

Example eviction logic:

- Append timestamp
- While leftmost timestamp < (now - 60): pop left

This ensures the deque always contains only the last 60 seconds of requests.

### Per-IP Window
- A dictionary maps IP → deque of timestamps
- Each IP deque is maintained the same way (append and evict)

### Request Rate Calculation
Rate is calculated as:

- **global req/s = len(global_window) / 60**
- **ip req/s = len(ip_window[ip]) / 60**

This makes the rate accurate and continuously updated.

---

# 📈 Rolling Baseline Learning (30 Minutes)

The baseline manager records **per-second request counts** and keeps a rolling history.

### How baseline works:
- Every second, the daemon records the number of requests received in that second.
- It stores counts for up to **30 minutes** (1800 seconds).
- Every **60 seconds**, it recalculates:
  - mean (average req/s)
  - standard deviation

### Hour Slot Preference
The tool stores baselines per hour slot.
If the current hour has enough data, it prefers that baseline.

This prevents a baseline learned at midnight from incorrectly applying at peak hours.

### Floor Values
To avoid division by zero and false anomalies:

- minimum mean = 1.0
- minimum std = 1.0

---

# 🚨 Detection Logic

The tool flags anomalies using:

### 1. Z-score Detection
A request rate is anomalous if:

```

z = (current_rate - mean) / std
z > 3.0

```

### 2. Multiplier Rule
A request rate is anomalous if:

```

current_rate > mean * 5

```

Whichever triggers first causes an alert/ban.

---

# ⚠️ Error Surge Detection (Threshold Tightening)

The detector also tracks 4xx/5xx responses per IP.

If an IP’s error rate becomes suspicious:

```

ip_error_rate > baseline_error_rate * 3

````

Then the detector tightens thresholds:

- z-score threshold becomes stricter (e.g. 2.5)
- multiplier becomes stricter (e.g. 3×)

This catches attackers faster if they generate many failed requests.

---

# 🔒 Blocking System (iptables)

When a per-IP anomaly is detected, the tool blocks the IP:

```bash
iptables -A INPUT -s <ip> -j DROP
````

This immediately drops all traffic from that IP.

The detector also records:

* ban time
* ban duration
* strike stage
* reason for ban

---

# 🔓 Auto-Unban Logic

Each IP has escalating strikes:

| Strike   | Duration   |
| -------- | ---------- |
| 1st ban  | 10 minutes |
| 2nd ban  | 30 minutes |
| 3rd ban  | 2 hours    |
| 4th+ ban | Permanent  |

Unbans happen automatically and trigger Slack notifications.

---

# 🔔 Slack Notifications

Slack alerts include:

* anomaly condition fired
* current rate
* baseline mean/stddev
* timestamp
* ban duration (if applicable)

Slack webhook is stored in:

`detector/config.yaml`

---

# 📺 Live Metrics Dashboard

The detector runs a Flask dashboard served at:

`http://hngmetrics.duckdns.org`

It refreshes every 3 seconds and shows:

* uptime
* global req/s
* baseline mean/stddev
* CPU usage
* memory usage
* banned IPs
* top 10 IPs by traffic

---

# 📝 Audit Logs

All key actions are written in structured format:

```
[timestamp] ACTION ip | condition | rate | baseline | duration
```

Logged actions include:

* BASELINE_RECALC
* GLOBAL_ALERT
* BAN
* UNBAN

Audit log location:

`detector/audit.log`

---

# 📂 Project Structure

```
detector/
  main.py
  monitor.py
  baseline.py
  detector.py
  blocker.py
  unbanner.py
  notifier.py
  dashboard.py
  baseline_graph.py
  config.yaml
  requirements.txt

nginx/
  nginx.conf

docs/
  architecture.png

screenshots/
  Tool-running.png
  Ban-slack.png
  Unban-slack.png
  Global-alert-slack.png
  Iptables-banned.png
  Audit-log.png
  Baseline-graph.png

README.md
docker-compose.yml
```

---

# 🖼️ Screenshots (Submission Proof)

All required screenshots are included in `screenshots/`:

1. Tool-running.png
2. Ban-slack.png
3. Unban-slack.png
4. Global-alert-slack.png
5. Iptables-banned.png
6. Audit-log.png
7. Baseline-graph.png

---

# ⚙️ Setup Instructions (Fresh VPS)

### 1. Update server

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Docker + Compose

```bash
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
newgrp docker
```

### 3. Clone repo

```bash
git clone git@github.com:mosesajayi458-pixel/hng14-stage3-devops.git
cd hng14-stage3-devops
```

### 4. Start the stack

```bash
docker-compose up -d --build
```

### 5. Confirm services

```bash
docker ps
```

### 6. Confirm Nextcloud is reachable

```bash
curl -I http://localhost:8080
```

### 7. Confirm dashboard is reachable

```bash
curl http://localhost:5000
```

### 8. Check logs

```bash
docker logs -f detector
```

---

# 🧪 Attack Simulation Testing

### Simulate heavy traffic using ApacheBench:

```bash
ab -n 20000 -c 500 http://100.27.253.179:8080/
```

Check bans:

```bash
docker exec -it detector iptables -L INPUT -n --line-numbers
```

---

# 📈 Baseline Graph Generator

Run inside detector container:

```bash
docker exec -it detector python baseline_graph.py
```

Copy output file:

```bash
docker cp detector:/app/Baseline-graph.png ./screenshots/Baseline-graph.png
```

---

# 📝 Blog Post Link
https://medium.com/@mosesajayi458/building-a-real-time-anomaly-detection-engine-ddos-detection-tool-with-python-nginx-logs-and-83af63bd8bcf

---

# 🔗 GitHub Repository

[https://github.com/mosesajayi458-pixel/hng14-stage3-devops](https://github.com/mosesajayi458-pixel/hng14-stage3-devops)

---

# 👨‍💻 Author

Olowookere Damilola
DevOps / DevSecOps Track

````

---

