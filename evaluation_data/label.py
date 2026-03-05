import argparse
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


def main():
    parser = argparse.ArgumentParser(
        description="Count seed methods in activities for each app."
    )
    parser.add_argument(
        "--apps_dir", required=True, help="Directory containing app folders"
    )
    parser.add_argument(
        "--seeds_dir", required=True, help="Directory containing .seed files"
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
            f"{app_name}: {count_in_activities}/{total} methods found in activities ({percentage:.2f}%)"
        )

        total_found += count_in_activities
        total_methods += total
        app_count += 1

    avg_percentage = (
        (total_found / total_methods * 100) if total_methods > 0 else 0
    )
    print(
        f"Average: {total_found}/{total_methods} methods found in activities across {app_count} apps ({avg_percentage:.2f}%)"
    )


if __name__ == "__main__":
    main()
