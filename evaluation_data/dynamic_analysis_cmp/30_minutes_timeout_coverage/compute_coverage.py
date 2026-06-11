import argparse
import json
import re
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Parse lines like:
# 03-13 20:22:37.523  7424  7424 D GAPS    : METHOD=<a2dp.Vol.main: void onCreate(android.os.Bundle)>
TS_PATTERN = re.compile(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)")
METHOD_PATTERN = re.compile(r"METHOD=(.+)")

TOOL_CONFIG = {
    "ape": {
        "runs": ["output_run1", "output_run2", "output_run3"],
        "title": "APE",
    },
    "goalexplorer": {
        "runs": ["output_run1", "output_run2", "output_run3"],
        "title": "GoalExplorer",
    },
    "guardian": {
        "runs": ["output_run1", "output_run2", "output_run3"],
        "title": "Guardian",
    },
}


def parse_time(ts: str) -> float:
    # "03-13 20:22:37.523" -> seconds in day
    _, time_part = ts.split()
    h, m, s = time_part.split(":")
    s, ms = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def extract_methods(log_path: Path):
    """
    Extract cumulative method-hit events from one .apk.log file.
    Restart blocks remain part of the same run, exactly as in the user's setup.
    """
    events = []
    first_ts = None

    with log_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ts_match = TS_PATTERN.search(line)
            meth_match = METHOD_PATTERN.search(line)
            if not ts_match or not meth_match:
                continue

            t_abs = parse_time(ts_match.group(1))
            if first_ts is None:
                first_ts = t_abs

            t_rel = t_abs - first_ts
            if t_rel < 0:
                # Defensive: skip weird wraparound / malformed ordering
                continue

            method_id = meth_match.group(1).strip()
            events.append((t_rel, method_id))

    return events


def infer_package_from_events(events, max_samples=200):
    counts = {}
    for _, method_id in events[:max_samples]:
        class_part = method_id.split(":", 1)[0].strip("<>")
        if "." not in class_part:
            continue
        pkg = ".".join(class_part.split(".")[:-1])
        if pkg:
            counts[pkg] = counts.get(pkg, 0) + 1

    if not counts:
        return ""

    return max(counts, key=counts.get)


def load_stats(stats_path: Path):
    with stats_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    by_apk = {}
    by_pkg = {}
    for app in data.get("apps", []):
        apk_path = app.get("apk", "")
        if apk_path:
            by_apk[Path(apk_path).name] = app
        pkg = app.get("package")
        if pkg:
            by_pkg[pkg] = app

    return by_apk, by_pkg


def resolve_denominator(log_name, events, by_apk, by_pkg):
    apk_name = log_name
    if apk_name.endswith(".log"):
        apk_name = apk_name[:-4]

    app = by_apk.get(apk_name)
    if app:
        return app, app.get("methods_total", 0)

    pkg = infer_package_from_events(events)
    if pkg in by_pkg:
        return by_pkg[pkg], by_pkg[pkg].get("methods_total", 0)

    return None, 0


def build_curve(events, denominator, times):
    """
    Coverage(t) = unique methods seen up to t / denominator
    """
    events = sorted(events, key=lambda x: x[0])
    seen = set()
    curve = []
    idx = 0

    for t in times:
        while idx < len(events) and events[idx][0] <= t:
            seen.add(events[idx][1])
            idx += 1

        if denominator:
            cov = 100.0 * len(seen) / denominator
            curve.append(min(100.0, cov))
        else:
            curve.append(0.0)

    return np.array(curve, dtype=float)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute average time-vs-coverage curves using androtest_stats.json denominators."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Tool directory containing output_run folders",
    )
    parser.add_argument(
        "--tool",
        type=str,
        choices=sorted(TOOL_CONFIG.keys()),
        help="Tool name (ape, goalexplorer, guardian)",
    )
    parser.add_argument(
        "--runs",
        nargs="+",
        default=None,
        help="Run folders (overrides tool defaults)",
    )
    parser.add_argument(
        "--stats",
        type=str,
        default="",
        help="Path to androtest_stats.json (default: ../androtest_stats.json)",
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=1800,
        help="Maximum analysis time in seconds (default 1800 = 30 min)",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=1,
        help="Sampling step in seconds",
    )
    parser.add_argument(
        "--save-run-curves",
        action="store_true",
        help="Also save the 3 average run curves in a secondary plot",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root)

    tool = args.tool
    if tool is None:
        if root.name in TOOL_CONFIG:
            tool = root.name
        else:
            raise SystemExit(
                "--tool is required when root folder name is not a known tool."
            )

    tool_cfg = TOOL_CONFIG[tool]
    run_folders = args.runs or tool_cfg["runs"]
    title = tool_cfg["title"]

    stats_path = (
        Path(args.stats)
        if args.stats
        else root.parent / "androtest_stats.json"
    )
    if not stats_path.is_file():
        raise SystemExit(f"Stats file not found: {stats_path}")

    by_apk, by_pkg = load_stats(stats_path)
    times = np.arange(0, args.max_time + 1, args.step)

    # 1) Read all logs, grouped by app and run
    run_events = {}
    missing_stats = set()

    for run_folder in run_folders:
        folder = root / run_folder
        logs = sorted(folder.glob("*.apk.log"))
        print(f"Scanning {run_folder}: {len(logs)} apps")
        run_events[run_folder] = {}

        for log_path in logs:
            events = extract_methods(log_path)
            app, denom = resolve_denominator(
                log_path.name, events, by_apk, by_pkg
            )
            if not denom:
                missing_stats.add(log_path.name)
                continue

            run_events[run_folder][log_path.name] = {
                "events": events,
                "denom": denom,
                "app": app,
            }

    # 2) Average over apps, separately for each run
    run_avg_curves = []
    run_avg_map = {}

    for run_folder in run_folders:
        app_curves = []
        for data in run_events[run_folder].values():
            curve = build_curve(data["events"], data["denom"], times)
            app_curves.append(curve)

        if app_curves:
            avg_curve = np.mean(app_curves, axis=0)
            run_avg_curves.append(avg_curve)
            run_avg_map[run_folder] = avg_curve
            print(
                f"Processed {run_folder}: averaged {len(app_curves)} app curves"
            )
        else:
            print(f"Warning: no valid app curves in {run_folder}")

    if not run_avg_curves:
        raise RuntimeError("No valid data found.")

    if missing_stats:
        print(f"Warning: {len(missing_stats)} apps missing stats (skipped).")

    # 3) Final average over runs
    final_avg = np.mean(run_avg_curves, axis=0)

    # 4) Save CSV
    csv_path = root / f"{tool}_runs.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        header = ["time_seconds", "time_minutes"]
        for run_folder in run_folders:
            if run_folder in run_avg_map:
                header.append(f"{run_folder}_avg")
        header.append("final_avg")
        f.write(",".join(header) + "\n")

        for i, t in enumerate(times):
            row = [str(int(t)), f"{t/60.0:.6f}"]
            for run_folder in run_folders:
                if run_folder in run_avg_map:
                    row.append(f"{run_avg_map[run_folder][i]:.6f}")
            row.append(f"{final_avg[i]:.6f}")
            f.write(",".join(row) + "\n")

    # 5) Final plot
    final_pdf = root / f"{tool}_runs.pdf"
    plt.figure(figsize=(10, 6))
    plt.plot(times / 60.0, final_avg, linewidth=3, label="Final average")
    max_val = float(np.max(final_avg))
    plt.axhline(
        y=max_val, linestyle=":", color="gray", label=f"Max {max_val:.2f}%"
    )
    plt.xlabel("Time (minutes)")
    plt.ylabel(f"Coverage (%) — max {max_val:.2f}%")
    plt.title(f"Average Coverage from {title} ({len(run_folders)} runs)")
    plt.xlim(0, args.max_time / 60.0)
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(final_pdf, dpi=200)

    # 6) Optional debug plot with the run-average curves
    if args.save_run_curves:
        debug_pdf = root / f"{tool}_run_average_curves_from_my_runs.pdf"
        plt.figure(figsize=(10, 6))
        for run_folder, curve in run_avg_map.items():
            plt.plot(times / 60.0, curve, label=run_folder)
        max_debug = float(np.max(list(run_avg_map.values())))
        plt.axhline(
            y=max_debug,
            linestyle=":",
            color="gray",
            label=f"Max {max_debug:.2f}%",
        )
        plt.xlabel("Time (minutes)")
        plt.ylabel(f"Coverage (%) — max {max_debug:.2f}%")
        plt.title("Average Coverage per Run (debug)")
        plt.xlim(0, args.max_time / 60.0)
        plt.ylim(0, 100)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(debug_pdf, dpi=200)
        print(f"Saved debug run plot to: {debug_pdf}")

    print(f"Saved final plot to: {final_pdf}")
    print(f"Saved CSV to:       {csv_path}")
    plt.show()


if __name__ == "__main__":
    main()
