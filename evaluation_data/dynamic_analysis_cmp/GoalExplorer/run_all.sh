#!/bin/bash

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <APP_DIR>"
    exit 1
fi

APP_DIR="$1"
TARGETS_DIR="./androtest_targets"
OUTPUT_DIR="goalexplorer_results"
JAR="GoalExplorer-1.2-SNAPSHOT-jar-with-dependencies.jar"
SDK_PATH="$HOME/Android/Sdk"
CSV_FILE="$OUTPUT_DIR/goal_explorer.csv"

mkdir -p "$OUTPUT_DIR"

echo "app_name,real_time(s)" > "$CSV_FILE"

for apk in "$APP_DIR"/*.apk; do
    app_name=$(basename "$apk" .apk)
    seed_file="$TARGETS_DIR/${app_name}.seed"

    if [[ -f "$seed_file" ]]; then
        targets=$(paste -sd\; "$seed_file")

        start_time=$(date +%s.%N)
        java -jar "$JAR" -i "$apk" -s "$SDK_PATH" --target "api: $targets" -o "$OUTPUT_DIR/$app_name" >/dev/null 2>&1
        end_time=$(date +%s.%N)
        real_time=$(echo "$end_time - $start_time" | bc)

        # Append to CSV
        echo "$app_name,$real_time" >> "$CSV_FILE"
    else
        echo "Seed file not found for $app_name, skipping."
    fi
done