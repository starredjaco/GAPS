import os
import json
import csv
import argparse


def main(base_dir, dataset_dir, output_csv, time_stats_csv):
    # Load time stats into a dict: {app_name: time_value}
    time_stats = {}
    with open(time_stats_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            app = row["App"]
            time = row.get("Droidreach (Androguard) time", "")
            time_stats[app] = time

    # Prepare data collection
    stats = []

    # Iterate over each app directory
    for app_name in os.listdir(base_dir):
        app_dir = os.path.join(base_dir, app_name)
        androtest_path = os.path.join(dataset_dir, f"{app_name}.apk")
        if os.path.isdir(app_dir) and os.path.exists(androtest_path):
            json_path = os.path.join(app_dir, "androguard_paths_fe.json")
            if os.path.isfile(json_path):
                try:
                    with open(json_path, "r") as f:
                        data = json.load(f)
                    num_keys = len(data["paths"].keys())
                except Exception:
                    num_keys = "error"
            else:
                num_keys = "missing"
            time_val = time_stats.get(app_name, "")
            stats.append(
                {
                    "app": app_name,
                    "Reached Methods": num_keys,
                    "Analysis time": time_val,
                }
            )

    # Compute averages (ignore "error", "missing", "")
    def safe_float(val):
        try:
            return float(val)
        except Exception:
            return None

    key_vals = [safe_float(row["Reached Methods"]) for row in stats]
    key_vals = [v for v in key_vals if v is not None]
    avg_keys = sum(key_vals) / len(key_vals) if key_vals else ""

    time_vals = [safe_float(row["Analysis time"]) for row in stats]
    time_vals = [v for v in time_vals if v is not None]
    avg_time = sum(time_vals) / len(time_vals) if time_vals else ""

    # Write to CSV
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = [
            "app",
            "Reached Methods",
            "Analysis time",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in stats:
            writer.writerow(row)
        # Write average row
        writer.writerow(
            {
                "app": "AVERAGE",
                "Reached Methods": avg_keys,
                "Analysis time": avg_time,
            }
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check DroidReach reachability stats."
    )
    parser.add_argument(
        "--base_dir",
        required=True,
        help="Base directory for DroidReach results",
    )
    parser.add_argument(
        "--dataset_dir",
        required=True,
        help="Base directory for dataset",
    )
    parser.add_argument(
        "--output_csv", required=True, help="Output CSV file path"
    )
    parser.add_argument(
        "--time_stats_csv", required=True, help="CSV file with time stats"
    )
    args = parser.parse_args()
    main(args.base_dir, args.dataset_dir, args.output_csv, args.time_stats_csv)
