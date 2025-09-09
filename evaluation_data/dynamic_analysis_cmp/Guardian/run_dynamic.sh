#!/bin/bash

# Check for mandatory apps_path argument
if [ -z "$1" ]; then
    echo "Usage: $0 <apps_path> [output_logs_dir]"
    exit 1
fi

apps_path="$1"
apps=$(ls "$apps_path" | grep ".apk")

# Optional output_logs_dir argument
output_logs_dir=${2:-"./output_logs_dir"}
if [ ! -d "$output_logs_dir" ]; then
    mkdir -p "$output_logs_dir"
fi

for app in $apps; do
    echo $app 
    adb install -g "$apps_path/$app"

    # Extract package name using aapt
    package_name=$(aapt dump badging "$apps_path/$app" | grep "package: name=" | awk -F"'" '{print $2}')
    
    # Run the provided command with timeout and kill the process after timeout
    timeout --kill-after=5m 5m python run.py -a "$apps_path/$app" -t "interact with the application to maximize exploration" 

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
