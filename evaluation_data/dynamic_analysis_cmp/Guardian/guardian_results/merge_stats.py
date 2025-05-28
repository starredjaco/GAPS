import os
import pandas as pd


def compute_avg_stats_and_merge(directory, output_file):
    csv_files = [f for f in os.listdir(directory) if f.endswith(".csv")]
    merged_data = []

    for csv_file in csv_files:
        file_path = os.path.join(directory, csv_file)
        df = pd.read_csv(file_path)

        # Compute averages for the specified columns
        avg_reached_methods = df["reached_methods"].mean()
        avg_percentage_reached = df["percentage_reached"].mean()

        # Append the averages as the last row
        avg_row = {
            "reached_methods": avg_reached_methods,
            "percentage_reached": avg_percentage_reached,
        }
        df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)

        # Save the updated CSV
        # df.to_csv(file_path, index=False)

        # Add the average row to the merged data
        avg_row["file_name"] = csv_file
        merged_data.append(avg_row)

    # Create a final DataFrame with all averages
    merged_df = pd.DataFrame(merged_data)

    # Save the merged DataFrame to the output file
    merged_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    directory = "/home/same/code/gaps/dynamic_analysis_cmp/guardian_results"
    output_file = "/home/same/code/gaps/dynamic_analysis_cmp/guardian_results/final_averages.csv"
    compute_avg_stats_and_merge(directory, output_file)
