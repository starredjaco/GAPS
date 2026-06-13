import argparse
import json
import os
from androguard.misc import AnalyzeAPK


def to_java(smali_name):
    return smali_name[1:-1].replace("/", ".")


def parse_seed_file(seed_file_path):
    with open(seed_file_path, "r") as f:
        classes = [
            to_java(line.strip().split("->")[0]) for line in f if line.strip()
        ]
    return classes


def get_activity_methods(apk_path):
    try:
        a, d, dx = AnalyzeAPK(apk_path)
    except Exception as e:
        print(f"Failed to analyze APK {apk_path}: {e}")
        return set()
    activity_classes = set(a.get_activities())
    print(activity_classes)

    return activity_classes


def collect_call_sequence_lengths(results_file_path):
    try:
        with open(results_file_path, "r") as f:
            results_data = json.load(f)
    except Exception as e:
        print(f"Failed to read results JSON {results_file_path}: {e}")
        return []

    call_sequence_lengths = []
    for target_method_data in results_data.values():
        if not isinstance(target_method_data, dict):
            continue

        for path_data in target_method_data.values():
            if not isinstance(path_data, dict):
                continue

            call_sequence = path_data.get("call_sequence", [])
            if isinstance(call_sequence, list):
                tool_call_count = sum(
                    1
                    for call in call_sequence
                    if call != "----- CONDITIONAL -----"
                )
                call_sequence_lengths.append(tool_call_count)

    return call_sequence_lengths


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Count seed methods in activities and call-sequence statistics "
            "for each app."
        )
    )
    parser.add_argument(
        "--apps_dir", required=True, help="Directory containing app folders"
    )
    parser.add_argument(
        "--seeds_dir", required=True, help="Directory containing .seed files"
    )
    parser.add_argument(
        "--results_dir",
        help=(
            "Directory containing app folders with <app_name>-instr.json "
            "files"
        ),
    )
    args = parser.parse_args()

    total_found = 0
    total_methods = 0
    app_count = 0
    app_dir = args.apps_dir
    for seed_file in os.listdir(args.seeds_dir):
        if not seed_file.endswith(".seed"):
            continue
        app_name = seed_file.replace(".seed", "")
        seed_file_path = os.path.join(args.seeds_dir, seed_file)

        if not os.path.isdir(app_dir):
            print(f"App directory not found for {app_name}")
            continue

        apk_path = os.path.join(app_dir, app_name + ".apk")

        seed_methods = parse_seed_file(seed_file_path)
        activity_methods = get_activity_methods(apk_path)

        count_in_activities = sum(
            1 for m in seed_methods if m in activity_methods
        )
        total = len(seed_methods)
        percentage = (count_in_activities / total * 100) if total > 0 else 0
        print(
            f"{app_name}: {count_in_activities}/{total} methods found in "
            f"activities ({percentage:.2f}%)"
        )

        total_found += count_in_activities
        total_methods += total
        app_count += 1

    avg_percentage = (
        (total_found / total_methods * 100) if total_methods > 0 else 0
    )
    print(
        f"Average: {total_found}/{total_methods} methods found in "
        f"activities across {app_count} apps ({avg_percentage:.2f}%)"
    )

    if not args.results_dir:
        return

    total_sequences = 0
    total_sequence_length = 0
    min_sequence_length = None
    max_sequence_length = None
    apps_with_average_at_least_five = 0
    app_count = 0

    for app_name in sorted(os.listdir(args.results_dir)):
        app_results_dir = os.path.join(args.results_dir, app_name)
        if not os.path.isdir(app_results_dir):
            continue

        results_file_path = os.path.join(
            app_results_dir, f"{app_name}-instr.json"
        )
        if not os.path.isfile(results_file_path):
            print(f"Results JSON not found for {app_name}")
            continue

        call_sequence_lengths = collect_call_sequence_lengths(
            results_file_path
        )
        if not call_sequence_lengths:
            print(f"{app_name}: no call sequences found")
            continue

        app_sequences = len(call_sequence_lengths)
        app_total_length = sum(call_sequence_lengths)
        app_average = app_total_length / app_sequences
        app_min = min(call_sequence_lengths)
        app_max = max(call_sequence_lengths)

        print(
            f"{app_name}: {app_sequences} call sequences, min={app_min}, "
            f"max={app_max}, avg={app_average:.2f}"
        )

        if app_average >= 5:
            apps_with_average_at_least_five += 1

        total_sequences += app_sequences
        total_sequence_length += app_total_length
        min_sequence_length = (
            app_min
            if min_sequence_length is None
            else min(min_sequence_length, app_min)
        )
        max_sequence_length = (
            app_max
            if max_sequence_length is None
            else max(max_sequence_length, app_max)
        )
        app_count += 1

    overall_average = (
        total_sequence_length / total_sequences if total_sequences > 0 else 0
    )
    overall_min = min_sequence_length if min_sequence_length is not None else 0
    overall_max = max_sequence_length if max_sequence_length is not None else 0
    print(
        f"Call-sequence average: {total_sequences} sequences across "
        f"{app_count} apps, min={overall_min}, max={overall_max}, "
        f"avg={overall_average:.2f}"
    )
    print(
        f"Apps with average call sequence length at least 5: "
        f"{apps_with_average_at_least_five}"
    )


if __name__ == "__main__":
    main()
