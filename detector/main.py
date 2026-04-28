import threading
from monitor import follow_log
from baseline import BaselineManager
from detector import AnomalyDetector
from notifier import SlackNotifier
from unbanner import UnbanManager
from dashboard import run_dashboard
from config_loader import load_config
from audit_logger import AuditLogger


def main():
    config = load_config("config.yaml")

    audit = AuditLogger("audit.log")
    notifier = SlackNotifier(config["slack_webhook"])

    baseline_mgr = BaselineManager(config, audit_logger=audit)
    detector = AnomalyDetector(config, baseline_mgr, notifier, audit)

    unban_mgr = UnbanManager(config, detector.blocker, notifier, audit)

    threading.Thread(target=baseline_mgr.recalc_loop, daemon=True).start()
    threading.Thread(target=unban_mgr.loop, daemon=True).start()
    threading.Thread(target=run_dashboard, args=(config, detector, baseline_mgr), daemon=True).start()

    print("[INFO] Detector daemon started...")

    for entry in follow_log(config["log_file"]):
        detector.process_log_entry(entry)


if __name__ == "__main__":
    main()
