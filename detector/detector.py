import time
from collections import defaultdict, deque
from blocker import Blocker


class AnomalyDetector:
    def __init__(self, config, baseline_mgr, notifier, audit_logger):
        self.config = config
        self.baseline_mgr = baseline_mgr
        self.notifier = notifier
        self.audit = audit_logger

        self.global_window = deque()
        self.ip_windows = defaultdict(deque)
        self.ip_error_window = defaultdict(deque)

        self.blocker = Blocker()

        self.current_second = int(time.time())
        self.second_count = 0

        self.last_global_alert = 0
        self.global_alert_cooldown = 60

    def cleanup_deque(self, dq, now, window=60):
        while dq and dq[0] < now - window:
            dq.popleft()

    def global_rate(self):
        return len(self.global_window) / 60

    def ip_rate(self, ip):
        return len(self.ip_windows[ip]) / 60

    def get_top_ips(self, limit=10):
        rates = [(ip, len(dq)) for ip, dq in self.ip_windows.items()]
        rates.sort(key=lambda x: x[1], reverse=True)
        return [(ip, count / 60) for ip, count in rates[:limit]]

    def process_log_entry(self, entry):
        now = time.time()

        ip = entry.get("source_ip") or entry.get("remote_addr") or "unknown"
        if isinstance(ip, str) and ip.strip() == "":
            ip = entry.get("remote_addr") or "unknown"

        status = int(entry.get("status", 200))

        self.global_window.append(now)
        self.cleanup_deque(self.global_window, now)

        self.ip_windows[ip].append(now)
        self.cleanup_deque(self.ip_windows[ip], now)

        if status >= 400:
            self.ip_error_window[ip].append(now)
            self.cleanup_deque(self.ip_error_window[ip], now)

        sec = int(now)
        if sec != self.current_second:
            self.baseline_mgr.record_second_count(self.second_count)
            self.second_count = 0
            self.current_second = sec

        self.second_count += 1

        self.detect(ip)

    def detect(self, ip):
        mean = self.baseline_mgr.global_mean
        std = self.baseline_mgr.global_std

        z_thresh = self.config["thresholds"]["zscore"]
        mult_thresh = self.config["thresholds"]["multiplier"]

        global_rate = self.global_rate()
        ip_rate = self.ip_rate(ip)

        global_z = (global_rate - mean) / std
        ip_z = (ip_rate - mean) / std

        # Error tightening
        ip_error_rate = len(self.ip_error_window[ip]) / 60
        baseline_error_rate = mean * 0.1

        if baseline_error_rate > 0 and ip_error_rate > baseline_error_rate * self.config["thresholds"]["error_multiplier"]:
            z_thresh = 2.5
            mult_thresh = 3.0

        # GLOBAL anomaly -> Slack only
        if global_z > z_thresh or global_rate > mean * mult_thresh:
            if time.time() - self.last_global_alert > self.global_alert_cooldown:
                self.last_global_alert = time.time()

                msg = (
                    f"🚨 GLOBAL ANOMALY DETECTED\n"
                    f"Rate: {global_rate:.2f} req/s\n"
                    f"Baseline mean: {mean:.2f}, std: {std:.2f}\n"
                    f"Z-score: {global_z:.2f}\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                )
                self.notifier.send(msg)
                self.audit.log("GLOBAL_ALERT", "global", "global spike", global_rate, mean, "N/A")

        # IP anomaly -> BAN
        if ip != "unknown" and (ip_z > z_thresh or ip_rate > mean * mult_thresh):
            if not self.blocker.is_banned(ip):

                strike = self.blocker.get_strike(ip)

                if strike == 0:
                    duration = self.config["unban_schedule_minutes"][0]
                elif strike == 1:
                    duration = self.config["unban_schedule_minutes"][1]
                elif strike == 2:
                    duration = self.config["unban_schedule_minutes"][2]
                else:
                    duration = "PERMANENT"

                condition = f"ip_z={ip_z:.2f} or ip_rate={ip_rate:.2f}"

                self.blocker.increment_strike(ip)
                stage = strike

                banned = self.blocker.ban_ip(ip, duration, condition, stage)

                if banned:
                    msg = (
                        f"⛔ IP BANNED: {ip}\n"
                        f"Condition: {condition}\n"
                        f"Rate: {ip_rate:.2f} req/s\n"
                        f"Baseline mean: {mean:.2f}, std: {std:.2f}\n"
                        f"Ban duration: {duration}\n"
                        f"Strike stage: {stage}\n"
                        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                    )
                    self.notifier.send(msg)

                    self.audit.log(
                        action="BAN",
                        ip=ip,
                        condition=condition,
                        rate=ip_rate,
                        baseline=mean,
                        duration=str(duration)
                    )
