import os
import sys

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} app_directory results")
    sys.exit(1)

app_path = str(sys.argv[1])
results = str(sys.argv[2])
apps = os.listdir(app_path)

logs = []
for app in apps:
    file_name = os.path.splitext(os.path.basename(app))[0]
    log_name = file_name + ".gaps-log"
    log_path = os.path.join(results, file_name, log_name)
    if os.path.exists(log_path):
        logs.append(log_path)

extends_and_implements_path_recon_stats = {}
extends_path_recon_stats = {}
implements_path_recon_stats = {}
id_retrieval_stats = {}
tot_entries = 0
tot_entries_extends = 0
tot_entries_implements = 0
tot_entries_id = 0
which_apps = {}

for log_path in logs:
    app_name = log_path.split("/")[-1]
    with open(log_path, "r") as log_file:
        log_lines = log_file.readlines()
        for log_line in log_lines:
            if log_line.strip():
                if log_line.startswith("COMPONENT CONCAT"):
                    tot_entries += 1
                    split_where = " < "
                    if split_where not in log_line:
                        split_where = "PRESS MENU"
                    extends_implements = log_line.split(split_where)[1]
                    if "}" in extends_implements:
                        extends_implements = extends_implements.split("}")[-1]
                    if (
                        extends_implements.rstrip()
                        not in extends_and_implements_path_recon_stats
                    ):
                        extends_and_implements_path_recon_stats[
                            extends_implements.rstrip()
                        ] = 0
                    extends_and_implements_path_recon_stats[
                        extends_implements.rstrip()
                    ] += 1
                    extends = (
                        extends_implements.split(",")[0]
                        .split("extends")[1]
                        .strip()
                    )
                    implements = extends_implements.split("implements")[
                        1
                    ].strip()
                    if extends:
                        tot_entries_extends += 1
                        if ";" in extends:
                            extends = extends.replace(";", "")
                        if extends not in extends_path_recon_stats:
                            extends_path_recon_stats[extends] = 0
                        extends_path_recon_stats[extends] += 1
                        if extends not in which_apps:
                            which_apps[extends] = set()
                        which_apps[extends].add(app_name)
                    if implements:
                        tot_entries_implements += 1
                        implements = implements.replace("[", "").replace(
                            "]", ""
                        )
                        implements_splits = implements.split(",")
                        for implements_split in implements_splits:
                            if implements_split.strip():
                                if ";" in implements_split:
                                    implements_split = (
                                        implements_split.replace(";", "")
                                    )
                                if (
                                    implements_split
                                    not in implements_path_recon_stats
                                ):
                                    implements_path_recon_stats[
                                        implements_split
                                    ] = 0
                                implements_path_recon_stats[
                                    implements_split
                                ] += 1
                                if implements_split not in which_apps:
                                    which_apps[implements_split] = set()
                                which_apps[implements_split].add(app_name)
                else:
                    callback = log_line.split("->")[1].split("<")[0]
                    if callback.strip():
                        tot_entries_id += 1
                        if callback not in id_retrieval_stats:
                            id_retrieval_stats[callback] = 0
                        id_retrieval_stats[callback] += 1

print("[+] PATH RECON STATS")
sorted_extends_implements = {
    k: v
    for k, v in sorted(
        extends_and_implements_path_recon_stats.items(),
        key=lambda item: item[1],
    )
}
print("\t[+] EXTENDS IMPLEMENTS")
for extend_implement in sorted_extends_implements:
    print(
        extend_implement
        + " : "
        + str(sorted_extends_implements[extend_implement])
        + " / "
        + str(tot_entries)
    )

print("\t[+] END EXTENDS IMPLEMENTS")
sorted_extends = {
    k: v
    for k, v in sorted(
        extends_path_recon_stats.items(), key=lambda item: item[1]
    )
}
print("\t[+] EXTENDS")
for extend in sorted_extends:
    print(
        extend
        + " : "
        + str(sorted_extends[extend])
        + " / "
        + str(tot_entries_extends)
        + " "
        + str(which_apps[extend])
    )

print("\t[+] END EXTENDS")
sorted_implements = {
    k: v
    for k, v in sorted(
        implements_path_recon_stats.items(), key=lambda item: item[1]
    )
}
print("\t[+] IMPLEMENTS")
for implement in sorted_implements:
    print(
        implement
        + " : "
        + str(sorted_implements[implement])
        + " / "
        + str(tot_entries_implements)
        + " "
        + str(which_apps[implement])
    )

print("\t[+] END IMPLEMENTS")
sorted_ids_retrieval = {
    k: v
    for k, v in sorted(id_retrieval_stats.items(), key=lambda item: item[1])
}
print("\t[+] MISSING IDs")
for id_retrieval in sorted_ids_retrieval:
    print(
        id_retrieval
        + " : "
        + str(sorted_ids_retrieval[id_retrieval])
        + " / "
        + str(tot_entries_id)
    )

print("\t[+] END MISSING IDs")
