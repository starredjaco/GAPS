#!/bin/bash

# Command-line arguments (both mandatory)
if [ $# -ne 2 ]; then
    echo "Usage: $0 <output_logs_dir> <apps_path>"
    exit 1
fi

output_logs_dir="$1"
apps_path="$2"

if [ ! -d "$output_logs_dir" ]; then
    mkdir -p "$output_logs_dir"
fi

apps=$(ls "$apps_path" | grep ".apk")

for app in $apps; do
    echo $app 
    adb install -g "$apps_path/$app"

    sleep 5

    # Extract package name using aapt
    package_name=$(aapt dump badging "$apps_path/$app" | grep "package: name=" | awk -F"'" '{print $2}')
    
    # Run the provided command with timeout and kill the process after timeout
    timeout --kill-after=5m 5m python ape.py -p $package_name --running-minutes 300 --ape sata

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
