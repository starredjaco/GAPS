import os
import json
import csv

# Define paths
base_dir = "/home/same/code/gaps/static_analysis_cmp/DroidReach/results"
output_csv = (
    "/home/same/code/gaps/static_analysis_cmp/stats_droidreach_androguard.csv"
)
time_stats_csv = (
    "/home/same/code/gaps/static_analysis_cmp/DroidReach/time_stats.csv"
)

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
    androtest_path = os.path.join(
        "/home/same/code/gaps/AndroLog/androtest", f"{app_name}.apk"
    )
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
