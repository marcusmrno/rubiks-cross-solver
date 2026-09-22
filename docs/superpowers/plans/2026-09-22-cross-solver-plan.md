# Rubik's Cube Cross Solver + Solve-Time Correlation Implementation Plan

> **This plan is for Marcus to implement himself, for learning.** Each task follows TDD: write the test, watch it fail, write the minimal code to pass, run it, commit. The code shown in each step has already been implemented and verified independently (all invariants and known cube facts checked against a working Python implementation) — copy it in, understand it, then move to the next task. Don't skip the "run and watch it fail" steps; they're what makes TDD actually catch mistakes as you retype the code.

**Goal:** Build a cross solver that enumerates every optimal cross solution for a scramble, then use it to test whether the number of optimal solutions available for a scramble correlates with how fast you actually solved it (from your csTimer history).

**Architecture:** Part 1 (`cube/`) is a standalone library: a coordinate-based edge-cubie model, a full breadth-first pattern database over the ~190k reachable cross states, and a pruned depth-first enumerator that finds every optimal solution for a given scramble. Part 2 (`analysis/`) parses your csTimer export, runs each scramble through Part 1, and correlates solution count against your real solve times.

**Tech Stack:** Python 3.10+, pytest, pandas/numpy, scipy (correlation), matplotlib (plot). No web framework, no database — CSV as the intermediate format.

## Global Constraints

- Python 3.10+, standard library plus: `pytest`, `numpy`, `scipy`, `pandas`, `matplotlib` (all in `requirements.txt`, no other dependencies).
- TDD throughout: every task writes the test before the implementation, and runs it once to confirm it fails for the right reason.
- Commit after every task (not every step) — one commit per working, tested increment.
- All cube state (Part 1) tracks only the 4 D-colored edge pieces (position slot 0–11 + orientation 0/1 each); corners and non-cross edges are never represented.
- Cross convention: cross is built on the **D** (down) face — the 4 cross pieces are whichever edges carry the D-face color in the solved state. This is fixed and doesn't depend on which physical color you use.

---

### Task 0: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `cube/__init__.py` (empty)
- Create: `analysis/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Create: `.gitignore`
- Create: `README.md`

**Interfaces:**
- Produces: a `cube/` package and `analysis/` package other tasks import from, and a working `pytest` command.

- [ ] **Step 1: Create the directory structure and empty package files**

```bash
mkdir -p cube analysis tests
touch cube/__init__.py analysis/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
pytest>=8.0
numpy>=1.26
scipy>=1.12
pandas>=2.2
matplotlib>=3.8
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 4: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
pdb_cache.pkl
solves.csv
correlation.png
```

- [ ] **Step 5: Write a one-paragraph `README.md` stub**

```markdown
# Rubik's Cube Cross Solver + Solve-Time Correlation

A cross solver that enumerates every optimal cross solution for a scramble,
built on a full pattern database over the reduced cross-edge state space.
Part 2 correlates the number of optimal solutions available for a scramble
against real solve times pulled from a csTimer export.

## Usage

    python -m cube.cli "R U R' U' F' U F U2 R U' R' D R U R' U' D' L U L'"
```

- [ ] **Step 6: Verify pytest runs (with nothing to collect yet)**

Run: `pytest -v`
Expected: `no tests ran` (exit code with no errors, not a crash)

- [ ] **Step 7: Commit**

```bash
git add requirements.txt cube/__init__.py analysis/__init__.py tests/__init__.py .gitignore README.md
git commit -m "Scaffold project structure and dependencies"
```

---

### Task 1: Cube edge move engine

**Files:**
- Create: `cube/moves.py`
- Test: `tests/test_moves.py`

**Interfaces:**
- Produces:
  - `MOVES: list[str]` — all 18 face turns, e.g. `["U", "U'", "U2", "R", ...]`.
  - `solved_edges() -> list[dict]` — a fresh solved-cube edge-cubie list. Each cubie is `{'id': frozenset[str,str], 'pos': (int,int,int), 'stickers': dict[(int,int,int), str]}`.
  - `apply_move(cubies: list[dict], move: str) -> list[dict]` — apply one move (e.g. `"R'"`), return a new cubie list (does not mutate input).
  - `apply_scramble(cubies: list[dict], scramble: str) -> list[dict]` — apply a space-separated move sequence.
  - `is_solved(cubies: list[dict]) -> bool`.

Every later task imports from this module and treats a "cubie list" (12 dicts) as the fundamental cube-state type.

This is a coordinate-based model, not a sticker-grid model: each edge cubie is tracked by its 3D position `(x,y,z) ∈ {-1,0,1}³` (exactly one coordinate is 0) and which color currently faces each of its two directions. This turned out to be much less error-prone than hand-writing per-face sticker-cycling tables — a first attempt using sticker strips produced a real bug (`R` followed by `D` corrupted piece identity) that this coordinate approach doesn't have, because all 6 faces share one geometrically-derived rotation rule instead of 6 independently hand-typed ones.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moves.py
from cube.moves import solved_edges, apply_move, apply_scramble, apply_cw, is_solved

INVERSES = {}
for f in "URFDLB":
    INVERSES[f] = f + "'"
    INVERSES[f + "'"] = f
    INVERSES[f + "2"] = f + "2"


def test_four_quarter_turns_is_identity():
    for f in "URFDLB":
        c = solved_edges()
        for _ in range(4):
            c = apply_cw(c, f)
        assert is_solved(c)


def test_move_then_inverse_is_identity():
    for mv, inv in INVERSES.items():
        c = apply_move(solved_edges(), mv)
        c = apply_move(c, inv)
        assert is_solved(c)


def test_opposite_faces_commute():
    assert apply_scramble(solved_edges(), "U D") == apply_scramble(solved_edges(), "D U")
    assert apply_scramble(solved_edges(), "R L") == apply_scramble(solved_edges(), "L R")


def test_sexy_move_has_order_six():
    c = apply_scramble(solved_edges(), ("R U R' U' " * 6).strip())
    assert is_solved(c)


def test_long_scramble_undone_by_reverse_inverse():
    scramble = "R U R' U' F' U F U2 R U' R' D R U R' U' D' L U L'"
    moves = scramble.split()
    rev_inv = " ".join(INVERSES[m] for m in reversed(moves))
    c = apply_scramble(solved_edges(), scramble)
    c = apply_scramble(c, rev_inv)
    assert is_solved(c)


def test_r_move_sends_fr_piece_to_ur_slot():
    # Ground-truth check against the known physical R-turn cycle FR -> UR -> BR -> DR -> FR
    c = apply_move(solved_edges(), "R")
    by_id = {frozenset(x['id']): x['pos'] for x in c}
    assert by_id[frozenset(['F', 'R'])] == (1, 1, 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_moves.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube.moves'`

- [ ] **Step 3: Write the implementation**

```python
# cube/moves.py
"""Edge-only cube model. Corners are irrelevant to cross solving and are never tracked."""

COLOR_OF = {(1, 0, 0): 'R', (-1, 0, 0): 'L', (0, 1, 0): 'U', (0, -1, 0): 'D', (0, 0, 1): 'F', (0, 0, -1): 'B'}

MOVES = [f + suf for f in "URFDLB" for suf in ("", "'", "2")]


def rot(vec, face):
    x, y, z = vec
    if face == 'R': return (x, z, -y)
    if face == 'L': return (x, -z, y)
    if face == 'U': return (-z, y, x)
    if face == 'D': return (z, y, -x)
    if face == 'F': return (y, -x, z)
    if face == 'B': return (-y, x, z)
    raise ValueError(face)


def _layer_coord(face):
    return {'R': (0, 1), 'L': (0, -1), 'U': (1, 1), 'D': (1, -1), 'F': (2, 1), 'B': (2, -1)}[face]


def _edge_homes():
    homes = []
    for a in range(3):
        for b in range(a + 1, 3):
            for sa in (1, -1):
                for sb in (1, -1):
                    pos = [0, 0, 0]
                    pos[a] = sa
                    pos[b] = sb
                    d1 = [0, 0, 0]
                    d1[a] = sa
                    d2 = [0, 0, 0]
                    d2[b] = sb
                    homes.append((tuple(pos), tuple(d1), tuple(d2)))
    return homes


EDGE_HOMES = _edge_homes()


def solved_edges():
    cubies = []
    for pos, d1, d2 in EDGE_HOMES:
        cid = frozenset([COLOR_OF[d1], COLOR_OF[d2]])
        stickers = {d1: COLOR_OF[d1], d2: COLOR_OF[d2]}
        cubies.append({'id': cid, 'pos': pos, 'stickers': stickers})
    return cubies


def apply_cw(cubies, face):
    axis, val = _layer_coord(face)
    new_cubies = []
    for c in cubies:
        if c['pos'][axis] == val:
            new_pos = rot(c['pos'], face)
            new_stickers = {rot(d, face): col for d, col in c['stickers'].items()}
            new_cubies.append({'id': c['id'], 'pos': new_pos, 'stickers': new_stickers})
        else:
            new_cubies.append(c)
    return new_cubies


def apply_move(cubies, move):
    face = move[0]
    n = 2 if move.endswith('2') else (3 if move.endswith("'") else 1)
    for _ in range(n):
        cubies = apply_cw(cubies, face)
    return cubies


def apply_scramble(cubies, scramble):
    for mv in scramble.split():
        cubies = apply_move(cubies, mv)
    return cubies


def is_solved(cubies):
    return all(c['pos'] == p for c, (p, d1, d2) in zip(cubies, EDGE_HOMES))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_moves.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add cube/moves.py tests/test_moves.py
git commit -m "Add coordinate-based edge cubie model with 18 face turns"
```

---

### Task 2: Cross-state extraction

**Files:**
- Create: `cube/cross.py`
- Test: `tests/test_cross.py`

**Interfaces:**
- Consumes: `EDGE_HOMES` from `cube.moves` (list of `(pos, d1, d2)` tuples defining the 12 home positions).
- Produces: `cross_key(cubies: list[dict]) -> tuple[tuple[int,int], ...]` — a hashable 4-tuple of `(slot 0-11, orientation 0/1)` for the DF, DR, DB, DL pieces in that fixed order. This is the PDB/solver's state representation everywhere downstream.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cross.py
from cube.moves import solved_edges, apply_move
from cube.cross import cross_key


def test_solved_cube_all_oriented():
    key = cross_key(solved_edges())
    assert all(oriented == 0 for _slot, oriented in key)


def test_u_move_never_disturbs_cross():
    assert cross_key(apply_move(solved_edges(), "U")) == cross_key(solved_edges())


def test_other_faces_each_disturb_cross():
    for f in "RFLBD":
        assert cross_key(apply_move(solved_edges(), f)) != cross_key(solved_edges())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cross.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube.cross'`

- [ ] **Step 3: Write the implementation**

```python
# cube/cross.py
"""Reduce full edge state to just the 4 cross (D-colored) edges: position slot + orientation."""

from cube.moves import EDGE_HOMES

SLOT_INDEX = {pos: i for i, (pos, d1, d2) in enumerate(EDGE_HOMES)}
CROSS_IDS = [frozenset(['D', 'F']), frozenset(['D', 'R']), frozenset(['D', 'B']), frozenset(['D', 'L'])]


def cross_key(cubies):
    by_id = {c['id']: c for c in cubies}
    result = []
    for cid in CROSS_IDS:
        c = by_id[cid]
        pos = c['pos']
        slot = SLOT_INDEX[pos]
        if pos[1] != 0:
            primary_dir = (0, pos[1], 0)
        else:
            primary_dir = (0, 0, pos[2])
        oriented = 0 if c['stickers'][primary_dir] == 'D' else 1
        result.append((slot, oriented))
    return tuple(result)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cross.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add cube/cross.py tests/test_cross.py
git commit -m "Add cross-edge state extraction"
```

---

### Task 3: Pattern database

**Files:**
- Create: `cube/pdb.py`
- Test: `tests/test_pdb.py`

**Interfaces:**
- Consumes: `solved_edges`, `apply_move`, `MOVES` from `cube.moves`; `cross_key` from `cube.cross`.
- Produces:
  - `build_pdb() -> dict[cross_key_tuple, int]` — exact optimal distance for every reachable cross state.
  - `save_pdb(dist, path)`, `load_pdb(path) -> dict`, `load_or_build_pdb(path=CACHE_PATH) -> dict` — disk caching so later tasks don't rebuild every run.

This step is the one that takes real time: the BFS visits and expands all 190,080 reachable states, roughly **50–60 seconds** in plain Python. That's expected — it's a one-time cost, cached to `pdb_cache.pkl` afterward by `load_or_build_pdb`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pdb.py
from cube.moves import solved_edges, apply_move
from cube.cross import cross_key
from cube.pdb import build_pdb


def test_pdb_matches_known_cross_facts():
    # Slow (~1 minute): one full BFS over the 190,080-state cross space.
    dist = build_pdb()
    assert len(dist) == 190080
    assert max(dist.values()) == 8

    solved_key = cross_key(solved_edges())
    assert dist[solved_key] == 0
    assert dist[cross_key(apply_move(solved_edges(), "U"))] == 0
    for f in "RFLBD":
        assert dist[cross_key(apply_move(solved_edges(), f))] == 1
```

These numbers aren't arbitrary: 190,080 = 12·11·10·9·2⁴ (the exact count of reachable 4-distinguishable-edge states), 8 is the known worst-case optimal cross length, and the single-move distances follow directly from the fact that only D-layer turns touch the cross (U turns never do).

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pdb.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube.pdb'`

- [ ] **Step 3: Write the implementation**

```python
# cube/pdb.py
"""Pattern database: exact optimal cross-distance for every reachable cross state."""

import pickle
from collections import deque
from pathlib import Path

from cube.moves import solved_edges, apply_move, MOVES
from cube.cross import cross_key

CACHE_PATH = Path(__file__).resolve().parent.parent / "pdb_cache.pkl"


def build_pdb():
    start = solved_edges()
    start_key = cross_key(start)
    dist = {start_key: 0}
    frontier = deque([(start, start_key)])
    while frontier:
        state, key = frontier.popleft()
        d = dist[key]
        for mv in MOVES:
            ns = apply_move(state, mv)
            nk = cross_key(ns)
            if nk not in dist:
                dist[nk] = d + 1
                frontier.append((ns, nk))
    return dist


def save_pdb(dist, path=CACHE_PATH):
    with open(path, "wb") as f:
        pickle.dump(dist, f)


def load_pdb(path=CACHE_PATH):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_or_build_pdb(path=CACHE_PATH):
    if path.exists():
        return load_pdb(path)
    dist = build_pdb()
    save_pdb(dist, path)
    return dist
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pdb.py -v`
Expected: 1 passed in ~55-115s (this one is genuinely slow — that's fine)

- [ ] **Step 5: Commit**

```bash
git add cube/pdb.py tests/test_pdb.py
git commit -m "Add BFS pattern database over the cross state space"
```

---

### Task 4: Optimal-solution enumeration with canonicalization

**Files:**
- Create: `cube/solver.py`
- Test: `tests/test_solver.py`

**Interfaces:**
- Consumes: `solved_edges`, `apply_move`, `apply_scramble`, `MOVES` from `cube.moves`; `cross_key` from `cube.cross`.
- Produces: `solve_all_optimal(dist: dict, scramble: str) -> tuple[int, list[list[str]]]` — `(optimal_length, list_of_move_sequences)`. This is the function `analysis/pipeline.py` (Task 8) calls per scramble.

Two move sequences that differ only by reordering independent moves (`R L` vs `L R`) are the same physical solution and are deduped by enforcing a fixed order on opposite-face pairs (U before D, L before R, F before B) whenever they'd otherwise be interchangeable. Moves on genuinely interacting adjacent axes (e.g. `R` and `F`) are **not** deduped — they can produce mechanically different solutions even at the same length.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_solver.py
import pytest

from cube.moves import solved_edges, apply_scramble, apply_move
from cube.cross import cross_key
from cube.pdb import build_pdb
from cube.solver import solve_all_optimal


@pytest.fixture(scope="module")
def dist():
    return build_pdb()


def test_sexy_move_has_zero_length_cross_solution(dist):
    d, sols = solve_all_optimal(dist, "R U R' U'")
    assert d == 0
    assert sols == [[]]


def test_known_scramble_has_expected_optimal_length_and_count(dist):
    scramble = "D2 R' D' F2 B2 U' R2 U' F2 D B2 U2 R' D R' B L2 F' U F2"
    d, sols = solve_all_optimal(dist, scramble)
    assert d == 7
    assert len(sols) == 56


def test_adjacent_axis_moves_are_not_deduped(dist):
    d, sols = solve_all_optimal(dist, "R2 F2 U' F2 U' R2 F2")
    assert d == 3
    assert len(sols) == 2


def test_every_enumerated_solution_actually_solves_the_cross(dist):
    scramble = "D2 R' D' F2 B2 U' R2 U' F2 D B2 U2 R' D R' B L2 F' U F2"
    solved_key = cross_key(solved_edges())
    _d, sols = solve_all_optimal(dist, scramble)
    for sol in sols:
        c = apply_scramble(solved_edges(), scramble)
        for mv in sol:
            c = apply_move(c, mv)
        assert cross_key(c) == solved_key
```

Note the `dist` fixture builds the PDB once per test file (~1 minute), not once per test.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_solver.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube.solver'`

- [ ] **Step 3: Write the implementation**

```python
# cube/solver.py
"""Enumerate every optimal cross solution for a scramble, deduping trivial move reorderings."""

from cube.moves import solved_edges, apply_move, apply_scramble, MOVES
from cube.cross import cross_key

AXIS_OF = {'U': 0, 'D': 0, 'L': 1, 'R': 1, 'F': 2, 'B': 2}
ORDER_OK = {'U': 'D', 'L': 'R', 'F': 'B'}  # first move of an opposite-face pair -> allowed second move


def solve_all_optimal(dist, scramble):
    start = apply_scramble(solved_edges(), scramble)
    start_key = cross_key(start)
    solved_key = cross_key(solved_edges())
    d = dist[start_key]
    solutions = []

    def dfs(state, key, remaining, path, last_face):
        if remaining == 0:
            if key == solved_key:
                solutions.append(list(path))
            return
        for mv in MOVES:
            f = mv[0]
            if f == last_face:
                continue
            if last_face is not None and AXIS_OF[f] == AXIS_OF[last_face]:
                if ORDER_OK.get(last_face) != f:
                    continue
            ns = apply_move(state, mv)
            nk = cross_key(ns)
            if dist[nk] == remaining - 1:
                path.append(mv)
                dfs(ns, nk, remaining - 1, path, f)
                path.pop()

    dfs(start, start_key, d, [], None)
    return d, solutions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_solver.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add cube/solver.py tests/test_solver.py
git commit -m "Add pruned DFS enumeration of all optimal cross solutions"
```

---

### Task 5: CLI

**Files:**
- Create: `cube/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_or_build_pdb` from `cube.pdb`; `solve_all_optimal` from `cube.solver`.
- Produces: a runnable `python -m cube.cli "<scramble>"` entry point. Nothing downstream depends on this module — it's a demoable checkpoint for Part 1.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
import subprocess
import sys


def test_cli_prints_optimal_length_and_solutions():
    result = subprocess.run(
        [sys.executable, "-m", "cube.cli", "R", "U", "R'", "U'"],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0
    assert "Optimal cross length: 0" in result.stdout
    assert "Number of optimal solutions: 1" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL — `No module named cube.cli`

- [ ] **Step 3: Write the implementation**

```python
# cube/cli.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: 1 passed (first run builds and caches the PDB, ~1 minute; instant after)

- [ ] **Step 5: Try it yourself with a real scramble**

```bash
python -m cube.cli "D2 R' D' F2 B2 U' R2 U' F2 D B2 U2 R' D R' B L2 F' U F2"
```

Expected: `Optimal cross length: 7`, `Number of optimal solutions: 56`, followed by all 56 move sequences.

- [ ] **Step 6: Commit**

```bash
git add cube/cli.py tests/test_cli.py
git commit -m "Add CLI entry point for the cross solver"
```

**Part 1 is now complete and independently demoable** — this is a good checkpoint to update the README with a couple of real example runs before moving to Part 2.

---

### Task 6: csTimer export parser

**Files:**
- Create: `analysis/parse_cstimer.py`
- Test: `tests/test_parse_cstimer.py`

**Interfaces:**
- Produces: `load_solves(path: str) -> list[dict]`, each dict `{"scramble": str, "time_ms": float, "session": str}`. DNFs are excluded; `+2` penalties keep the already-adjusted time.

**Before writing the implementation**, export a real (even small) csTimer session — csTimer web app → the menu → Export → save the `.txt`/`.json` file — and inspect its actual top-level shape:

```bash
python3 -m json.tool your_export.txt | head -60
```

The code below assumes the commonly-documented csTimer shape: a top-level object with one key per session (`"session1"`, `"session2"`, ...) mapping to a list of `[[penalty, time_ms], scramble, comment]` entries, where `penalty` is `0` (none), `2000` (+2, with `time_ms` already including the 2000ms), or `-1` (DNF). **Confirm this against what you actually see before trusting it** — this was flagged as an open question during design since real export data wasn't available yet. If your export differs, adjust `load_solves` (and the fixture in the test below) to match before moving on — this is expected, not a sign you did something wrong.

- [ ] **Step 1: Write the failing test with a fixture matching the documented shape**

```python
# tests/test_parse_cstimer.py
import json

from analysis.parse_cstimer import load_solves

FIXTURE = {
    "session1": [
        [[0, 12345], "R U R' U'", ""],
        [[2000, 14345], "F2 R2 U'", "slow"],
        [[-1, 9999], "L2 B2", ""],
    ],
    "session1Name": "Session 1",
}


def test_load_solves_excludes_dnf_and_keeps_plus2(tmp_path):
    export_path = tmp_path / "export.json"
    export_path.write_text(json.dumps(FIXTURE))

    solves = load_solves(str(export_path))

    assert len(solves) == 2
    assert solves[0] == {"scramble": "R U R' U'", "time_ms": 12345, "session": "session1"}
    assert solves[1] == {"scramble": "F2 R2 U'", "time_ms": 14345, "session": "session1"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parse_cstimer.py -v`
Expected: FAIL — `No module named 'analysis.parse_cstimer'`

- [ ] **Step 3: Write the implementation**

```python
# analysis/parse_cstimer.py
"""Parse a csTimer JSON export into (scramble, time_ms, session) records."""

import json

PENALTY_DNF = -1


def load_solves(path):
    with open(path) as f:
        data = json.load(f)

    solves = []
    for key, value in data.items():
        if not key.startswith("session") or not isinstance(value, list):
            continue
        for entry in value:
            (penalty, time_ms), scramble = entry[0], entry[1]
            if penalty == PENALTY_DNF:
                continue
            solves.append({"scramble": scramble, "time_ms": time_ms, "session": key})
    return solves
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parse_cstimer.py -v`
Expected: 1 passed

- [ ] **Step 5: Run against your real export and sanity-check the count**

```bash
python3 -c "from analysis.parse_cstimer import load_solves; print(len(load_solves('your_export.json')))"
```

Compare this count against what csTimer's own stats screen reports for that session (minus DNFs). If it's off, the assumed shape was wrong somewhere — go back and fix `load_solves` against the real structure before Task 7.

- [ ] **Step 6: Commit**

```bash
git add analysis/parse_cstimer.py tests/test_parse_cstimer.py
git commit -m "Add csTimer export parser"
```

---

### Task 7: Data pipeline (join solver output with solve times)

**Files:**
- Create: `analysis/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `load_or_build_pdb` from `cube.pdb`; `solve_all_optimal` from `cube.solver`; `load_solves` from `analysis.parse_cstimer`.
- Produces: `build_dataset(export_path: str, cache_path: str = "solves.csv") -> list[dict]`, each dict `{"scramble": str, "time_ms": float, "optimal_length": int, "num_optimal_solutions": int}`. Also writes/updates `cache_path` as a CSV so re-runs don't re-solve scrambles already seen.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import json

from analysis.pipeline import build_dataset

FIXTURE = {
    "session1": [
        [[0, 5000], "R U R' U'", ""],
        [[0, 9000], "R2 F2 U' F2 U' R2 F2", ""],
    ],
}


def test_build_dataset_joins_solver_output_with_times(tmp_path):
    export_path = tmp_path / "export.json"
    export_path.write_text(json.dumps(FIXTURE))
    cache_path = tmp_path / "solves.csv"

    rows = build_dataset(str(export_path), cache_path=str(cache_path))

    assert len(rows) == 2
    row_by_scramble = {r["scramble"]: r for r in rows}
    assert row_by_scramble["R U R' U'"]["optimal_length"] == 0
    assert row_by_scramble["R U R' U'"]["num_optimal_solutions"] == 1
    assert row_by_scramble["R2 F2 U' F2 U' R2 F2"]["optimal_length"] == 3
    assert row_by_scramble["R2 F2 U' F2 U' R2 F2"]["num_optimal_solutions"] == 2
    assert cache_path.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL — `No module named 'analysis.pipeline'`

- [ ] **Step 3: Write the implementation**

```python
# analysis/pipeline.py
"""Join solve times with cross-solver output, caching results to avoid re-solving scrambles."""

import csv
from pathlib import Path

from cube.pdb import load_or_build_pdb
from cube.solver import solve_all_optimal
from analysis.parse_cstimer import load_solves

FIELDS = ["scramble", "time_ms", "optimal_length", "num_optimal_solutions"]


def build_dataset(export_path, cache_path="solves.csv"):
    cache_path = Path(cache_path)
    cached = {}
    if cache_path.exists():
        with open(cache_path) as f:
            for row in csv.DictReader(f):
                cached[row["scramble"]] = row

    dist = load_or_build_pdb()
    solves = load_solves(export_path)
    rows = []
    for s in solves:
        scramble = s["scramble"]
        if scramble in cached:
            row = cached[scramble]
            optimal_length = int(row["optimal_length"])
            num_optimal_solutions = int(row["num_optimal_solutions"])
        else:
            optimal_length, sols = solve_all_optimal(dist, scramble)
            num_optimal_solutions = len(sols)
        rows.append({
            "scramble": scramble,
            "time_ms": s["time_ms"],
            "optimal_length": optimal_length,
            "num_optimal_solutions": num_optimal_solutions,
        })

    with open(cache_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: 1 passed (builds/caches the PDB on first run if `pdb_cache.pkl` doesn't exist yet — up to ~1 minute)

- [ ] **Step 5: Run it against your real csTimer export**

```bash
python3 -c "from analysis.pipeline import build_dataset; rows = build_dataset('your_export.json'); print(len(rows), 'solves processed')"
```

This writes `solves.csv` with every solve joined to its optimal cross length and solution count — the input for Task 8's analysis.

- [ ] **Step 6: Commit**

```bash
git add analysis/pipeline.py tests/test_pipeline.py
git commit -m "Add data pipeline joining solver output with csTimer times"
```

---

### Task 8: Correlation and regression analysis

**Files:**
- Create: `analysis/analyze.py`
- Test: `tests/test_analyze.py`

**Interfaces:**
- Consumes: a `solves.csv` in the shape written by Task 7's `build_dataset` (columns: `scramble, time_ms, optimal_length, num_optimal_solutions`).
- Produces: `analyze(csv_path: str = "solves.csv") -> dict` with keys `pearson_r`, `pearson_p`, `spearman_r`, `spearman_p`, `linear_fit` (slope, intercept), `log_fit` (slope, intercept). Also writes `correlation.png`, a scatter plot with the linear fit overlaid.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_analyze.py
import csv

from analysis.analyze import analyze


def test_analyze_finds_negative_correlation_in_synthetic_data(tmp_path):
    # Synthetic but realistic: more optimal solutions -> lower solve time, plus noise.
    csv_path = tmp_path / "solves.csv"
    rows = []
    for i in range(30):
        num_solutions = 1 + (i % 20)
        time_ms = 12000 - num_solutions * 200 + (i % 3) * 150
        rows.append({"scramble": f"scramble{i}", "time_ms": time_ms,
                      "optimal_length": 6, "num_optimal_solutions": num_solutions})
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scramble", "time_ms", "optimal_length", "num_optimal_solutions"])
        writer.writeheader()
        writer.writerows(rows)

    result = analyze(str(csv_path))

    assert result["pearson_r"] < -0.5  # strong negative correlation by construction
    slope, _intercept = result["linear_fit"]
    assert slope < 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_analyze.py -v`
Expected: FAIL — `No module named 'analysis.analyze'`

- [ ] **Step 3: Write the implementation**

```python
# analysis/analyze.py
"""Correlate number of optimal cross solutions with actual solve time."""

import csv

import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_dataset(csv_path):
    xs, ys = [], []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            xs.append(int(row["num_optimal_solutions"]))
            ys.append(float(row["time_ms"]))
    return np.array(xs), np.array(ys)


def analyze(csv_path="solves.csv"):
    x, y = load_dataset(csv_path)

    pearson_r, pearson_p = stats.pearsonr(x, y)
    spearman_r, spearman_p = stats.spearmanr(x, y)

    slope, intercept = np.polyfit(x, y, 1)
    log_slope, log_intercept = np.polyfit(np.log(x), y, 1)

    fig, ax = plt.subplots()
    ax.scatter(x, y, alpha=0.5)
    xs_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs_line, slope * xs_line + intercept, color="red", label=f"linear fit (r={pearson_r:.2f})")
    ax.set_xlabel("Number of optimal cross solutions")
    ax.set_ylabel("Solve time (ms)")
    ax.legend()
    fig.savefig("correlation.png")
    plt.close(fig)

    return {
        "pearson_r": pearson_r, "pearson_p": pearson_p,
        "spearman_r": spearman_r, "spearman_p": spearman_p,
        "linear_fit": (slope, intercept),
        "log_fit": (log_slope, log_intercept),
    }


if __name__ == "__main__":
    print(analyze())
```

`np.log(x)` is safe here because `num_optimal_solutions` is always ≥ 1 (every reachable scramble has at least one optimal solution) — `log(1) == 0`, no divide-by-zero or domain error.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_analyze.py -v`
Expected: 1 passed

- [ ] **Step 5: Run it against your real data and look at the plot**

```bash
python3 -m analysis.analyze
open correlation.png
```

- [ ] **Step 6: Commit**

```bash
git add analysis/analyze.py tests/test_analyze.py
git commit -m "Add correlation and regression analysis"
```

---

### Task 9: End-to-end wiring and README

**Files:**
- Create: `run_analysis.py`
- Modify: `README.md`

**Interfaces:**
- Produces: a single script tying Tasks 6–8 together, and a finished README documenting both parts as independently demoable pieces.

- [ ] **Step 1: Write the end-to-end script**

```python
# run_analysis.py
"""Run the full pipeline: parse csTimer export -> solve every scramble -> analyze."""

import sys

from analysis.pipeline import build_dataset
from analysis.analyze import analyze

if __name__ == "__main__":
    export_path = sys.argv[1]
    rows = build_dataset(export_path)
    print(f"Processed {len(rows)} solves.")
    result = analyze()
    print(result)
    print("Scatter plot written to correlation.png")
```

- [ ] **Step 2: Run it against your real export end to end**

```bash
python3 run_analysis.py your_export.json
```

Expected: prints the solve count, correlation stats, and writes `correlation.png`.

- [ ] **Step 3: Run the full test suite one more time**

Run: `pytest -v`
Expected: all tests pass (the PDB-building ones will reuse `pdb_cache.pkl` by now and be fast)

- [ ] **Step 4: Update `README.md` with real results**

Add a "Results" section stating your actual Pearson/Spearman r and what it means for cross practice, plus the two `python -m cube.cli` / `python3 run_analysis.py` usage examples confirmed working above.

- [ ] **Step 5: Commit**

```bash
git add run_analysis.py README.md
git commit -m "Wire up end-to-end pipeline and document results"
```
