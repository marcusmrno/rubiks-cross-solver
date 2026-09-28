"""Join csTimer solve times with the cross solver's output and write solves.csv.

I scramble with white on top and green in front, then solve the white cross.
The solver always solves the D-face cross, which in scramble orientation is
yellow, so each scramble is relabeled as if the cube were turned over (x2:
U<->D, F<->B) before solving. solves.csv keeps the scramble as csTimer wrote
it, so pasting one from there into `python -m cube.cli` gives the
yellow-cross numbers, not the ones in the file.
"""

import csv

from analysis.parse_cstimer import load_solves
from cube.pdb import load_or_build_pdb
from cube.solver import solve_all_optimal

FIELDS = ["scramble", "time_ms", "optimal_length", "num_optimal_solutions"]
X2 = str.maketrans("UDFB", "DUBF")


def build_dataset(export_path, csv_path="solves.csv"):
    """One row per solve: its time, the optimal white-cross length, and how
    many optimal solutions there are. Also writes the rows to csv_path.

    Every run solves every scramble again: 650 take about 7s once the table
    is loaded, so solves.csv is only an output, never read back as a cache.
    """
    dist = load_or_build_pdb()
    rows = []
    for s in load_solves(export_path):
        length, sols = solve_all_optimal(dist, s["scramble"].translate(X2))
        rows.append({
            "scramble": s["scramble"],
            "time_ms": s["time_ms"],
            "optimal_length": length,
            "num_optimal_solutions": len(sols),
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows
