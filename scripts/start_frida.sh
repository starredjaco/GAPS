#!/bin/bash
adb root && adb push ~/Downloads/frida-server-16.5.7-android-x86_64 /data/local/tmp/frida-server && adb shell "chmod +x /data/local/tmp/frida-server" && adb shell "/data/local/tmp/frida-server -D &"
