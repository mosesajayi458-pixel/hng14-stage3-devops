import time


class UnbanManager:
    def __init__(self, config, blocker, notifier, audit_logger):
        self.schedule = config["unban_schedule_minutes"]
        self.blocker = blocker
        self.notifier = notifier
        self.audit = audit_logger

    def loop(self):
        while True:
            time.sleep(5)
            now = time.time()

            for ip, info in list(self.blocker.banned.items()):
                ban_time = info["ban_time"]
                duration = info["duration"]

                # Permanent bans have duration "PERMANENT"
                if duration == "PERMANENT":
                    continue

                if now - ban_time >= (duration * 60):
                    self.blocker.unban_ip(ip)

                    msg = (
                        f"✅ IP UNBANNED: {ip}\n"
                        f"Previous reason: {info.get('reason')}\n"
                        f"Previous ban duration: {duration} minutes\n"
                        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                    )
                    self.notifier.send(msg)

                    self.audit.log(
                        action="UNBAN",
                        ip=ip,
                        condition=info.get("reason", "N/A"),
                        rate=0,
                        baseline=0,
                        duration=f"{duration}m"
                    )

                    print(f"[UNBAN] Released {ip}")
