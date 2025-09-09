import os
import json
import csv
import sys


def process_stats_file(results_directory):
    stats_file = os.path.join(results_directory, "stats.csv")
    if not os.path.exists(stats_file):
        print(f"Stats file not found: {stats_file}")
        return

    stats_data = []
    with open(stats_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            stats_data.append(row)

    # Calculate averages for Analysis Time and Max RAM Usage
    if stats_data:
        total_analysis_time = sum(
            float(row["Analysis Time (s)"]) for row in stats_data
        )
        total_max_ram_usage = sum(
            float(row["Max RAM Usage (MB)"]) for row in stats_data
        )
        num_entries = len(stats_data)

        average_analysis_time = total_analysis_time / num_entries
        average_max_ram_usage = total_max_ram_usage / num_entries

        # Append the averages as the last row
        stats_data.append(
            {
                "App Name": "Overall Average",
                "Analysis Time (s)": "{:.2f}".format(average_analysis_time),
                "Max RAM Usage (MB)": "{:.2f}".format(average_max_ram_usage),
            }
        )

        # Write the updated stats back to the file
        with open(stats_file, "w", newline="") as csvfile:
            fieldnames = [
                "App Name",
                "Analysis Time (s)",
                "Max RAM Usage (MB)",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stats_data)

    print(f"Updated stats written to {stats_file}")


def to_java_signature(smali_sig):
    class_name_smali, params_and_return = smali_sig.split(";->")
    class_name = class_name_smali[1:].replace("/", ".")
    return f"<{class_name}: {params_and_return}>"


def java_to_dalvik_type_reverse(dtype):
    reverse_mapping = {
        "I": "int",
        "V": "void",
        "Z": "boolean",
        "C": "char",
        "B": "byte",
        "S": "short",
        "J": "long",
        "F": "float",
        "D": "double",
    }
    return reverse_mapping.get(dtype, dtype)


def extract_methods_from_seed(seed_file):
    with open(seed_file, "r") as f:
        return [line.strip() for line in f.readlines()]


def check_reachability_in_callgraph(callgraph_file, methods):
    with open(callgraph_file, "r") as f:
        callgraph = json.load(f)

    # Extract all destination methods from the callgraph edges
    reachable_methods = {edge["dst"] for edge in callgraph.get("edges", [])}

    # Check which of the provided methods are reachable
    reached = [method for method in methods if method in reachable_methods]
    return reached


def main(results_directory, testing_seeds_dir, dataset_dir, output_csv):
    results = []

    subdirectories = [
        os.path.join(results_directory, d)
        for d in os.listdir(results_directory)
        if os.path.isdir(os.path.join(results_directory, d))
    ]

    for subdir in subdirectories:
        app_name = os.path.basename(subdir)
        androtest_path = os.path.join(dataset_dir, f"{app_name}.apk")
        callgraph_file = os.path.join(subdir, "callgraph.json")
        seed_file = os.path.join(testing_seeds_dir, f"{app_name}.seed")

        if (
            os.path.exists(callgraph_file)
            and os.path.exists(seed_file)
            and os.path.exists(androtest_path)
        ):
            methods = extract_methods_from_seed(seed_file)
            java_methods = [to_java_signature(method) for method in methods]
            reached_methods = check_reachability_in_callgraph(
                callgraph_file, java_methods
            )

            results.append(
                {
                    "app_name": app_name,
                    "reached_methods": len(reached_methods),
                    "total_methods": len(java_methods),
                    "percentage_reached": (
                        (len(reached_methods) / len(java_methods)) * 100
                        if len(java_methods) > 0
                        else 0
                    ),
                }
            )

    # Calculate overall average
    if results:
        overall_average = sum(
            result["percentage_reached"] for result in results
        ) / len(results)
        results.append(
            {
                "app_name": "Overall Average",
                "reached_methods": "",
                "total_methods": "",
                "percentage_reached": "{:.2f}".format(overall_average),
            }
        )

    # Write results to CSV
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = [
            "app_name",
            "reached_methods",
            "total_methods",
            "percentage_reached",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Reachability stats written to {output_csv}")


# Example usage
if __name__ == "__main__":

    if len(sys.argv) != 4:
        print(
            "Usage: python check_reachability.py <results_directory> <testing_seeds_dir> <dataset_dir>"
        )
        sys.exit(1)

    results_directory = sys.argv[1]
    testing_seeds_dir = sys.argv[2]
    dataset_dir = sys.argv[3]
    output_csv = os.path.join(
        results_directory, "final_reachability_stats.csv"
    )
    main(results_directory, testing_seeds_dir, dataset_dir, output_csv)

    process_stats_file(results_directory)
