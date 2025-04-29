import subprocess
import random
import re
import os
import sys
import logging
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import method_utils
from . import myAndroguard

###############################################################################
# LOGGING
###############################################################################

LOG = logging.getLogger("gaps")

###############################################################################
# GLOBALS
###############################################################################

MAX_THREADS = 8

icc_methods = [
    "startService",
    "startForegroundService",
    "bindService",
    "bindIsolatedService",
    "bindServiceAsUser",
    "startIntentSender",
    "startActivity",
    "startActivityForResult",
    "startActivities",
    "sendBroadcast",
    "sendBroadcastAsUser",
    "sendBroadcastWithMultiplePermissions",
    "sendOrderedBroadcast",
    "sendOrderedBroadcastAsUser",
    "sendStickyBroadcast",
    "sendStickyBroadcastAsUser",
    "sendStickyOrderedBroadcast",
    "sendStickyOrderedBroadcastAsUser",
    "registerReceiver",
    "setContent",
    "setIntent",
]

ARTIFACTS_DIR = Path(__file__).parent.parent.parent.parent / "artifacts"

ANDROLIBZOO = ARTIFACTS_DIR / "smaliAndroLibZoo.lst"


###############################################################################
# CODE
###############################################################################


def disassemble(gaps):
    """
    Disassembles the app

    Args:
        gaps (object): Instance of GAPS.

    Returns:
        None
    """
    all_methods = [defaultdict(set), defaultdict(set)]

    starting_points_set = str(set(gaps.starting_points.keys()))
    analysis_blacklist = set()

    with ANDROLIBZOO.open() as f:
        for pkg in map(str.strip, f):
            if pkg not in starting_points_set and pkg not in gaps.package_name:
                analysis_blacklist.add(pkg)

    args = []
    method_objs = gaps.method_objs
    method_index = gaps.method_index

    def filter_method(method):
        """Filters methods and prepares arguments for processing."""
        nonlocal method_index  # Avoid repeated attribute access

        if method.is_android_api():
            return None  # Skip API methods

        m = method.get_method()
        method_name = str(m)  # Convert to string once

        class_name_parent, _ = method_utils.get_class_and_method(
            method_name, True
        )

        if any(
            class_name_parent.startswith(pkg) for pkg in analysis_blacklist
        ):
            return None  # Skip methods from blacklisted packages

        method_objs[method_index] = method

        result = [gaps, method, method_index, all_methods]
        method_index += 1
        return result

    # Process methods in parallel
    with ThreadPoolExecutor() as executor:
        results = executor.map(filter_method, gaps.dx.get_methods())

    # Filter out None results and add to args
    args.extend(filter(None, results))

    # Run process_method() in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_method, *x) for x in args]

    # Wait for all futures to complete
    for _ in as_completed(futures):
        pass

    save_testing_seeds(gaps, all_methods)

    # Update method index after processing
    gaps.method_index = method_index


def process_method(gaps, method, method_index: int, all_methods: list) -> str:
    """
    Processes the methods during disassembly.

    Args:
        gaps (object): Instance of GAPS.
        method (object): Method object.
        method_index (int): Index of the method.
        combined (str): Combined blacklist patterns.
        all_methods (list): List of all methods.

    Returns:
        str: Completion status message.
    """
    parent_method = _get_method_name(method)
    class_name_parent, method_name_parent = method_utils.get_class_and_method(
        parent_method, True
    )

    if ";->" in parent_method:
        rest_signature_parent = parent_method.split(";->", 1)[1].split()[0]
        gaps.all_methods[rest_signature_parent].add(parent_method)
    for (
        bb
    ) in method.get_basic_blocks():  # No need to store basic blocks in a list
        for (
            instruction
        ) in bb.get_instructions():  # Process instructions lazily
            inst_out = instruction.get_output()

            # Optimize string manipulation
            if "(" in inst_out:
                inst_out = inst_out.replace(" ", "").replace(",", ", ")

            # Use f-string instead of format()
            str_inst = f"{instruction.get_name()} {inst_out}"

            process_instr(
                gaps,
                str_inst,
                method,
                method_index,
                parent_method.split()[1],
                class_name_parent,
                all_methods,
            )

    return "finish"


def process_instr(
    gaps,
    str_inst: str,
    method,
    entry: int,
    parent_method: str,
    class_name_parent: str,
    all_methods: list,
):
    """
    Processes instructions during disassembly.

    Args:
        gaps (object): Instance of GAPS.
        str_inst (str): Instruction string.
        method: Method object.
        method_index (int): Index of the method.
        all_methods (list): List of all methods.

    Returns:
        None
    """
    class_name, method_name = method_utils.get_class_and_method(str_inst, True)
    instr_type = str_inst.split()[0]

    instr_sig = str_inst.split()[-1]

    if (
        any(op in instr_type for op in ("put", "get"))
        and ";->" in str_inst
        and "this$0" not in str_inst
    ):
        rest_of_signature = str_inst.split("->", 1)[1].split()[0]
        gaps.signature_to_address[method_name][rest_of_signature][
            class_name
        ].add(entry)

        object_type = instr_sig
        if ";" in object_type:
            gaps.object_instantiated[object_type.split(";")[0]].add(entry)
        return

    elif "check-cast" in instr_type:
        object_type = instr_sig
        if ";" in object_type:
            gaps.object_instantiated[object_type.split(";")[0]].add(entry)
        return

    elif "const-class" == instr_type:
        string_class = instr_sig.replace(";", "")
        gaps.icc_string_analysis[string_class].add(entry)
        return

    elif "sparse-switch" in str_inst or "packed-switch" in str_inst:
        if parent_method not in gaps.methods_with_switches:
            method_body = myAndroguard.get_whole_method(
                method.basic_blocks.get()
            )
            gaps.methods_with_switches[parent_method] = method_body
        return

    elif "return" in instr_type and "return-void" not in instr_type:
        gaps.return_by[parent_method].add(entry)
        return

    # Optimize "invoke" processing
    if "invoke" in instr_type and "this$0" not in str_inst:
        rest_of_signature = str_inst.split("->", 1)[1]
        gaps.signature_to_address[method_name][rest_of_signature][
            class_name
        ].add(entry)

        if (
            not (gaps.target_method or gaps.signature)
            and gaps.save_testing_seeds
        ):
            index = 0 if gaps.package_name in class_name else 1
            all_methods[index][instr_sig].add(entry)

    if method_name in icc_methods or "Landroid/app/PendingIntent;" in str_inst:
        gaps.icc_method_addresses[instr_sig].add(entry)

    if ";->access$" in parent_method:
        gaps.access_methods[parent_method] = str_inst

    if gaps.target_method:
        if (
            method_name == gaps.target_method
            and "invoke" in instr_type
            and (not gaps.class_name or gaps.class_name == class_name)
            and (
                not gaps.parent_class or gaps.parent_class in class_name_parent
            )
        ):
            gaps.starting_points[instr_sig].add(entry)

    elif gaps.class_name == class_name and (
        not gaps.parent_class or gaps.parent_class in class_name_parent
    ):
        gaps.starting_points[instr_sig].add(entry)

    elif (
        (gaps.seed_file or gaps.signature)
        and instr_sig in gaps.starting_points
        and "invoke" in instr_type
    ):
        gaps.starting_points[instr_sig].add(entry)

    elif gaps.custom_seeds and method_name in gaps.custom_seeds:
        for custom_seed in gaps.custom_seeds[method_name]:
            if (
                custom_seed["class_name"].strip() == class_name
                and custom_seed["parent_class"] == class_name_parent
            ):
                gaps.starting_points[instr_sig].add(entry)


def _get_method_name(method):
    """
    Retrieves the method name.

    Args:
        method: Method object.

    Returns:
        str: Method name.
    """
    method_name = str(method).replace("<analysis.MethodAnalysis", "")
    method_name = method_name[: len(method_name) - 1]
    method_name = "".join(method_name.split())
    if "[access" in method_name:
        method_name = method_name.split("[access")[0].replace(" ", "")
    return f"> {method_name} <"


def basic_blocks_2_graph(
    gaps,
    method,
) -> defaultdict:
    """
    Converts basic blocks to a graph representation.

    Args:
        gaps (object): Instance of GAPS.
        method: Method object.

    Returns:
        defaultdict: Graph representation of basic blocks.
    """
    graph = defaultdict(set)
    m = method.get_method()
    method_name = _get_method_name(method)
    if method_name in gaps.search_list:
        return gaps.search_list[method_name]
    offset_method = m.get_address()
    translate = dict()
    translate[-1] = method_name
    basic_blocks = method.get_basic_blocks()
    for bb in basic_blocks:
        instructions = list(bb.get_instructions())
        offset_inst = bb.get_start() + offset_method
        for inst in instructions[:-1]:
            inst_out = inst.get_output()
            if "(" in inst_out:
                inst_out = inst_out.replace(" ", "").replace(",", ", ")
            str_inst = "{} {}".format(inst.get_name(), inst_out)
            translate[offset_inst] = str_inst

            next_inst_offset = offset_inst + inst.get_length()

            graph[next_inst_offset].add(offset_inst)

            offset_inst = next_inst_offset
        # multiple destinations ?
        last_inst = instructions[-1]
        # node
        inst_out = last_inst.get_output()
        if "(" in inst_out:
            inst_out = inst_out.replace(" ", "").replace(",", ", ")
        str_inst = "{} {}".format(last_inst.get_name(), inst_out)
        translate[offset_inst] = str_inst
        # edges
        for child in bb.childs:
            child_offset = child[1] + offset_method
            graph[child_offset].add(offset_inst)
    gaps.search_list[method_name] = graph, translate
    return graph, translate


def save_testing_seeds(gaps, all_methods: list):
    """
    Saves testing seeds.

    Args:
        gaps (object): Instance of GAPS.
        all_methods (list): List of all methods.

    Returns:
        None
    """
    if not gaps.save_testing_seeds:
        return
    max_random_methods = 50
    random_method = 0
    methods_list = list(all_methods[0].keys())
    meth_dict = all_methods[0]
    step = 0
    while random_method < max_random_methods:
        if len(methods_list) == 0:
            methods_list = list(all_methods[1].keys())
            if len(methods_list) == 0:
                break
            meth_dict = all_methods[1]
            step += 1
            if step == 2:
                break
        random_index = random.randint(0, len(methods_list) - 1)
        picked_method = methods_list[random_index]
        gaps.starting_points[picked_method] = meth_dict[picked_method]
        random_method += 1
        gaps.testing_seeds += picked_method + "\n"
        methods_list.pop(random_index)


def resolve_access_method(access_signature: str, gaps) -> str:
    """
    Resolves access methods.

    Args:
        access_signature (str): Access signature.
        gaps (object): Instance of GAPS.

    Returns:
        str: Resolved access method.
    """
    if access_signature in gaps.access_methods:
        return gaps.access_methods[access_signature]
    return ""


def run_apktool(gaps):
    """
    Runs apktool for disassembly.

    Args:
        gaps (object): Instance of GAPS.

    Returns:
        None
    """
    LOG.info(f"[+] STARTING APK DISASSEMBLY IN {gaps.tmp_path}")
    cmd = f'apktool d -f --no-assets "{gaps.dalvik_path}" -o "{gaps.tmp_path}"'
    subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not os.path.exists(gaps.tmp_path):
        LOG.error("[-] ERROR IN DISASSEMBLY")
        sys.exit(0)
    LOG.info(f"[+] DISASSEMBLED IN {gaps.tmp_path}")


def run_baksmali(gaps):
    """
    Runs baksmali for disassembly.

    Args:
        gaps (object): Instance of GAPS.

    Returns:
        None
    """
    LOG.info(f"[+] STARTING DEX DISASSEMBLY IN {gaps.tmp_path}")
    subprocess.run(
        f'baksmali d "{gaps.dalvik_path}" -o "{gaps.tmp_path}"',
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not os.path.exists(gaps.tmp_path):
        LOG.error("[-] ERROR IN DISASSEMBLY")
        sys.exit(0)
    LOG.info(f"[+] DISASSEMBLED IN {gaps.tmp_path}")
