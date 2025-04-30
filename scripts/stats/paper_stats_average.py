import csv
import os
import subprocess

stats_files = [
    "stats-l 5000.csv",
]

stats_dir = ".."
app_directory = "app_examples/"

tot_runs = 5
tot_apps = 64

stats = {}

paper_table_fields = [
    "App",
    "Time",
    "Reachable Methods",
    "Avg. Paths",
    "PoR",
]

paper_table_writer = csv.DictWriter(
    open("paper_table.csv", "w"),
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
    stats_row = ["", "", "", "", ""]
    dict_sums = {}
    stats_file_split = stats_file.split()
    file_path = os.path.join(stats_dir, stats_file)
    with open(file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        for i, row in enumerate(reader):
            if i == 0:
                continue
            if row["APP"] not in dict_sums:
                dict_sums[row["APP"]] = {
                    "Time": 0,
                    "Reachable Methods": 0,
                    "Avg. Paths": 0,
                }
            dict_sums[row["APP"]]["Time"] += float(row["TIME"])
            dict_sums[row["APP"]]["Reachable Methods"] += int(
                row["REACHED METHODS"]
            )
            dict_sums[row["APP"]]["Avg. Paths"] += float(
                row["AVG. REACHABLE PATHS"]
            )
    avgs = {
        "Time": 0,
        "Reachable Methods": 0,
        "Avg. Paths": 0,
    }
    tot_seeds = 0
    for app in dict_sums:
        paper_table_row = {}
        i = 0

        app_name_real = app
        app_name_command = subprocess.Popen(
            f'aapt dump badging {os.path.join("..", app_directory, app+".apk")} | grep "application-label-en:"',
            shell=True,
            stdout=subprocess.PIPE,
        )
        app_name = (
            app_name_command.communicate()[0].decode("utf-8").split("\n")
        )
        app_name_set = False
        for result in app_name:
            if result.strip():
                app_name_real = result.split("application-label-en:")[
                    1
                ].replace("'", "")
                app_name_set = True
                break

        if not app_name_set:
            app_name_command = subprocess.Popen(
                f'aapt dump badging {os.path.join("..", app_directory, app+".apk")} | grep "application-label:"',
                shell=True,
                stdout=subprocess.PIPE,
            )
            app_name = (
                app_name_command.communicate()[0].decode("utf-8").split("\n")
            )
            for result in app_name:
                if result.strip():
                    app_name_real = result.split("application-label:")[
                        1
                    ].replace("'", "")
                    break

        paper_table_row[paper_table_fields[i]] = app_name_real
        i += 1
        len_seed = len(open(f"../testing_seeds/{app}.seed", "r").readlines())
        tot_seeds += len_seed
        for key in dict_sums[app]:

            dict_sums[app][key] /= tot_runs
            if paper_table_fields[i] == "Reachable Methods":
                paper_table_row[paper_table_fields[i]] = (
                    "{:.2f}".format(
                        float(dict_sums[app][key] / len_seed) * 100
                    )
                    + "%"
                )
            else:

                paper_table_row[paper_table_fields[i]] = "{:.2f}".format(
                    float(dict_sums[app][key])
                )
            i += 1
            avgs[key] += dict_sums[app][key]
        paper_table_writer.writerow(paper_table_row)
    paper_table_row = {}
    i = 0
    paper_table_row[paper_table_fields[i]] = "Average"
    i += 1
    for key in avgs:
        if paper_table_fields[i] == "Reachable Methods":
            paper_table_row[paper_table_fields[i]] = (
                "{:.2f}".format((avgs[key] / tot_seeds) * 100) + "%"
            )
        else:
            avgs[key] /= tot_apps
            paper_table_row[paper_table_fields[i]] = "{:.2f}".format(
                float(avgs[key])
            )
        i += 1
    paper_table_writer.writerow(paper_table_row)
