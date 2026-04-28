import subprocess
import time


class Blocker:
    def __init__(self):
        self.banned = {}   # ip -> ban info
        self.strikes = {}  # ip -> strike count

    def is_banned(self, ip):
        return ip in self.banned

    def get_strike(self, ip):
        return self.strikes.get(ip, 0)

    def increment_strike(self, ip):
        current = self.get_strike(ip)
        self.strikes[ip] = current + 1
        return self.strikes[ip]

    def ban_ip(self, ip, duration_minutes, reason, stage):
        if self.is_banned(ip):
            return False

        # Insert rule at the TOP so it takes effect immediately
        cmd = ["iptables", "-I", "INPUT", "1", "-s", ip, "-j", "DROP"]
        subprocess.run(cmd, check=False)

        self.banned[ip] = {
            "ban_time": time.time(),
            "duration": duration_minutes,
            "reason": reason,
            "stage": stage
        }
        return True

    def unban_ip(self, ip):
        # Remove rule
        cmd = ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
        subprocess.run(cmd, check=False)

        if ip in self.banned:
            del self.banned[ip]
