#! /usr/bin/python

import os, sys, traceback, subprocess, time

ADB = os.getenv("ADB", "adb")

APE_ROOT = "/data/local/tmp/"
APE_JAR = APE_ROOT + "ape.jar"

APE_MAIN = "com.android.commands.monkey.Monkey"

APP_PROCESS = "/system/bin/app_process"

SERIAL = os.getenv("SERIAL")

if SERIAL:
    BASE_CMD = [
        ADB,
        "-s",
        SERIAL,
        "shell",
        "CLASSPATH=" + APE_JAR,
        APP_PROCESS,
        APE_ROOT,
        APE_MAIN,
    ]
else:
    BASE_CMD = [
        ADB,
        "shell",
        "CLASSPATH=" + APE_JAR,
        APP_PROCESS,
        APE_ROOT,
        APE_MAIN,
    ]


def run_cmd(*args):
    print("Run cmd: " + (" ".join(*args)))
    subprocess.check_call(*args)


def start_app(package_name):
    print("[+] APP STARTING")
    subprocess.Popen(
        f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_ape(args):
    run_cmd(BASE_CMD + list(args))


if __name__ == "__main__":
    pkg = sys.argv[2]
    print(pkg)
    start_app(pkg)
    start_time = time.time()
    while True:
        try:
            run_ape(sys.argv[1:])
        except:
            # restart app
            start_app(pkg)
        if time.time() - start_time > 300:  # 5 minutes = 300 seconds
            print("[+] Exiting after 5 minutes")
            break
