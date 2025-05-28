#!/bin/bash

apps_path="/home/same/code/gaps/AndroLog/androtest"
apps=$(ls $apps_path | grep ".apk")
#apps=$(cat missing.txt)

# Command-line arguments
output_logs_dir=${1:-"./output_logs_dir"}  # Default to "./output_logs_dir" if not provided
if [ ! -d "$output_logs_dir" ]; then
    mkdir -p "$output_logs_dir"
fi

for app in $apps; do
    echo $app 
    adb install -g "$apps_path/$app"

    # Extract package name using aapt
    package_name=$(aapt dump badging "$apps_path/$app" | grep "package: name=" | awk -F"'" '{print $2}')
    
    # Run the provided command with timeout and kill the process after timeout
    # timeout --kill-after=5m 5m python /home/same/code/gaps/GAPS/Guardian/run.py -a "$apps_path/$app" -t "interact with the application to maximize exploration" 
    python ape-bin/ape.py -p $package_name --running-minutes 300 --ape sata

    echo "Command done"
    
    # Save logs and clear logcat
    adb logcat -d -s GAPS > "$output_logs_dir/$app.log"
    adb logcat -c
    
    # Uninstall the app
    if [ -n "$package_name" ]; then
        adb uninstall "$package_name"
    else
        echo "Failed to extract package name for $app"
    fi
done
