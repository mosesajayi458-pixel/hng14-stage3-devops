**🚀 HNG Stage 3 – Real-Time Anomaly & DDoS Detection Engine (DevSecOps)**

This project implements a real-time anomaly detection system designed to monitor and protect a publicly accessible Nextcloud deployment.
The system continuously analyzes incoming HTTP traffic using Nginx access logs, learns normal behavior dynamically, detects abnormal spikes, and automatically mitigates threats by blocking malicious IPs using iptables.
It also provides a live monitoring dashboard and Slack-based alerting system for real-time visibility.

🌐 Live Deployment


Server IP: 100.27.253.179


Nextcloud URL: http://100.27.253.179:8080


Live Metrics Dashboard: http://hngmetrics.duckdns.org



🧠 Why Python?
Python was chosen for the following reasons:


Fast and efficient development for security tooling


Built-in data structures like deque for sliding window operations


Easy integration with system tools (iptables) and APIs (Slack webhooks)


Strong ecosystem for monitoring and data processing



🏗️ System Architecture
The solution is deployed using Docker Compose with three core services:
1. Nextcloud Container


Image: kefaslungu/hng-nextcloud


Hosts the application


Not modified (as required)


2. Nginx Reverse Proxy


Acts as the public entry point


Forwards traffic to Nextcloud


Logs all requests in structured JSON format


3. Detector Daemon (Core Engine)


Continuously tails Nginx logs


Computes real-time traffic metrics


Learns baseline behavior dynamically


Detects anomalies (global + per-IP)


Blocks malicious IPs using iptables


Sends Slack alerts


Hosts a live monitoring dashboard



📦 Shared Logging (Named Volume)
All Nginx logs are written to a Docker named volume:
HNG-nginx-logs
Usage:


Nginx → writes logs (read/write)


Detector → reads logs (read-only)


Nextcloud → reads logs (read-only)


This ensures:


Persistence


Safe sharing between containers


Real-time monitoring without interference



📊 Sliding Window Traffic Analysis (60 Seconds)
The system uses a sliding window approach to calculate real-time request rates.
Implementation


Uses collections.deque


Stores timestamps of incoming requests


Removes entries older than 60 seconds


Metrics


Global Rate: len(global_window) / 60


Per-IP Rate: len(ip_window[ip]) / 60


Why deque?


O(1) append and removal


Ideal for real-time streaming data



📈 Rolling Baseline Learning (30 Minutes)
The system dynamically learns “normal” traffic behavior.
How It Works


Counts requests per second


Stores last 1800 seconds (30 minutes)


Recalculates every 60 seconds


Metrics Computed


Mean (average traffic)


Standard deviation (traffic variation)


Hour-Based Optimization


Baselines are grouped per hour


Prevents off-peak data affecting peak-time detection


Safety Floors


Minimum mean = 1.0


Minimum stddev = 1.0


Prevents:


Division by zero


False positives



🚨 Anomaly Detection Logic
An anomaly is triggered if either condition is met:
1. Z-Score Detection
z = (current_rate - mean) / std


Trigger if: z > 3.0


2. Multiplier Rule
current_rate > mean * 5
This ensures detection of both:


Statistical anomalies


Sudden traffic spikes



⚠️ Error Surge Detection (Adaptive Sensitivity)
The system monitors error responses (4xx/5xx).
If an IP shows abnormal error behavior:
ip_error_rate > baseline_error_rate * 3
Then detection becomes stricter:


Z-score threshold → reduced (e.g. 2.5)


Multiplier → reduced (e.g. 3×)


This allows faster detection of malicious activity.

🔒 Automated IP Blocking (iptables)
When a per-IP anomaly is detected:
iptables -A INPUT -s <ip> -j DROP
Why iptables?


Blocks traffic at kernel level


Prevents load on application


Immediate and efficient mitigation



🔁 Ban Escalation & Auto-Unban
Each IP follows a progressive penalty system:
StrikeDuration1st10 minutes2nd30 minutes3rd2 hours4th+Permanent
Auto-Unban


System tracks ban time and duration


Automatically removes expired bans


Sends Slack notification on unban



🔔 Slack Notifications
Real-time alerts are sent for:


Global anomalies


IP bans


IP unbans


Each alert includes:


Trigger condition


Request rate


Baseline values


Timestamp


Ban duration (if applicable)



🔐 Note: Webhook URLs are excluded from the repository for security.


📺 Live Metrics Dashboard
Accessible at:
http://hngmetrics.duckdns.org
Features


Refreshes every 3 seconds


Displays:


System uptime


Global request rate


Baseline mean & stddev


CPU & memory usage


Active banned IPs


Top 10 IPs by traffic





📝 Audit Logging
All system actions are logged in structured format:
[timestamp] ACTION ip | condition | rate | baseline | duration
Logged Events


BASELINE_RECALC


GLOBAL_ALERT


BAN


UNBAN


📍 Location:
detector/audit.log

📁 Project Structure
detector/  main.py  monitor.py  baseline.py  detector.py  blocker.py  unbanner.py  notifier.py  dashboard.py  baseline_graph.py  config.yaml  requirements.txtnginx/  nginx.confdocs/  architecture.pngscreenshots/  Tool-running.png  Ban-slack.png  Unban-slack.png  Global-alert-slack.png  Iptables-banned.png  Audit-log.png  Baseline-graph.pngdocker-compose.ymlREADME.md

🧪 Testing (Attack Simulation)
Simulate high traffic using ApacheBench:
ab -n 20000 -c 500 http://100.27.253.179:8080/
Verification Steps


Check Slack alerts


Check audit logs


Confirm blocked IPs:


docker exec -it detector iptables -L INPUT -n --line-numbers

📈 Baseline Graph Generation
Generate baseline visualization:
docker exec -it detector python baseline_graph.py
Copy output:
docker cp detector:/app/Baseline-graph.png ./screenshots/Baseline-graph.png

🛠️ Setup Instructions (Fresh VPS)
1. Update System
sudo apt update && sudo apt upgrade -y
2. Install Docker
sudo apt install -y docker.io docker-composesudo systemctl enable dockersudo systemctl start dockersudo usermod -aG docker ubuntunewgrp docker
3. Clone Repository
git clone git@github.com:mosesajayi458-pixel/hng14-stage3-devops.gitcd hng14-stage3-devops
4. Start Services
docker-compose up -d --build
5. Verify
docker pscurl -I http://localhost:8080curl http://localhost:5000docker logs -f detector

📝 Blog Post
https://medium.com/@mosesajayi458/building-a-real-time-anomaly-detection-engine-ddos-detection-tool-with-python-nginx-logs-and-83af63bd8bcf

🔗 GitHub Repository
https://github.com/mosesajayi458-pixel/hng14-stage3-devops

👨‍💻 Author
Olowookere Damilola
DevOps / DevSecOps Track
✅ Turn this into a 1-page cheat sheet for defense
✅ Or simulate a live panel interview (hard questions)
✅ Or help you tighten your spoken explanation (1–2 min pitch)
