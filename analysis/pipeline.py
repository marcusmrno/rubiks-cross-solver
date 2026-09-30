"""Join csTimer solve times with the cross solver's output and write solves.csv.

I scramble with white on top and green in front, then solve the white cross.
The solver always solves the D-face cross, which in scramble orientation is
yellow, so each scramble is relabeled as if the cube were turned over (x2:
U<->D, F<->B) before solving. solves.csv keeps the scramble as csTimer wrote
it, so pasting one from there into `python -m cube.cli` gives the
yellow-cross numbers, not the ones in the file.

On my smart cube, csTimer also records every turn. The cube names a turn by
the center of the face that moved, not by how I'm holding it, so the turns
are in scramble orientation too and get the same relabel. Replaying them
shows when I finished the white cross and in how many moves.
"""

import csv
from itertools import groupby

from analysis.parse_cstimer import load_solves
from cube.cross import cross_key
from cube.moves import apply_move, apply_scramble, solved_edges
from cube.pdb import load_or_build_pdb
from cube.solver import solve_all_optimal

FIELDS = ["scramble", "time_ms", "optimal_length", "num_optimal_solutions", "cross_ms", "cross_moves"]
X2 = str.maketrans("UDFB", "DUBF")
SOLVED_CROSS = cross_key(solved_edges())
QUARTER_TURNS = {"": 1, "2": 2, "'": 3}


def build_dataset(export_path, csv_path="solves.csv"):
    """One row per solve: its time, the optimal white-cross length, and how
    many optimal solutions there are. For a smart-cube solve, also when I
    finished the cross and in how many moves (None for other solves). Also
    writes the rows to csv_path.

    Every run solves every scramble again: 650 take about 7s once the table
    is loaded, so solves.csv is only an output, never read back as a cache.
    """
    dist = load_or_build_pdb()
    rows = []
    for s in load_solves(export_path):
        length, sols = solve_all_optimal(dist, s["scramble"].translate(X2))
        cross_ms, cross_moves = cross_split(s["scramble"], s["turns"]) if s["turns"] else (None, None)
        rows.append({
            "scramble": s["scramble"],
            "time_ms": s["time_ms"],
            "optimal_length": length,
            "num_optimal_solutions": len(sols),
            "cross_ms": cross_ms,
            "cross_moves": cross_moves,
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def cross_split(scramble, turns):
    """When I finished the white cross, and in how many moves.

    Both arguments are as csTimer recorded them; turns is [(move, ms), ...],
    timed from my first turn. Returns (ms, moves) for the turn that first
    completes the cross, or (0, 0) if the scramble left it solved. moves is
    counted the way the solver counts, so it's never below optimal_length,
    and equal to it when I found an optimal cross.
    """
    cubies = apply_scramble(solved_edges(), scramble.translate(X2))
    if cross_key(cubies) == SOLVED_CROSS:
        return 0, 0
    for i, (move, ms) in enumerate(turns):
        cubies = apply_move(cubies, move.translate(X2))
        if cross_key(cubies) == SOLVED_CROSS:
            return ms, _count_moves([m for m, _ in turns[:i + 1]])
    raise ValueError(f"the turns never solve the white cross of {scramble!r}")


def _count_moves(turns):
    """Count moves the way the solver does: turns of one face in a row are
    one move (R R is R2), or none if they cancel out (R R').
    """
    # Only neighbors merge: R U U' R' counts 2, though it all cancels. Fine
    # while misturns like that are rare; a full cancel pass would fix it.
    return sum(1 for _face, run in groupby(turns, key=lambda m: m[0])
               if sum(QUARTER_TURNS[m[1:]] for m in run) % 4)
