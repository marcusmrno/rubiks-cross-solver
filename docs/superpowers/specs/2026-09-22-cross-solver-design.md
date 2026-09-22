# Rubik's Cube Cross Solver + Solve-Time Correlation — Design

## Goal

A resume-worthy 10-day CS project in two parts, built by the user (Marcus) for learning — Claude provides design/spec/plan only, not code:

1. **Cross Solver**: given a WCA scramble, compute the optimal cross-solution length and enumerate *every* distinct optimal solution (not just one).
2. **Correlation Analysis**: using Marcus's own csTimer solve history, test whether the number of optimal cross solutions available for a scramble correlates with how fast he actually solved it — i.e. does having more options during inspection make the cross (and by extension the solve) faster to find and execute.

## Non-goals

- Solving beyond the cross (F2L/OLL/PLL) is out of scope.
- No GUI; a CLI/scriptable library is sufficient.
- No symmetry reduction in the pattern database — the state space is small enough (~190k states) that this adds complexity without practical benefit.
- No separate inspection-time logging — the analysis uses total solve time from csTimer as-is (see Open Questions).

## Architecture

Two independent, connected-by-a-file pieces:

```
Part 1: Cross Solver               Part 2: Correlation Analysis
┌─────────────────────┐            ┌──────────────────────────┐
│ cube/moves.py         │            │ parse_cstimer.py           │
│ cube/pdb.py (BFS)     │            │  → scramble, time, penalty │
│ cube/solver.py         │  scramble  │ join on scramble             │
│  (enumerate optimal    │──────────▶│ analysis.py                  │
│   solutions per        │  results   │  → correlation, regression   │
│   scramble)             │  CSV       │  → scatter plot                │
└─────────────────────┘            └──────────────────────────┘
```

Part 1 is a standalone, independently testable library: given any WCA scramble string, it returns `(optimal_length, num_optimal_solutions, [solution move lists])`. Part 2 never touches cube internals — it calls Part 1 per scramble and joins the result with csTimer times.

This split gives two independently demoable artifacts: Part 1 is an "algorithms" piece (paste a scramble, get all optimal cross solutions), Part 2 is a "data analysis" piece (a real correlation study on real data).

## Part 1 — Cross Solver

### State representation

Track only the 4 cross-edge pieces as `(position 0–11, orientation 0/1)` each. Corners and the other 8 edges are irrelevant to cross and are never simulated. Total reachable states: `12 × 11 × 10 × 9 × 2^4 = 190,080`.

### Move tables

Precompute, for each of the 18 face turns (U/U'/U2, D/D'/D2, R/R'/R2, L/L'/L2, F/F'/F2, B/B'/B2), how it permutes the 12 edge-position labels and flips orientation. One-time lookup table, not per-move simulation from scratch.

### Pattern database (PDB)

Single BFS from the solved cross state over all 190,080 states, storing the exact optimal distance for every state. Built once, cached to disk (`pdb.pkl`), reused for every scramble solved afterward.

### Per-scramble solve

1. Parse the WCA scramble string.
2. Apply its moves from the solved cross state to land on state `s`.
3. Look up `d = pdb[s]` — this *is* the optimal cross length, no search required.
4. Depth-`d` DFS from `s` toward solved, pruned via the exact PDB (only descend into children whose distance-to-goal equals remaining depth). This enumerates every optimal-length solution path with no wasted exploration, since the heuristic is exact.

### Canonicalization (dedup)

Two move sequences that differ only by reordering independent moves (e.g. `R L` vs `L R`, since R and L act on disjoint pieces) represent the same physical solution and should not be double-counted. Enforce a fixed order between opposite-face moves during enumeration (e.g. always emit `U` before `D` when both appear consecutively/interchangeably) so trivially-reordered duplicates collapse into one canonical form.

### Output

Per scramble: `(optimal_length, num_optimal_solutions, list_of_solutions)`.

## Part 2 — Data Pipeline & Analysis

### Parsing the csTimer export

csTimer's export JSON has a shape roughly like `session1: [[[penalty, time_ms], scramble, comment], ...]` (exact shape to be confirmed against a real export when this phase starts — see Open Questions). Extract `(scramble, time_ms, penalty)`. Drop DNFs. For `+2` penalties, add 2000ms to the recorded time (standard WCA handling) rather than dropping them.

### Join

For each scramble in the parsed history, run it through the Part 1 solver to get `num_optimal_solutions` at that scramble's own optimal length. Join with `time_ms` into one table (pandas DataFrame), cached to `solves.csv` so re-runs don't re-solve every scramble.

### Analysis

- Pearson and Spearman correlation between `num_optimal_solutions` and `time_ms`.
- Simple regression (linear, and log-x since solution counts likely skew) to quantify the effect size, not just detect it.
- Scatter plot of `num_optimal_solutions` vs `time_ms` with the fit line overlaid (matplotlib).

## Key decisions (from design discussion)

- **Time metric**: total solve time from csTimer, as-is. No separate inspection-time logging.
- **Solution-count metric**: for each scramble, count solutions at *that scramble's own optimal length* (not a fixed move count like "always 6").
- **Dedup**: canonicalize independent-move reorderings so they count as one solution (see above).
- **Language**: Python throughout — the state space is small enough that pure Python is fast, and it keeps the solver and the pandas/matplotlib analysis in one language.
- **Solver algorithm**: precomputed pattern database (BFS once from solved, reused for every scramble), not per-scramble IDA* — this is what makes enumerating *all* optimal solutions fast, and what makes batch-processing an entire solve history practical.

## Testing & Validation

- Unit tests for the move tables: a few known short scrambles with hand-verified optimal cross length.
- Sanity check: the PDB's max value should equal the known worst-case optimal cross length for a Rubik's cube cross (8 moves per existing cubing research) — a good assertion to catch move-table bugs early.
- Solver regression test: a scramble with a documented optimal solution count (from speedcubing forums/tools) checked against this solver's output.

## Open Questions (to resolve when that phase starts)

- Exact shape of the csTimer export JSON (session key names, whether multiple sessions need merging, comment field format) — confirm against a real export before writing `parse_cstimer.py`.
