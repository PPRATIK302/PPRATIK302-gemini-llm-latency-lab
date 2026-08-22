"""Create simple charts from saved benchmark CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    results_dir = Path("results")
    csv_files = sorted(results_dir.glob("*.csv"))
    if not csv_files:
        raise SystemExit("No CSV benchmark files found in results/. Run scripts/run_benchmark.py first.")
    frame = pd.read_csv(csv_files[-1])
    chart_path = results_dir / "latency-summary.png"
    frame["total_latency_ms"].plot(kind="line", title="Total Latency by Request")
    plt.ylabel("ms")
    plt.tight_layout()
    plt.savefig(chart_path)
    print(f"Saved chart: {chart_path}")


if __name__ == "__main__":
    main()

