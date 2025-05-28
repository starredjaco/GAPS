#!/bin/bash

# Command-line arguments
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <apps_path> <output_dir>"
    exit 1
fi

apps_path=$1
output_dir=$2   

apps=$(ls $apps_path | grep \.apk$)

for app in $apps;do
    echo $app
    ./run.sh $apps_path/$app $output_dir
    echo "done"
done