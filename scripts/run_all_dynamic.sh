#!/usr/bin/env bash

OIFS="$IFS"
IFS=$'\n'

# Command-line arguments
if [[ $# -lt 3 ]]; then
	echo "Usage: $0 <app_path> <output_dir> [files] [resume_from]"
	exit 1
fi

app_path=$1
output_dir=$2
files=${3:-$(ls $app_path | grep .apk$)}
resume_from=${4:-""}

resume=0
if [[ "$resume_from" == "" ]]; then
	resume=1
fi

for file in $files; do
	echo $file
	app_name=$(basename $file .apk)
	if [[ "$file" == "$resume_from" ]]; then
		resume=1
	fi
	if [ $resume -eq 1 ]; then
		poetry run gaps run -i $app_path/$file -instr $output_dir/$app_name/$app_name-instr.json -o $output_dir -frida 
	fi
	echo "done"
done

