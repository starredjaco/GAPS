# README


## Install


    adb push ape.jar /data/local/tmp/


## Run


We install a script in `/data/loca/tmp/ape`. So you can simply launch `ape` via `adb shell /data/local/tmp/ape`.

We also provide a python script (i.e., `ape.py`) to facilitate running ape on Android devices in your local machine.
The following command starts to run Ape to test the Calculator on a real device connected via `adb`.


    ./ape.py -p com.google.android.calculator --running-minutes 100 --ape sata


For emulator, we can try the following command.


    export SERIAL=emulator-5554 && ./ape.py -p com.google.android.calculator --running-minutes 100 --ape sata


Check the `ape.py` if you want to run Ape with an emulator or more devices.

Options:

* `-p`: specify the package name, the same as Monkey
* `--running-minutes`: the total testing time in minutes
* `--ape sata`: use the exploration strategy described in the paper.
    * Another exploration strategy is `random`.
