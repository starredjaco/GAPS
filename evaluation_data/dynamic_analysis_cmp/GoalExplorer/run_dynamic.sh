#!/bin/bash

# Check if apps_path is provided as a CLI argument
if [ $# -lt 1 ]; then
    echo "Usage: $0 <apps_path>"
    exit 1
fi

apps_path="$1"
apps=$(ls "$apps_path" | grep ".apk")
#apps=$(cat missing.txt)

emulator_name="emulator-5554"

# Function to check if emulator is running
is_emulator_running() {
    pgrep -f "emulator.*-avd $emulator_name" > /dev/null
}

# Function to launch emulator if not running
ensure_emulator_running() {
    if ! is_emulator_running; then
        echo "Emulator not running. Launching emulator..."
        nohup emulator -avd "$emulator_name" -no-snapshot-save -no-snapshot-load > /dev/null 2>&1 &
        # Wait for emulator to boot
        echo "Waiting for emulator to boot..."
        adb wait-for-device
        boot_completed=""
        while [ "$boot_completed" != "1" ]; do
            boot_completed=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
            sleep 2
        done
        echo "Emulator booted."
    else
        echo "Emulator is already running."
    fi
}

# Run the process three times with different output_logs_dirs
for i in 1 2 3; do
    output_logs_dir="./output_logs_dir_run_$i"
    if [ ! -d "$output_logs_dir" ]; then
        mkdir -p "$output_logs_dir"
    fi

    for app in $apps; do
        appname=$(echo $app | sed 's/.apk//g')
        log_file="$output_logs_dir/$app.log"

        # Skip if log file already exists
        if [ -f "$log_file" ]; then
            echo "Log file for $app already exists in $output_logs_dir. Skipping."
            continue
        fi

        echo $app

        sleep 5

        # Ensure emulator is running
        ensure_emulator_running

        # Extract package name using aapt
        package_name=$(aapt dump badging "$apps_path/$app" | grep "package: name=" | awk -F"'" '{print $2}')
        
        # Run the provided command with timeout and kill the process after timeout
        timeout --kill-after=5m 5m ruby Stoat/bin/run_stoat_testing.rb --avd_name=$emulator_name --apk_path="$apps_path/$app" --stg=./GoalExplorer/goalexplorer_results/$appname/${appname}_stg.xml

        echo "Command done"
        
        # Save logs and clear logcat
        adb logcat -d -s GAPS > "$log_file"
        adb logcat -c
        
    done
done
