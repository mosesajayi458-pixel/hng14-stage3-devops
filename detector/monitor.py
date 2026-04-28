import time
import json

def follow_log(log_path):
    with open(log_path, "r") as f:
        f.seek(0, 2)  # move to end

        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue

            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                yield data
            except Exception:
                continue
