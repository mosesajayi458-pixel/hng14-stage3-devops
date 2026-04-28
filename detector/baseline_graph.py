import matplotlib.pyplot as plt
import time
import os


def parse_audit_log(filepath):
    timestamps = []
    means = []

    if not os.path.exists(filepath):
        print(f"[ERROR] Audit log not found: {filepath}")
        return timestamps, means

    with open(filepath, "r") as f:
        for line in f:
            if "BASELINE_RECALC" in line:
                try:
                    # Example line:
                    # [2026-04-28T01:10:00Z] BASELINE_RECALC global | recalculated | rate=0.00 | baseline=12.30 | duration=N/A
                    parts = line.split("]")
                    ts = parts[0].replace("[", "").strip()

                    baseline_part = line.split("baseline=")[1]
                    baseline_value = float(baseline_part.split("|")[0].strip())

                    timestamps.append(ts)
                    means.append(baseline_value)
                except Exception:
                    continue

    return timestamps, means


def plot_baseline(timestamps, means, output_file="Baseline-graph.png"):
    if len(means) < 2:
        print("[ERROR] Not enough baseline data to plot.")
        return

    # Convert timestamps to simple index-based X axis
    x = list(range(len(means)))

    plt.figure(figsize=(12, 6))
    plt.plot(x, means, marker="o")
    plt.title("Baseline Mean Over Time (Hourly Slots Effect)")
    plt.xlabel("Baseline Recalculation Point")
    plt.ylabel("Effective Mean (req/s)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_file)

    print(f"[SUCCESS] Baseline graph saved as {output_file}")


if __name__ == "__main__":
    audit_file = "audit.log"

    timestamps, means = parse_audit_log(audit_file)

    print(f"[INFO] Found {len(means)} baseline recalculation points")

    plot_baseline(timestamps, means)
