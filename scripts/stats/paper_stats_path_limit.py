import csv
import os

stats_files = [
    "stats-l 500.csv",
    "stats-l 1000.csv",
    "stats-l 2000.csv",
    "stats-l 5000.csv",
    "stats-l 10000.csv",
    "stats-l 20000.csv",
    "stats-up.csv",
]

stats_dir = "path_limit"

tot_runs = 5
tot_apps = 64

stats = {}

paper_table_fields = [
    "Path Limit",
    "OOMs",
    "Analysis Time",
    "Paths reconstructed",
]

paper_table_writer = csv.DictWriter(
    open(os.path.join(stats_dir, "paper_table.csv"), "w"),
    fieldnames=paper_table_fields,
)


paper_table_row = {}
i = 0
for paper_table_field in paper_table_fields:
    paper_table_row[paper_table_field] = paper_table_field
    i += 1

paper_table_writer.writerow(paper_table_row)

fields = [
    "APP",
    "TIME",
    "REACHED METHODS",
    "TOT. REACHABLE PATHS",
    "REACHABLE CONDITIONAL PATHS",
    "AVG. REACHABLE PATHS",
    "UNIQUE PATHS",
]

for stats_file in stats_files:
    stats_row = ["", "", "", ""]
    stats_file_split = stats_file.split()
    if len(stats_file_split) > 1:
        stats_row[0] = stats_file_split[1].split(".csv")[0]
    else:
        stats_row[0] = "No limit"
    sum_all_runs = [0, 0, 0]
    file_path = os.path.join(stats_dir, stats_file)
    with open(file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        analyzed_apps = 0
        sums_run = [0, 0, 0]
        run_n = 0
        for i, row in enumerate(reader):
            if i == 0:
                continue
            if row["APP"] == "a2dpvolume" and i > 1:
                print(run_n)
                run_n += 1
                if analyzed_apps < tot_apps:
                    sums_run[0] = tot_apps - analyzed_apps
                    print(sums_run[0])
                sum_all_runs[0] += sums_run[0]
                sums_run[1] /= analyzed_apps
                # sums_run[2] /= analyzed_apps
                sum_all_runs[1] += sums_run[1]
                sum_all_runs[2] += sums_run[2]
                analyzed_apps = 0
                sums_run = [0, 0, 0]

            analyzed_apps += 1
            sums_run[1] += float(row["TIME"])
            sums_run[2] += int(row["TOT. REACHABLE PATHS"])
        print(run_n)
        if analyzed_apps < tot_apps:
            sums_run[0] = tot_apps - analyzed_apps
            print(sums_run[0])
        sum_all_runs[0] += sums_run[0]
        sums_run[1] /= analyzed_apps
        # sums_run[2] /= analyzed_apps
        sum_all_runs[1] += sums_run[1]
        sum_all_runs[2] += sums_run[2]
        analyzed_apps = 0
        sums_run = [0, 0, 0]
    avg_all_runs = [0, 0, 0]
    for i, sum_val in enumerate(sum_all_runs):
        avg_all_runs[i] = sum_val / tot_runs
        avg_all_runs[i] = "{:.2f}".format(float(avg_all_runs[i]))
        stats_row[i + 1] = avg_all_runs[i]
    paper_table_row = {}
    i = 0
    for paper_table_field in paper_table_fields:
        paper_table_row[paper_table_field] = stats_row[i]
        i += 1
    paper_table_writer.writerow(paper_table_row)
