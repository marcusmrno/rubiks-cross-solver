# Rubik's Cube Cross Solver + Solve-Time Analysis

An exact solver that finds every optimal cross for a Rubik's cube scramble,
and an analysis that runs it over 750 of my own timed solves to measure how
much the cross a scramble gives me affects the solve.

https://github.com/user-attachments/assets/6e25f812-2135-450c-8972-4e231c9c8108

## Highlights

- **Exact search.** A breadth-first search from the solved state builds a
  pattern database of all 190,080 cross states and their exact distance to
  solved (8 moves at most). A depth-first search pruned by that table then
  lists every optimal solution, skipping move orders that are just
  reorderings of the same solution.
- **Solve data.** A parser for csTimer exports, plus a replay of smart-cube
  turn logs that finds the exact turn where I finished the cross, how many
  moves I used, and whether that was optimal.
- **Statistics.** A least-squares regression written in numpy and checked
  against scipy, measuring the effect of cross length and of the number of
  optimal solutions, each with the other held fixed.
- **Tests.** 62 pytest tests. During development I mutation-checked them:
  I broke the code on purpose and confirmed that a test fails each time.

## What I found

From my own solves: 650 timed on a keyboard (2019–2026) and 100 on a smart
cube that logs every turn. These describe one solver, not cubers in general.

| Finding | Data |
|---|---|
| Each extra move in the optimal cross costs about **0.28 s** per solve | 650 solves, p = 0.0002 |
| ...but cross length explains only about **3%** of the variation in solve time | 650 solves |
| The cross takes **12%** of a solve on average (1.58 s of 13.5 s) | 100 smart-cube solves |
| I find an optimal cross **42%** of the time | 100 smart-cube solves |
| On 6-move crosses I find the optimal one **57%** of the time when the scramble has many optimal solutions, vs **18%** when it has few | 23 vs 28 solves, p = 0.002 |
| Same pattern on 7-move crosses: **64%** vs **18%** | 11 vs 11 solves, p = 0.007 |

So the scramble's cross matters less for raw speed than for whether I find
the best cross at all.

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

## Project layout

| Path | What it does |
|---|---|
| `cube/moves.py` | Edge-only cube model and face turns (corners don't affect the cross, so they aren't tracked) |
| `cube/cross.py` | Reduces a cube state to the 4 cross edges' positions and orientations |
| `cube/pdb.py` | Builds, caches and loads the pattern database |
| `cube/solver.py` | Lists every optimal cross solution |
| `cube/cli.py` | Command-line entry point |
| `analysis/parse_cstimer.py` | Reads csTimer exports, including smart-cube turn logs |
| `analysis/pipeline.py` | Solves each scramble's white cross and replays smart-cube turns |
| `analysis/analyze.py` | Per-length means, regression and plot |

## Tests

    python -m pytest -q
