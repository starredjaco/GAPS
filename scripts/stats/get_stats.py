import csv
import sys
import os
import json
import subprocess

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} csv_file app_directory seeds_directory")
    sys.exit(1)

TIMEOUT = 5 * 60 * 60


def update_csv(file_path, app_directory, seeds_directory):
    tot_apps = 0
    tot_time = 0
    tot_paths = 0
    tot_unique_paths = 0
    tot_reached_methods = 0
    tot_avg_paths_x_method = 0
    tot_seeds = 0
    tot_por = 0
    overall_path_recon_cond = 0
    paper_table_fields = [
        "App name",
        # "# DEX(s)",
        "Analysis Time",
        "SR",
        "Average paths per method",
        "RR",
    ]

    fields = [
        "APP",
        "TIME",
        "REACHED METHODS",
        "TOT. REACHABLE PATHS",
        "REACHABLE CONDITIONAL PATHS",
        "AVG. REACHABLE PATHS",
        "UNIQUE PATHS",
        "RR",
    ]

    containing_dir = os.path.dirname(file_path)
    paper_table_path = os.path.join(containing_dir, "final_stats.csv")
    with open(file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)
        paper_table_writer = csv.DictWriter(
            open(paper_table_path, "w"), fieldnames=paper_table_fields
        )
        for i, row in enumerate(reader):
            paper_table_row = {}
            if i == 0:
                for field in fields:
                    row[field] = field
                for field in paper_table_fields:
                    paper_table_row[field] = field
            if i != 0:
                for field in paper_table_fields:
                    paper_table_row[field] = ""
                tot_apps += 1
                tot_time += float(row["TIME"])
                tot_paths += int(row["TOT. REACHABLE PATHS"])
                if "/" not in row["REACHED METHODS"]:
                    tot_reached_methods += int(row["REACHED METHODS"])
                else:
                    tot_reached_methods += int(
                        row["REACHED METHODS"].split("/")[0]
                    )
                tot_unique_paths += int(row["UNIQUE PATHS"])
                tot_avg_paths_x_method += float(row["AVG. REACHABLE PATHS"])
                overall_path_recon_cond += int(
                    row["REACHABLE CONDITIONAL PATHS"]
                )
                app_name = row["APP"]
                paper_table_row["Analysis Time"] = "{:.2f}".format(
                    float(row["TIME"])
                )
                if "/" not in row["REACHED METHODS"]:
                    len_seed = len(
                        open(
                            os.path.join(seeds_directory, f"{app_name}.seed"),
                            "r",
                        ).readlines()
                    )
                else:
                    len_seed = int(row["REACHED METHODS"].split("/")[1])
                    row["REACHED METHODS"] = row["REACHED METHODS"].split("/")[
                        0
                    ]
                tot_seeds += len_seed
                if len_seed > 0:
                    paper_table_row["SR"] = (
                        "{:.2f}".format(
                            float(int(row["REACHED METHODS"]) / (len_seed))
                            * 100
                        )
                        + "%"
                    )
                else:
                    paper_table_row["SR"] = "0%"
                paper_table_row["Average paths per method"] = float(
                    row["AVG. REACHABLE PATHS"]
                )
                if not row["RR"]:
                    row["RR"] = "0"
                tot_por += float(row["RR"])
                paper_table_row["RR"] = row["RR"] + "%"
                # paper table
                apk_path = os.path.join(app_directory, row["APP"] + ".apk")
                if not os.path.exists(apk_path):
                    apk_path = os.path.join(
                        app_directory, row["APP"], row["APP"] + ".apk"
                    )
                app_name_command = subprocess.Popen(
                    f'aapt dump badging {apk_path} | grep "application-label-en:"',
                    shell=True,
                    stdout=subprocess.PIPE,
                )
                app_name = (
                    app_name_command.communicate()[0]
                    .decode("utf-8")
                    .split("\n")
                )
                app_name_set = False
                for result in app_name:
                    if result.strip():
                        paper_table_row["App name"] = result.split(
                            "application-label-en:"
                        )[1].replace("'", "")
                        app_name_set = True
                        break

                if not app_name_set:
                    app_name_command = subprocess.Popen(
                        f'aapt dump badging {apk_path} | grep "application-label:"',
                        shell=True,
                        stdout=subprocess.PIPE,
                    )
                    app_name = (
                        app_name_command.communicate()[0]
                        .decode("utf-8")
                        .split("\n")
                    )
                    for result in app_name:
                        if result.strip():
                            paper_table_row["App name"] = result.split(
                                "application-label:"
                            )[1].replace("'", "")
                            break

                if not paper_table_row["App name"].strip():
                    print(row["APP"])

                """
                n_dex_command = subprocess.Popen(
                    f'aapt list {os.path.join(app_directory, row["APP"]+".apk")} | grep "classes[[:digit:]]*.dex"',
                    shell=True,
                    stdout=subprocess.PIPE,
                )
                dexes = (
                    n_dex_command.communicate()[0].decode("utf-8").split("\n")
                )
                n_dex = 0
                for dex in dexes:
                    if dex.strip():
                        n_dex += 1
                        tot_dex += 1

                paper_table_row["# DEX(s)"] = n_dex
                """

            paper_table_writer.writerow(paper_table_row)

        paper_table_row = {
            "App name": "",
            # "# DEX(s)": "",
            "Analysis Time": "",
            "SR": "",
            "Average paths per method": "",
            "RR": "",
        }
        paper_table_writer.writerow(paper_table_row)

        paper_table_row = {
            "App name": "Average",
            # "# DEX(s)": "{:.2f}".format(float(tot_dex / tot_apps)),
            "Analysis Time": "{:.2f}".format(float(tot_time / tot_apps)),
            "SR": "{:.2f}%".format(
                float((tot_reached_methods / tot_seeds) * 100)
            ),
            "Average paths per method": "{:.2f}".format(
                float(tot_avg_paths_x_method / tot_apps)
            ),
            "RR": "{:.2f}%".format(float(tot_por / tot_apps)),
        }
        paper_table_writer.writerow(paper_table_row)


update_csv(sys.argv[1], sys.argv[2], sys.argv[3])
