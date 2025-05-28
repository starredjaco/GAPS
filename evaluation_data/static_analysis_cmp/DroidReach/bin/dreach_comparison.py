#!/usr/bin/env python3

import logging
import argparse
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from apk_analyzer import APKAnalyzer


def main(args):
    if not args.apk and not args.targets_file_path:
        return 1

    apk_path = args.apk

    targets_file_path = args.targets_file_path

    targets = []

    with open(targets_file_path) as targets_file:
        targets = [t.strip() for t in targets_file.readlines()]

    use_flowdroid = False
    if args.use_flowdroid:
        use_flowdroid = True

    if args.verbose:
        APKAnalyzer.log.setLevel(logging.INFO)

    apka = APKAnalyzer(apk_path, use_flowdroid=use_flowdroid)

    apka.get_paths_to_java_methods(targets)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DroidReach APK analyzer")
    parser.add_argument(
        "--use-flowdroid",
        help="Use flowdroid to generate the Java callgraph",
        action="store_true",
    )
    parser.add_argument("--verbose", help="Verbose mode", action="store_true")

    parser.add_argument("apk", help="The binary to analyze")

    parser.add_argument(
        "targets_file_path", help="File containing the targets"
    )

    args = parser.parse_args()
    exit(main(args))
