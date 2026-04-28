import time
import statistics
from collections import deque
from datetime import datetime


class BaselineManager:
    def __init__(self, config, audit_logger=None):
        self.window_seconds = config["baseline"]["window_minutes"] * 60
        self.recalc_interval = config["baseline"]["recalc_interval_seconds"]

        self.global_counts = deque(maxlen=self.window_seconds)
        self.hourly_counts = {}

        self.global_mean = 1.0
        self.global_std = 1.0

        self.audit = audit_logger

        # store baseline mean history for graphing
        self.mean_history = deque(maxlen=5000)
        self.std_history = deque(maxlen=5000)

    def record_second_count(self, count):
        self.global_counts.append(count)

        hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
        if hour not in self.hourly_counts:
            self.hourly_counts[hour] = deque(maxlen=self.window_seconds)

        self.hourly_counts[hour].append(count)

    def compute_stats(self, data):
        if len(data) < 30:
            return 1.0, 1.0

        mean = statistics.mean(data)
        std = statistics.pstdev(data)

        if std == 0:
            std = 1.0
        if mean < 1:
            mean = 1.0

        return mean, std

    def recalc(self):
        hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
        current_hour_data = self.hourly_counts.get(hour, [])

        # prefer current hour if enough data
        if len(current_hour_data) > 300:
            mean, std = self.compute_stats(current_hour_data)
        else:
            mean, std = self.compute_stats(self.global_counts)

        self.global_mean = mean
        self.global_std = std

        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.mean_history.append((ts, mean))
        self.std_history.append((ts, std))

        if self.audit:
            self.audit.log(
                action="BASELINE_RECALC",
                ip="global",
                condition="recalculated",
                rate=0,
                baseline=mean,
                duration="N/A"
            )

        print(f"[BASELINE] mean={mean:.2f} std={std:.2f}")

    def recalc_loop(self):
        while True:
            time.sleep(self.recalc_interval)
            self.recalc()
