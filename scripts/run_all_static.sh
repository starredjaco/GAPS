#!/usr/bin/env bash

OIFS="$IFS"
IFS=$'\n'

# Command-line arguments
if [[ $# -lt 3 ]]; then
	echo "Usage: $0 <app_path> <testing_seed_path> <output_data_dir> [files] [resume_from]"
	exit 1
fi

app_path=$1
testing_seed_path=$2
output_data_dir=$3
files=${4:-$(ls $app_path | grep .apk$)}
resume_from=${5:-""}

resume=0
if [[ "$resume_from" == "" ]]; then
	resume=1
fi

for file in $files; do
	echo $file
	if [[ "$file" == "$resume_from" ]]; then
		resume=1
	fi
	if [ $resume -eq 1 ]; then
		app_name=$(basename $file .apk)
		poetry run gaps static -i $app_path/$file -seed $testing_seed_path/$app_name.seed -cond -o $output_data_dir
		echo "done"
		rm -rf /tmp/*.cache
	fi
done
