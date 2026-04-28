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

📌 Blog Post (Hashnode):
https://mydev-blog.hashnode.dev/building-a-real-time-anomaly-detection-engine-ddos-detection-tool-with-python-nginx-logs-and-iptables-when-you-deploy-an-application-publicly-on-the-internet-it-becomes-a-target-sometimes-the-attacks-are-obvious-sometimes-they-are-subtle-but-one-thing-is-guaranteed-if-your-platform-is-open-to-the-world-you-will-eventually-receive-suspicious-traffic-in-this-post-i-ll-explain-how-i-built-a-real-time-anomaly-detection-engine-that-monitors-http-traffic-learns-what-normal-traffic-looks-like-detects-abnormal-spikes-and-automatically-responds-by-blocking-malicious-ip-addresses-using-iptables-this-project-was-built-as-part-of-the-hng-internship-devsecops-track-stage-3-what-this-tool-does-the-system-monitors-all-incoming-http-traffic-to-a-nextcloud-instance-and-detects-sudden-spikes-in-traffic-globally-possible-ddos-attack-high-request-rate-from-a-single-ip-possible-brute-force-or-abuse-surges-in-error-responses-4xx-5xx-which-often-indicate-malicious-behavior-once-an-anomaly-is-detected-if-the-anomaly-is-global-it-sends-a-slack-alert-if-the-anomaly-is-from-a-single-ip-it-sends-a-slack-alert-and-blocks-the-ip-automatically-using-iptables-the-tool-also-includes-a-live-monitoring-dashboard-that-updates-every-3-seconds-high-level-architecture-the-entire-project-runs-on-a-linux-vps-aws-ec2-using-docker-compose-with-3-containers-1-nextcloud-container-this-is-the-cloud-storage-application-itself-2-nginx-reverse-proxy-this-sits-in-front-of-nextcloud-and-logs-all-requests-in-json-format-3-detector-daemon-python-this-continuously-reads-nginx-logs-in-real-time-detects-anomalies-bans-ips-and-runs-the-dashboard-the-most-important-part-is-that-nginx-writes-logs-into-a-shared-docker-named-volume-hng-nginx-logs-this-volume-is-mounted-read-only-by-both-nextcloud-and-the-detector-why-nginx-access-logs-matter-nginx-logs-contain-valuable-information-such-as-source-ip-request-method-get-post-requested-endpoint-login-upload-etc-response-status-code-200-404-500-response-size-if-we-can-monitor-these-logs-in-real-time-we-can-detect-suspicious-patterns-early-json-log-format-configuration-to-make-parsing-easier-i-configured-nginx-to-log-requests-in-json-format-like-this-json-timestamp-2026-04-28t12-05-44-00-00-source-ip-203-0-113-10-method-get-path-status-200-response-size-6674-json-logs-are-much-easier-to-parse-than-the-default-nginx-log-format-the-sliding-window-concept-deque-one-of-the-most-important-requirements-in-this-project-was-using-a-sliding-window-to-track-request-rates-instead-of-counting-requests-per-minute-the-system-must-always-track-only-the-last-60-seconds-of-traffic-to-achieve-this-i-used-python-s-collections-deque-why-deque-a-deque-is-perfect-because-appending-is-fast-o-1-removing-from-the-left-is-fast-o-1-how-sliding-window-works-each-request-is-stored-as-a-timestamp-example-python-self-global-window-append-time-time-but-we-must-remove-old-timestamps-older-than-60-seconds-python-while-dq-and-dq-0-now-60-dq-popleft-this-means-the-deque-always-contains-only-requests-from-the-last-60-seconds-calculating-request-rate-once-we-have-a-deque-of-timestamps-the-request-rate-is-simply-python-rate-len-deque-60-so-global-req-s-len-global-window-60-ip-req-s-len-ip-window-ip-60-learning-normal-traffic-rolling-baseline-anomaly-detection-needs-a-reference-point-instead-of-hardcoding-a-fixed-number-like-50-req-s-is-bad-the-tool-learns-normal-traffic-by-building-a-baseline-rolling-baseline-window-30-minutes-1800-seconds-every-second-the-daemon-counts-how-many-requests-happened-in-that-second-that-count-is-stored-in-history-then-every-60-seconds-the-baseline-is-recalculated-using-mean-standard-deviation-why-mean-and-standard-deviation-mean-tells-us-the-average-request-rate-standard-deviation-tells-us-how-much-traffic-normally-varies-if-traffic-is-usually-stable-std-will-be-low-if-traffic-is-naturally-spiky-std-will-be-higher-baseline-calculation-example-if-normal-traffic-is-around-10-req-s-mean-10-std-2-if-suddenly-traffic-becomes-30-req-s-z-30-10-2-10-that-is-extremely-abnormal-z-score-detection-the-tool-flags-anomalies-using-the-z-score-formula-z-current-rate-mean-std-if-z-3-0-then-the-traffic-is-anomalous-multiplier-rule-sometimes-stddev-can-be-large-during-peak-times-so-the-system-also-uses-a-multiplier-rule-current-rate-mean-5-this-catches-huge-spikes-even-if-stddev-is-high-detecting-error-surges-4xx-5xx-attack-traffic-often-generates-many-errors-for-example-brute-force-login-attempts-401-403-scanning-endpoints-404-broken-exploit-attempts-500-so-i-track-errors-per-ip-if-an-ip-generates-too-many-errors-ip-error-rate-baseline-error-rate-3-then-detection-becomes-stricter-blocking-malicious-ips-with-iptables-when-an-ip-is-confirmed-anomalous-the-system-blocks-it-with-bash-iptables-a-input-s-ip-j-drop-this-rule-immediately-drops-all-traffic-from-that-ip-in-python-python-cmd-iptables-a-input-s-ip-j-drop-subprocess-run-cmd-check-false-auto-unban-strategy-backoff-schedule-permanent-bans-are-dangerous-because-false-positives-can-happen-so-the-tool-uses-an-escalating-backoff-schedule-strike-ban-duration-1st-ban-10-minutes-2nd-ban-30-minutes-3rd-ban-2-hours-4th-ban-permanent-this-is-fair-because-accidental-spikes-get-forgiven-repeated-abuse-gets-permanently-blocked-slack-notifications-the-system-sends-slack-alerts-for-global-anomaly-detected-ip-banned-ip-unbanned-alerts-include-current-rate-baseline-mean-stddev-z-score-timestamp-ban-duration-example-slack-message-ip-banned-203-0-113-10-condition-ip-z-4-12-rate-20-30-req-s-baseline-mean-3-20-std-1-10-ban-duration-10-minutes-live-monitoring-dashboard-a-flask-dashboard-runs-on-port-5000-and-is-served-publicly-via-a-domain-it-refreshes-every-3-seconds-and-shows-global-req-s-baseline-mean-stddev-cpu-usage-memory-usage-uptime-top-10-ips-by-traffic-currently-banned-ips-this-dashboard-is-what-the-graders-use-during-evaluation-audit-logging-every-major-action-is-written-to-an-audit-log-file-timestamp-action-ip-condition-rate-baseline-duration-examples-2026-04-28t14-15-19z-ban-172-18-0-1-ip-z-3-02-rate-4-02-baseline-1-00-duration-10-2026-04-28t14-25-24z-unban-172-18-0-1-expired-rate-0-00-baseline-0-00-duration-10m-this-is-important-for-security-because-audit-logs-provide-traceability-testing-with-apachebench-to-simulate-ddos-traffic-i-used-apachebench-bash-ab-n-20000-c-500-http-100-27-253-179-8080-this-creates-thousands-of-requests-at-high-concurrency-the-detector-immediately-flagged-anomalies-and-blocked-the-abusive-ip-baseline-graph-to-prove-the-baseline-adapts-over-time-i-created-a-script-that-reads-baseline-recalculation-logs-and-plots-the-baseline-mean-over-time-the-graph-clearly-shows-different-effective-means-at-different-time-periods-this-proves-the-system-is-learning-traffic-patterns-dynamically-key-lessons-learned-this-project-taught-me-important-devsecops-concepts-traffic-baselining-is-better-than-hardcoded-thresholds-sliding-window-tracking-provides-real-time-visibility-anomaly-detection-can-be-built-with-simple-statistics-iptables-is-powerful-for-blocking-attackers-instantly-monitoring-dashboards-make-security-tooling-more-usable-conclusion-this-project-demonstrates-how-to-build-a-real-time-security-monitoring-tool-using-nginx-json-logs-python-deque-sliding-windows-rolling-baselines-mean-stddev-z-score-anomaly-detection-iptables-banning-slack-alerting-flask-monitoring-dashboard-even-though-this-is-a-beginner-friendly-project-the-ideas-are-very-close-to-how-real-production-monitoring-and-security-detection-systems-work-github-repository-https-github-com-mosesajayi458-pixel-hng14-stage3-devops-https-github-com-mosesajayi458-pixel-hng14-stage3-devops-author-hng-internship-stage-3-submission-olowookere-damilola-devsecops-track

---

# 🔗 GitHub Repository

[https://github.com/mosesajayi458-pixel/hng14-stage3-devops](https://github.com/mosesajayi458-pixel/hng14-stage3-devops)

---

# 👨‍💻 Author

Olowookere Damilola
DevOps / DevSecOps Track

````

---

