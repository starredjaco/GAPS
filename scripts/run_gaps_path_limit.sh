#!/usr/bin/env bash

export PYTHONPATH=$PYTHONPATH:src/

app_path="../app_examples/"
files=$(ls $app_path|grep .apk$)
mp500="-l 500"
mp1000="-l 1000"
mp2000="-l 2000"
mp5000="-l 5000"
mp10000="-l 10000"
mp20000="-l 20000"
up="-up"
runs=("$mp5000" "$mp10000" "$mp20000")
resume_from="tomdroid.apk"
resume=0
if [[ "$resume_from" == "" ]]; then
	resume=1
fi
for run in "${runs[@]}"; do
	echo "$run"
	for i in $(seq 1 5); do
		for file in $files; do
			#echo $file
			if [[ "$file" == "$resume_from" ]]; then
                resume=1
        	fi
        	if [ $resume -eq 1 ]; then
				app_name=$(basename $file .apk)
				python3 -m gaps -i $app_path$file -int -cond -seed testing_seeds/$app_name.seed "$run" -d > logout/$file-output.out 2>&1
				#echo "done"
				rm -rf /tmp/*.cache
			fi
		done
		echo >> stats.csv
	done
	echo "$run done" 
	mv stats.csv stats"$run".csv
done
