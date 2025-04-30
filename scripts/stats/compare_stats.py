import csv
import sys

def load_reached_methods(csv_path):
    data = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            app = row['APP']
            try:
                reached = int(row['REACHED METHODS'])
                data[app] = reached
            except ValueError:
                print(f"Warning: Non-integer value for APP {app} in {csv_path}")
    return data

def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_reached_methods.py old.csv new.csv")
        sys.exit(1)

    old_csv = sys.argv[1]
    new_csv = sys.argv[2]

    old_data = load_reached_methods(old_csv)
    new_data = load_reached_methods(new_csv)

    deltas = []
    for app, new_value in new_data.items():
        old_value = old_data.get(app)
        if old_value is not None:
            delta = new_value - old_value
            deltas.append((app, delta, old_value, new_value))

    # Sort by absolute delta
    deltas.sort(key=lambda x: abs(x[1]), reverse=True)

    print("Top changes in REACHED METHODS:\n")
    for app, delta, old_val, new_val in deltas[:10]:  # Top 10 changes
        change = "improved" if delta > 0 else "regressed" if delta < 0 else "unchanged"
        print(f"{app}: {change} by {delta} (was {old_val}, now {new_val})")

if __name__ == "__main__":
    main()
