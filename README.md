# Rubik's Cube Cross Solver + Solve-Time Correlation

A cross solver that enumerates every optimal cross solution for a scramble,
built on a full pattern database over the reduced cross-edge state space.
Part 2 joins those numbers with real solve times from a csTimer export, to
study how much the cross a scramble gives you affects the solve.

https://github.com/user-attachments/assets/55091fe2-7d9a-424c-ae60-08ccb6013e38

## Setup

    pip install -r requirements.txt

The first run builds the pattern database (about a minute) and caches it in
`pdb_cache.pkl` at the repo root; later runs load it in a fraction of a second.

## Usage

    python -m cube.cli "D2 R' D' F2 B2 U' R2 U' F2 D B2 U2 R' D R' B L2 F' U F2"

Prints the optimal cross length (7 here), the number of optimal solutions (56),
and each solution.

Always quote the scramble. Unquoted, the shell treats the `'` in moves like
`R'` as quote marks, and `R U R' U'` reaches the program as `R U R U`.

The CLI solves the cross on the D face with the cube held as the scramble left
it. Scrambled in WCA orientation (white on top, green in front), that's the
yellow cross. For the white cross, swap U with D and F with B in the scramble
(the pipeline below does this): `R U R' U'` has an intact yellow cross, but
`python -m cube.cli "R D R' D'"` gives the white cross, `D R D' R'`.

## Solve-time analysis

    python -m analysis.analyze cstimer_export.txt

Reads a csTimer export (two-handed 3x3 sessions only) and writes `solves.csv`:
each solve's time, the optimal white-cross length and solution count, and, for
smart-cube solves, when the cross was finished, in how many moves, and the
pause before F2L.

Then, for total time and the three smart-cube outcomes (cross time, whether
the cross was optimal, the pause), it prints the mean at each cross length and
the effect of one more optimal move and of twice as many optimal solutions,
each with the other held fixed. `by_length.png` plots the means.

## Tests

    python -m pytest -q
