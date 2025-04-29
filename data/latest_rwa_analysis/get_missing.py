import csv
import os
import subprocess as subp

missing = []
missing_static = []
apps_dir="/home/same/code/speck/gaps_real_world_dataset"

def get_package_name(apk_path):
    """get the package name of an app"""
    p1 = subp.Popen(
        ["aapt", "dump", "badging", apk_path], stdout=subp.PIPE
    )
    p2 = subp.Popen(
        ["grep", r"package:\ name"],
        stdin=p1.stdout,
        stdout=subp.PIPE,
        stderr=subp.DEVNULL,
    )
    p3 = subp.Popen(
        ["cut", "-c", "15-"], stdin=p2.stdout, stdout=subp.PIPE
    )
    p4 = subp.Popen(
        ["awk", "{print $1}"], stdin=p3.stdout, stdout=subp.PIPE
    )
    return p4.communicate()[0].decode().strip().replace("'", "")

apps = os.listdir(apps_dir)
print(len(apps))
missing_pkgs = []
with open("stats.csv") as stats_file:
    reader = csv.reader(stats_file)
    next(reader)
    for row in reader:
        apk = row[0] + ".apk"
        if float(row[1]) < 18000 and float(row[-1]) < 1:
            missing.append(apk)
            missing_pkgs.append(get_package_name(os.path.join(apps_dir, apk)))
        #missing_static.append(apk)

with open("missing.txt", "w") as missing_file:
    for app in missing:
        missing_file.write(app + "\n")

with open("missing_pkgs.txt", "w") as missing_file:
    for app in missing_pkgs:
        missing_file.write(app + "\n")
