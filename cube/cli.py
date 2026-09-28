"""Command line: print every optimal cross solution for a scramble."""

import sys

from cube.pdb import load_or_build_pdb
from cube.solver import solve_all_optimal


def main():
    scramble = " ".join(sys.argv[1:])
    dist = load_or_build_pdb()
    d, sols = solve_all_optimal(dist, scramble)
    print(f"Optimal cross length: {d}")
    print(f"Number of optimal solutions: {len(sols)}")
    for s in sols:
        print(" ", " ".join(s))


if __name__ == "__main__":
    main()
