# GAPS

Graph-based Automated Path Sythesizer

## Instructions

GAPS uses poetry so first install via:

`
curl -sSL https://install.python-poetry.org | python3 -
`

or pipx:

`
pipx install poetry
`

Then, GAPS can be installed from the current directory by running:

`poetry install
`

Make sure that you also have `apktool` (and `baksmali` if also interested in DEX-only analysis) in your PATH.

You can get `apktool` from [here](https://apktool.org/).


GAPS has two running modes:

- static, producing call-sequences and high-level instructions for automatic interaction
- run, dynamic automatic interaction module that uses the aforementioned high-level instructions

## [static] Command line arguments

- `-i, --input PATH` : APK/DEX path file to disassemble  [required]
- `-m, --method TEXT` : Target method to generate paths from
- `-cls, --class_name TEXT` : Target class to generate paths from
- `-p_cls, --parent_class TEXT` : Find target method invocation in a specific parent class
- `-sig, --signature TEXT` : Target method signature in Smali format to build paths for it
- `-seed, --seed_file PATH` : Path to the file containing seed signatures
- `-custom_seed, --custom_seed_file PATH` : Path to the file containing custom seed signatures
- `-cond, --conditional` : Generate paths that satisfy conditional statements
- `-l, --path_limit INTEGER RANGE` : Set an upper bound to the total number of paths reconstructed for each query (default: 1000)  [0<=x<=1000]
- `-up, --unconstrained-paths` : Generate paths without constraints
- `-v, --verbose` : Enable verbose output
- `-d, --debug` : Enable debug output
- `--help` : Show this message and exit

## Example usage

`
poetry run gaps static -i <app-path> -cond -m <target-method> -o <output_dir>
`

If no search direction is given (i.e., target method, target class and signature are not specified), a seed file is generated automatically by randomly selecting 50 methods in the app's package name.

# GAPS Automatic Interaction

If device is rooted and equipped with Frida, a Runtime Reachability can be obtained.

## [run] Command line arguments

- `-i, --input PATH` : APK path file to run  [required]
- `-instr, --instructions PATH` : JSON instruction file
- `-frida, --frida` : Add Frida hooks
- `-ms, --manual-setup` : manually setup the app in the initial stage
-  `-t, --target` : specify a target method from the instructions file
- `--help` : Show this message and exit

## Example usage

`
poetry run gaps run -i <app_path> -instr <path_to_json> -frida
`

## Paper evaluation data

In `evaluation_data` the results of the experiments described in the paper can be found, as well as the target methods considered.
The AndroTest benchmark dataset instrumented by AndroLogs can be downloaded from [here](https://drive.google.com/file/d/16RnqK_L0I90e2OzqjDM9YMK5PKvnILHo/view?usp=sharing). 

Download it and unzip it in a directory.

Then:
```bash
cd scripts
./run_all_static.sh <androtest_directory_path> ../evaluation_data/androtest_seeds <output_directory>
```

After this step, you should have generated in <output_directory> a directory for each app analyzed containing the high-level instructions and logs. Additionally, statistics are saved in a csv file.

Finally, plug an Android device or an emulator and run:
```bash
./run_all_dynamic.sh <androtest_directory_path> <output_directory>
```

Finally, you can get some more refined statistics by running the get_stats.py file

```bash
cd stats # while in scripts
python get_stats.py <output_directory>/stats.csv <androtest_directory_path> ../../evaluation_data/androtest_seeds
```

A `final_stats.csv` file will be generated in <output_directory>.