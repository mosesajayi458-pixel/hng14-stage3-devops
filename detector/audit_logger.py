import time


class AuditLogger:
    def __init__(self, logfile="audit.log"):
        self.logfile = logfile

    def log(self, action, ip, condition, rate, baseline, duration="N/A"):
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        line = f"[{ts}] {action} {ip} | {condition} | rate={rate:.2f} | baseline={baseline:.2f} | duration={duration}\n"
        with open(self.logfile, "a") as f:
            f.write(line)
