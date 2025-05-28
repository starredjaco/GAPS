import time
import subprocess as sub
import os
import threading
import csv
import sys

TIMEOUT = 5 * 60 * 60


class RunCmd(threading.Thread):
    def __init__(self, cmd, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        self.p = sub.Popen(self.cmd)
        self.p.wait()

    def Run(self):
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()  # use self.p.kill() if process needs a kill -9
            self.join()


if not os.path.exists("../results"):
    os.mkdir("../results")

#apps_dir = "/home/same/code/speck/speck_extension/SPECK+/Interpreter/exploit/CFG/app_examples/"
#seeds_dir = "/home/same/code/speck/speck_extension/SPECK+/Interpreter/exploit/CFG/gaps/testing_seeds/"
apps_dir = "/users/same/app_examples/"
seeds_dir = "/users/same/testing_seeds/"

#apps = os.listdir(apps_dir)
apps = []
with open("missing.txt") as missing_file:
    lines = missing_file.readlines()
    for line in lines:
        apps.append(line.strip())

for i in range(2):
    stats = "../results/stats_wo_flowdroid_fe.csv"
    flowdroid_param = ""
    if i == 0:
        continue
    if i == 1:
        stats = "../results/stats_W_flowdroid.csv"
        flowdroid_param = "--use-flowdroid"
    for app in apps:
        if ".apk" in app:
            start_time = time.time()
            app_name = app.replace(".apk", "")
            print(app)
            cmd = [
                "python",
                "dreach_comparison.py",
                f"{os.path.join(apps_dir, app)}",
                f'{os.path.join(seeds_dir, app_name+".seed")}',
            ]
            if flowdroid_param.strip():
                cmd.append(flowdroid_param)
            print(cmd)
            RunCmd(cmd, TIMEOUT).Run()
            end_time = "{:.2f}".format(time.time() - start_time)
            if not os.path.exists(stats):
                with open(stats, "w") as stats_file:
                    writer = csv.writer(stats_file)
                    writer.writerow(["App", "Time"])
            with open(stats, "a") as stats_file:
                writer = csv.writer(stats_file)
                writer.writerow([app, end_time])
