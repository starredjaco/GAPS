#!/usr/bin/python3
import os
import subprocess as subp
import sys
import time
import json
import frida
import threading
import csv
import xml.etree.ElementTree as ET
import re

from pathlib import Path
from com.dtmilano.android.viewclient import ViewClient
from collections import defaultdict

from . import utils

event = threading.Event()


class InternalLLMThread(threading.Thread):
    def __init__(
        self,
        apk_path,
        instructions_dir,
        target_method,
        activity,
        _id,
        package_name,
        target_path,
    ):
        self.apk_path = apk_path
        self.activity = activity
        self._id = _id
        self.instructions_dir = instructions_dir
        self.target_method = target_method
        self.package_name = package_name
        self.target_path = target_path
        self._stop_event = threading.Event()
        threading.Thread.__init__(self)

    def get_ui_hierarchy(self):
        # dump hierarchy
        subp.run(
            "adb shell uiautomator dump /data/local/tmp/window_dump.xml",
            shell=True,
            stdout=subp.DEVNULL,
            stderr=subp.DEVNULL,
        )
        res = subp.run(
            "adb shell cat /data/local/tmp/window_dump.xml",
            shell=True,
            capture_output=True,
            text=True,
        )
        xml_content = res.stdout
        if (
            not xml_content
            or "UI hierchary dumped to" not in xml_content
            and not xml_content.strip().startswith("<?xml")
        ):
            return []

        xml_start = xml_content.find("<?xml")
        if xml_start != -1:
            xml_content = xml_content[xml_start:]
        else:
            return []

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return []

        elements = []
        element_idx = 0
        for node in root.iter("node"):
            if node.attrib.get("package") == "com.android.systemui":
                continue
            clickable = node.attrib.get("clickable") == "true"
            scrollable = node.attrib.get("scrollable") == "true"
            is_edit_text = "EditText" in node.attrib.get("class", "")

            if clickable or scrollable or is_edit_text:
                resource_id = node.attrib.get("resource-id", "")
                text = node.attrib.get("text", "")
                content_desc = node.attrib.get("content-desc", "")
                bounds = node.attrib.get("bounds", "")
                class_name = node.attrib.get("class", "")

                if bounds == "[0,0][0,0]":
                    continue

                info = f"Index: {element_idx}, Class: {class_name}, Text: {text}, Desc: {content_desc}, Id: {resource_id}"
                action_type = (
                    "text"
                    if is_edit_text
                    else ("click" if clickable else "swipe")
                )
                elements.append(
                    {
                        "index": element_idx,
                        "info": info,
                        "resource_id": resource_id,
                        "action_type": action_type,
                        "bounds": bounds,
                        "class_name": class_name,
                    }
                )
                element_idx += 1
        return elements

    def query_llm(
        self,
        class_name,
        method_name,
        elements,
        curr_activity,
        past_actions,
        error_feedback="",
    ):
        import openai

        # Initialize OpenAI client
        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "PLACEHOLDER_KEY")
        )

        elements_text = "\n".join([e["info"] for e in elements])
        history_text = (
            "\n".join([f"- {act}" for act in past_actions])
            if past_actions
            else "None"
        )
        path_text = (
            "\n".join([str(p) for p in self.target_path])
            if self.target_path
            else "Not provided"
        )

        prompt = f"""You are an Android UI testing agent navigating an app to find a specific target.
Your objective is to reach class "{class_name}" and method "{method_name}".
The planned execution path provided by static analysis is:
{path_text}

You are currently on the Android activity: {curr_activity}.
Here are the interactable elements on the current screen:
{elements_text}

Past actions taken in this session (avoid repeating failed loops):
{history_text}

{error_feedback}

Choose one element to interact with to get closer to the objective.
You MUST respond with a strictly valid JSON object using this schema:
{{
    "action": "CLICK" | "TYPE" | "SWIPE" | "BACK",
    "index": <integer reference to the element index, or -1 if BACK>,
    "text": "<only required if action is TYPE, otherwise empty string>"
}}
Output nothing but the JSON object. Do not wrap it in markdown block quotes.
"""
        max_retries = 3
        for _ in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-5.2",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a specialized JSON-only Android UI testing assistant.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                return json.loads(content)
            except Exception as e:
                print(f"OpenAI API Error: {e}")
                time.sleep(2)
        return {"action": "BACK", "index": -1, "text": ""}

    def execute_action(self, action_json, elements, curr_activity):
        cmd = action_json.get("action", "").upper()

        if cmd == "BACK":
            subp.run("adb shell input keyevent 4", shell=True)
            return "BACK", ""

        index = action_json.get("index", -1)
        if index == -1:
            return "INVALID", "No valid index provided."

        element = next((e for e in elements if e["index"] == index), None)
        if not element:
            return (
                "INVALID",
                f"Element with index {index} not found on screen.",
            )

        resource_id = element["resource_id"]
        if resource_id and "/" in resource_id:
            res_id_short = resource_id.split("/")[1]
        else:
            res_id_short = str(element["bounds"])

        action_log = ""
        action_summary = ""

        if cmd == "CLICK":
            bounds = element["bounds"]
            if bounds:
                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                if m:
                    x = (int(m.group(1)) + int(m.group(3))) // 2
                    y = (int(m.group(2)) + int(m.group(4))) // 2
                    subp.run(f"adb shell input tap {x} {y}", shell=True)
            action_log = f"click {self.package_name}:id/{res_id_short}"
            action_summary = f"CLICKED index {index}"

        elif cmd == "TYPE":
            text = action_json.get("text", "")
            bounds = element["bounds"]
            if bounds:
                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                if m:
                    x = (int(m.group(1)) + int(m.group(3))) // 2
                    y = (int(m.group(2)) + int(m.group(4))) // 2
                    subp.run(f"adb shell input tap {x} {y}", shell=True)
                    time.sleep(0.5)
                    text_escaped = text.replace(" ", r"\ ")
                    subp.run(
                        f'adb shell input keycombination 113 29 && adb shell input keyevent 67 && adb shell input text "{text_escaped}"',
                        shell=True,
                    )
            action_log = f"text {self.package_name}:id/{res_id_short} {text}"
            action_summary = f"TYPED '{text}' into index {index}"

        elif cmd == "SWIPE":
            bounds = element["bounds"]
            if bounds:
                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                if m:
                    x = (int(m.group(1)) + int(m.group(3))) // 2
                    y = (int(m.group(2)) + int(m.group(4))) // 2
                    subp.run(
                        f"adb shell input swipe {x} {y} {x} {max(10, y - 400)}",
                        shell=True,
                    )
            else:
                subp.run("adb shell input swipe 500 1000 500 300", shell=True)
            action_log = f"swipe {self.package_name}:id/{res_id_short}"
            action_summary = f"SWIPED on index {index}"

        if action_log:
            self.save_memory(curr_activity, action_log)
            return "SUCCESS", action_summary

        return "UNKNOWN", "Unknown action command"

    def save_memory(self, curr_activity, action_log):
        memory_file = os.path.join(
            self.instructions_dir, "activity_memory.json"
        )
        try:
            time.sleep(1)
            get_current_focus = subp.Popen(
                "adb shell dumpsys window | grep mCurrentFocus",
                shell=True,
                stdout=subp.PIPE,
            )
            communicate = get_current_focus.communicate()
            if not communicate[0]:
                return
            new_activity = (
                communicate[0].decode().strip().split("/")[-1].replace("}", "")
            )

            if (
                curr_activity != new_activity
                and curr_activity
                and new_activity
            ):
                data = {}
                if os.path.exists(memory_file):
                    with open(memory_file, "r") as f:
                        data = json.load(f)

                if curr_activity not in data:
                    data[curr_activity] = {}
                if new_activity not in data[curr_activity]:
                    data[curr_activity][new_activity] = []

                events_list = [action_log]
                if events_list not in data[curr_activity][new_activity]:
                    data[curr_activity][new_activity].append(events_list)

                with open(memory_file, "w") as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def run(self):
        class_name, method_name = self.target_method.split(";->")
        class_name = class_name[1:].replace("/", ".")
        method_name = method_name.split("(")[0]
        if "<init>" == method_name:
            method_name = "init"

        attempts = 0
        past_actions = []
        error_feedback = ""

        while not self._stop_event.is_set() and attempts < 15:
            get_current_focus = subp.Popen(
                "adb shell dumpsys window | grep mCurrentFocus",
                shell=True,
                stdout=subp.PIPE,
            )
            communicate = get_current_focus.communicate()
            if not communicate[0]:
                time.sleep(1)
                attempts += 1
                continue
            curr_activity = (
                communicate[0].decode().strip().split("/")[-1].replace("}", "")
            )

            elements = self.get_ui_hierarchy()
            if not elements:
                time.sleep(1)
                attempts += 1
                continue

            action_json = self.query_llm(
                class_name,
                method_name,
                elements,
                curr_activity,
                past_actions,
                error_feedback,
            )
            print(f"[{curr_activity}] LLM Action JSON: {action_json}")
            status, msg = self.execute_action(
                action_json, elements, curr_activity
            )

            if status == "INVALID":
                error_feedback = f"Error from last action: {msg}. Please select a valid index from the list."
                print(f"[!] {error_feedback}")
            else:
                error_feedback = ""
                if status == "SUCCESS":
                    past_actions.append(msg)
                    if len(past_actions) > 5:
                        past_actions.pop(0)

            time.sleep(2)
            attempts += 1

    def stop(self):
        self._stop_event.set()


class GAPSRUN:

    def __init__(self, apk_path, output, manual_setup, frida_bool):
        self.apk_path = apk_path
        self.output = output
        self.stats_file_path = os.path.join(self.output, "stats.csv")
        if not os.path.exists(self.stats_file_path):
            print(f"Missing stats file at: {self.stats_file_path}")
            sys.exit(1)
        self.manual_setup = manual_setup
        self.avc_device = None
        self.vc = None
        self.frida_device = None
        self.frida_bool = frida_bool
        self.method_reached = False
        self.package_name = ""
        self.log = ""
        self.frida_script_name = "fridaHooks.js"
        self.hook_dir = self.output
        self.hook_path = os.path.join(self.hook_dir, self.frida_script_name)
        self.llm_used = defaultdict(bool)
        if not os.path.exists(self.hook_path):
            with open(self.hook_path, "w") as _:
                pass

    def spawn_added(self, spawn):
        event.set()
        if spawn.identifier.startswith(self.package_name):
            session = self.frida_device.attach(spawn.pid)
            try:
                script = session.create_script(open(self.hook_path).read())
                script.on("message", self.on_message)
                script.load()
            except Exception:
                pass
            self.frida_device.resume(spawn.pid)

    def on_message(self, message, data):
        if message["type"] == "send":
            comm = message["payload"]
            if not self.method_reached:
                print("[+] Received response")
                print(comm)
            self.method_reached = True

    def check_method_in_logcat(self, json_paths):
        """
        Continuously monitors adb logcat output in a separate thread to check if the method is reached.

        :param method_name: The name of the method to check.
        """
        methods = list(json_paths.keys())
        java_methods = {}
        for method in methods:
            java_method = utils.to_java_signature(method)
            java_methods[java_method] = method

        def monitor_logcat():
            process = subp.Popen(
                ["adb", "logcat", "-s", "GAPS"],
                stdout=subp.PIPE,
                stderr=subp.DEVNULL,
                text=True,
            )
            for line in process.stdout:
                if "METHOD" in line:
                    for method_name in java_methods:
                        if method_name in line:
                            print(
                                f"[+] Method '{java_methods[method_name]}' found in logcat."
                            )
                            self.methods_por[java_methods[method_name]] += 1
                        else:
                            smali_key = java_methods[method_name]
                            for path in json_paths[smali_key]:
                                alternative_target = json_paths[smali_key][
                                    path
                                ]["call_sequence"][0]
                                java_alternative_target = (
                                    utils.to_java_signature(
                                        alternative_target.split()[1]
                                    )
                                )
                                if java_alternative_target in line:
                                    print(
                                        f"[+] Alternative target '{smali_key}' found in logcat."
                                    )
                                    self.methods_por[
                                        java_methods[method_name]
                                    ] += 1

        logcat_thread = threading.Thread(target=monitor_logcat, daemon=True)
        logcat_thread.start()

    def save(self, javascript):
        if not os.path.exists(self.hook_dir):
            os.makedirs(self.hook_dir)

        with open(self.hook_path, "w") as f:
            f.write(javascript)

    def get_package_name(self, apk_path):
        """get the package name of an app"""
        p1 = subp.Popen(
            ["aapt", "dump", "badging", apk_path], stdout=subp.PIPE
        )
        p2 = subp.Popen(
            ["grep", r"package:\ name"],
            stdin=p1.stdout,
            stdout=subp.PIPE,
            stderr=subp.DEVNULL,
        )
        p3 = subp.Popen(
            ["cut", "-c", "15-"], stdin=p2.stdout, stdout=subp.PIPE
        )
        p4 = subp.Popen(
            ["awk", "{print $1}"], stdin=p3.stdout, stdout=subp.PIPE
        )
        return p4.communicate()[0].decode().strip()

    def get_main_activity(self, apk_path):
        """get the main activity of an app"""
        p1 = subp.Popen(
            ["aapt", "dump", "badging", apk_path], stdout=subp.PIPE
        )
        p2 = subp.Popen(
            ["grep", "launchable-activity"],
            stdin=p1.stdout,
            stdout=subp.PIPE,
            stderr=subp.DEVNULL,
        )
        p3 = subp.Popen(
            ["awk", "{print $2}"], stdin=p2.stdout, stdout=subp.PIPE
        )
        p4 = subp.Popen(["cut", "-c6-"], stdin=p3.stdout, stdout=subp.PIPE)
        return p4.communicate()[0].decode().strip()

    def get_main_component(self, apk_path):
        """gets the main activity component by combining the app package and app main activity"""
        app_package_name = self.get_package_name(apk_path)
        app_main_activity = self.get_main_activity(apk_path)
        return app_package_name + "/" + app_main_activity

    def get_serialno(self):
        """get serial number of device"""
        return subp.check_output(["adb", "get-serialno"]).decode().strip()

    def force_dump(self, vc):
        """force dump of the screen despite errors"""
        attempts = 0
        while attempts < 10:
            try:
                attempts += 1
                vc.dump(-1, sleep=0.2)
                break
            except Exception:
                pass

    def get_current_activity(self):
        get_current_focus = subp.Popen(
            "adb shell dumpsys window | grep mCurrentFocus",
            shell=True,
            stdout=subp.PIPE,
        )
        communicate = get_current_focus.communicate()
        activity = (
            communicate[0].decode().strip().split("/")[-1].replace("}", "")
        )
        return activity

    def check_current_activity(self, activity):
        cycles = 0
        while True:
            curr_activity = self.get_current_activity()
            if activity == curr_activity:
                return True
            if cycles > 2:
                return False
            time.sleep(1)
            cycles += 1

    def scroll_find_click(self, vc, comp_id):
        # manual scrolling
        tries = 2
        scroll = 0
        while True:
            self.force_dump(vc)
            if vc.findViewById(comp_id):
                vc.findViewById(comp_id).touch()
                break
            if scroll > 5:
                subp.Popen(
                    "adb shell input swipe 300 300 500 1000",
                    shell=True,
                    stdout=subp.DEVNULL,
                    stderr=subp.DEVNULL,
                )
                vc.sleep(0.2)
                tries -= 1
                scroll = 0
                if tries == 0:
                    break
            else:
                subp.Popen(
                    "adb shell input swipe 500 1000  300 300",
                    shell=True,
                    stdout=subp.DEVNULL,
                    stderr=subp.DEVNULL,
                )
                vc.sleep(0.2)
                scroll += 1

    def perform_action(self, vc, instruction, package_name):
        if instruction[0] == "intent":
            print(f"[+] SENT INTENT FOR {instruction[1]}")
            if instruction[1] == "android.intent.action.MAIN":
                return 0
            if instruction[1].startswith("android.intent.action"):
                self.log += "unsupported intent " + instruction[1] + " \n"
                return 0
            subp.Popen(
                f"adb shell am {instruction[2]} {instruction[1]}",
                shell=True,
                stdout=subp.PIPE,
            )
            return 0
        if instruction[0] == "press menu":
            print("[+] PRESSED MENU")
            self.avc_device.shell("input keyevent KEYCODE_MENU")
            return 0
        if instruction[0] == "main activity":
            return 0
        if len(instruction) > 2:
            correct_activity = True
        else:
            correct_activity = self.check_current_activity(instruction[0])
        if correct_activity:
            self.force_dump(vc)
            if instruction[1] == "<unknown>":
                return -2
            print(f"[+] LOOKING FOR {instruction[1]}")
            try:
                comp_id = f"{package_name}:id/{instruction[1]}"
                try:
                    vc.findViewByIdOrRaise(comp_id).touch()
                    print(f"[+] CLICKED {instruction[1]}")
                except Exception:
                    print(
                        f"[!] Element with id '{instruction[1]}' not found under package '{package_name}'. Listing all elements on the screen:"
                    )
                    self.force_dump(vc)
                    for view in vc.views:
                        if (
                            instruction[1] in view.getId()
                            or instruction[1] in view.getUniqueId()
                        ):
                            print(
                                f"[+] Found matching element: {view.getId()} or {view.getUniqueId()}"
                            )
                            view.touch()
                            print(f"[+] CLICKED {instruction[1]}")
                            return
                    raise Exception(
                        f"[!] Element with id '{instruction[1]}' not found on the screen."
                    )
            except Exception:
                try:
                    if len(instruction) > 2:
                        vc.findViewWithText(instruction[2]).touch()
                        print(f"[+] CLICKED {instruction[1]}")
                    else:
                        self.scroll_find_click(vc, comp_id)
                except Exception:
                    self.log += (
                        "missing id " + instruction[1] + " not found \n"
                    )
                    return -1

            vc.sleep(0.2)
        else:
            return -1
        return 0

    def update_csv(self, app_name, tot_methods, methods_por):
        rows = []
        app_por = 0
        if tot_methods > 0:
            app_por = "{:.2f}".format(
                float(
                    (
                        sum(1 for method in methods_por.values() if method > 0)
                        / tot_methods
                    )
                    * 100
                )
            )
        with open(self.stats_file_path, "r") as stats_file:
            reader = csv.reader(stats_file)
            header = next(reader)
            if header[-1] != "PoR":
                header.append("PoR")
            rows.append(header)
            for row in reader:
                if row[0] == app_name:
                    if len(row) == 8:
                        row[7] = app_por
                    else:
                        row.append(app_por)
                rows.append(row)

        with open(self.stats_file_path, "w") as stats_file:
            writer = csv.writer(stats_file)
            writer.writerows(rows)

    def uninstall_app(self, package_name):
        print("[+] UNINSTALLING APP")
        if package_name != "com.fsck.k9":
            subp.Popen(
                ["adb", "shell", "pm", "uninstall", package_name],
                stdout=subp.PIPE,
            )

    def start_app(self, package_name):
        print("[+] APP STARTING")
        subp.Popen(
            f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1",
            shell=True,
            stdout=subp.DEVNULL,
            stderr=subp.DEVNULL,
        )

    def stop_app(self, app_pkg_name):
        print("[+] APP STOPPING")
        subp.call(
            f"adb shell am force-stop {app_pkg_name}",
            shell=True,
            stdout=subp.DEVNULL,
            stderr=subp.DEVNULL,
        )

    def restart_app(self, package_name):
        self.stop_app(self.package_name)
        time.sleep(2)
        self.start_app(self.package_name)

    def use_llms(self, instruction, target_path=None):
        if len(instruction) == 2:
            activity, _id = instruction
        else:
            activity, _id = instruction[0], None

        if len(activity.split()) > 1:
            activity = "_".join(activity.split())

        llmThread = InternalLLMThread(
            self.apk_path,
            self.instructions_dir,
            self.target_method,
            activity,
            _id,
            self.package_name,
            target_path,
        )
        llmThread.start()
        old_val = self.methods_por[self.target_method]
        while llmThread.is_alive():
            if self.methods_por[self.target_method] > old_val:
                print("[+] Target method reached, killing thread.")
                llmThread.stop()  # Forcefully stop the thread
                break
        llmThread.join()

    def input_text(self, text):
        try:
            text = text.replace(" ", r"\ ")

            subp.Popen(
                'adb shell input keycombination 113 29 && adb shell input keyevent 67 && adb shell input text "{}"'.format(
                    text
                ),
                shell=True,
                stdout=subp.DEVNULL,
                stderr=subp.PIPE,
            )
            time.sleep(0.2)
        except Exception:
            return False
        return True

    def perform_action_from_memory(self, curr_activity, target_activity):
        activity_memory_path = os.path.join(
            self.instructions_dir, "activity_memory.json"
        )
        found = False
        if os.path.exists(activity_memory_path):
            with open(activity_memory_path, "r") as f:
                activity_memory = json.load(f)
            print(curr_activity, target_activity)
            if (
                curr_activity in activity_memory
                and target_activity in activity_memory[curr_activity]
            ):
                print("[+] FOUND ACTIVITY MEMORY, PERFORMING ACTIONS")
                for actions in activity_memory[curr_activity][target_activity]:
                    for action in actions:
                        splits = action.split()
                        if splits[0] == "click" and "/" in splits[1]:
                            operation = [
                                curr_activity,
                                splits[1].split("/")[1],
                            ]
                            self.perform_action(
                                self.vc, operation, self.package_name
                            )
                        elif splits[0] == "text" and "/" in splits[1]:
                            operation = [
                                curr_activity,
                                splits[1].split("/")[1],
                            ]
                            self.perform_action(
                                self.vc, operation, self.package_name
                            )
                            self.input_text(splits[2])
                    if self.get_current_activity() == target_activity:
                        found = True
                        return found
        return found

    def _process_method(self, class_method, json_paths):
        print(f"[+] LOOKING FOR {class_method}")
        if self.frida_bool:
            self.save("")
            frida_script = utils.create_javascript(class_method)
            self.save(frida_script)
            print("[+] CREATED FRIDA SCRIPT\n")
        frida_err = False
        self.method_reached = False
        if self.frida_bool:
            try:
                pid = self.frida_device.spawn([self.package_name])
                session = self.frida_device.attach(pid)
                script = session.create_script(open(self.hook_path).read())
                script.on("message", self.on_message)
                script.load()

                self.frida_device.resume(pid)
            except Exception:
                frida_err = True
                pass
        else:
            self.start_app(self.package_name)
        if frida_err:
            self.log += "could not hook " + class_method + " \n "
            print(f"[!] ERROR COULD NOT HOOK {class_method}")
            # return tot_methods, methods_por
            self.stop_app(self.package_name)
            time.sleep(2)
            self.start_app(self.package_name)

        seen_paths = set()
        traversable_paths = []
        for key in json_paths[class_method]:
            path = json_paths[class_method][key]["path"]
            path_key = ""
            if path[0][0] == "intent":
                continue
            for element in path:
                path_key += str(element) + " "
            if path_key in seen_paths:
                # print("already visited")
                continue
            seen_paths.add(path_key)
            traversable_paths.append(path)
        for path in traversable_paths:
            """
            if frida_err:
                frida_err_again = True
                attempts = 0
                for method_to_hook in json_paths[class_method][key][
                    "call_sequence"
                ]:
                    attempts += 1
                    if attempts > 5:
                        break
                    method_to_hook = method_to_hook.split()[1]
                    print(method_to_hook)
                    frida_script = self.create_javascript(method_to_hook)
                    self.save(frida_script)
                    try:
                        if self.frida_bool and self.method_reached:
                            print("[*] PATH SUCCESSFULLY VISITED!\n")
                            if class_method not in methods_por:
                                methods_por[class_method] = 0
                            methods_por[class_method] += 1
                            break
                        pid = self.frida_device.spawn([self.package_name])
                        session = self.frida_device.attach(pid)
                        script = session.create_script(
                            open(self.hook_path).read()
                        )
                        script.on("message", self.on_message)
                        script.load()

                        self.frida_device.resume(pid)
                        frida_err_again = False
                    except Exception:
                        self.stop_app(self.package_name)
                        time.sleep(5)
                        self.start_app(self.package_name)
                        pass
                    if not frida_err_again:
                        break
            if self.frida_bool and frida_err:
                self.log += (
                    "could not hook anything in the callsequence of "
                    + class_method
                    + " \n "
                )
                self.stop_app(self.package_name)
                time.sleep(5)
                self.start_app(self.package_name)
                continue
            """
            self.force_dump(self.vc)
            self.vc.sleep(0.2)
            self.avc_device.startActivity(
                component=self.get_main_component(self.apk_path)
            )
            self.vc.sleep(0.2)
            i = 0
            while i < len(path):
                if type(path[i]) is str:
                    self.start_app(self.package_name)
                    self.vc.sleep(0.2)
                    i += 1
                    pass
                elif type(path[i]) is list:
                    self.vc.sleep(0.2)
                    status = self.perform_action(
                        self.vc, path[i], self.package_name
                    )
                    curr_activity = self.get_current_activity()
                    target_activity = path[i][0]
                    if (status == -1 or status == -2) and not self.llm_used[
                        target_activity
                    ]:
                        if not self.perform_action_from_memory(
                            curr_activity, target_activity
                        ):
                            print("[+] USING LLMs")
                            self.use_llms(path[i], target_path=path)
                            self.llm_used[target_activity] = True
                    elif self.perform_action_from_memory(
                        curr_activity, target_activity
                    ):
                        i += 1
                        print("[+] USING MEMORY")
                    else:
                        i += 1
                    self.vc.sleep(0.2)
                if self.frida_bool and self.method_reached:
                    break
                if self.methods_por[class_method] > 0:
                    print("[*] PATH SUCCESSFULLY VISITED!\n")
                    break
            if self.frida_bool and self.method_reached:
                print("[*] PATH SUCCESSFULLY VISITED!\n")
                self.methods_por[class_method] += 1
                break
            if self.methods_por[class_method] > 0:
                print("[*] PATH SUCCESSFULLY VISITED!\n")
                break
            print("-" * 100)
        subp.call(f"adb shell am force-stop {self.package_name}", shell=True)
        self.save("")

    def is_app_installed(self):
        adb_packages = subp.Popen(
            "adb shell pm list package", shell=True, stdout=subp.PIPE
        )
        list_packages = adb_packages.communicate()[0].decode()
        installed = False
        for pkg in list_packages.split("\n"):
            if self.package_name in pkg:
                installed = True
        return installed

    def run(self, json_path, target, instructions_dir):
        tot_methods = 0
        self.methods_por = defaultdict(int)
        self.instructions_dir = instructions_dir
        app_name = os.path.splitext(os.path.basename(self.apk_path))[0]
        with open(self.stats_file_path, "r") as stats_file:
            reader = csv.reader(stats_file)
            header = next(reader)
            if header[-1] != "PoR":
                header.append("PoR")
            for row in reader:
                if row[0] == app_name and len(row) >= 8 and not row[8].strip():
                    print("[*] ALREADY ANALYZED")
                    sys.exit(1)
        self.avc_device, serialno = ViewClient.connectToDeviceOrExit(
            serialno=self.get_serialno()
        )

        if self.frida_bool:
            subp.run(
                'adb shell "su -c /data/local/tmp/frida-server -D &"',
                shell=True,
            )
            self.frida_device = frida.get_usb_device()
            self.frida_device.on("spawn-added", self.spawn_added)
            self.frida_device.enable_spawn_gating()

        ViewClient.sleep(0.2)

        self.package_name = self.get_package_name(self.apk_path).replace(
            "'", ""
        )

        if not self.is_app_installed():
            print("[+] INSTALLING APP")
            install_status = subp.Popen(
                ["adb", "install", "-r", "-g", self.apk_path], stderr=subp.PIPE
            )
            print(install_status.communicate())

        if not self.is_app_installed():
            self.update_csv(app_name, tot_methods, self.methods_por)
            print("[+] APP NOT INSTALLED")
            return

        print("[+] INSTALLATION SUCCESSFUL")

        self.start_app(self.package_name)

        if self.manual_setup:
            print("[?] Initial setup (CTRL+C to end)")
            try:
                sys.stdin.read()
            except KeyboardInterrupt:
                pass

        print("[+] CONNECTING TO VIEW CLIENT\n")
        while True:
            try:
                self.vc = ViewClient(self.avc_device, serialno)
                break
            except ValueError:
                pass

        with open(json_path, "r") as json_file:
            json_paths = json.load(json_file)

        self.target_method = target
        if target:
            self.check_method_in_logcat(json_paths)
            self.restart_app(self.package_name)
            self._process_method(target, json_paths)
            tot_methods += 1
        else:
            tot_methods = len(json_paths)
            self.check_method_in_logcat(json_paths)
            self.restart_app(self.package_name)
            for i, class_method in enumerate(json_paths):
                print(f"[+] METHOD {str(i)}/{str(tot_methods)}")
                if class_method in self.methods_por:
                    print(f"[+] METHOD {class_method} ALREADY VISITED")
                    continue
                self.target_method = class_method
                self._process_method(class_method, json_paths)

        # self.uninstall_app(self.package_name)
        self.update_csv(app_name, tot_methods, self.methods_por)

        with open(
            os.path.join(self.output, app_name, app_name + "_run.gaps-log"),
            "w",
        ) as log_file:
            log_file.write(self.log)
