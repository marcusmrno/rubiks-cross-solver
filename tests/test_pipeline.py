import csv

import pytest

import analysis.pipeline
from analysis.pipeline import build_dataset, cross_split
from cube.solver import solve_all_optimal

# scramble, time_ms, optimal white-cross length, number of optimal solutions
EXPECTED = [
    ("R U R' U'", 5000, 4, 1),
    ("R2 F2 U' F2 U' R2 F2", 9000, 5, 4),
    ("R' B L' U B R U' B D R' F2 L U2 R F2 L' D2 R' F2 B2 R'", 13009, 6, 1),
]


@pytest.fixture
def export(write_export, dist, monkeypatch):
    """A one-session export of the EXPECTED scrambles. The pipeline gets the
    session's table instead of loading or building the real cache.
    """
    monkeypatch.setattr(analysis.pipeline, "load_or_build_pdb", lambda: dist)
    return write_export(
        {"session1": [[[0, ms], scramble, "", 1548020659] for scramble, ms, _, _ in EXPECTED]},
        {"1": {"name": "3x3", "opt": {}}},
    )


def test_rows_give_white_cross_numbers(export, tmp_path):
    """Each row is solved for the white cross, not the D cross of the scramble
    as written (yellow). As written, R U R' U' leaves the D cross solved: 0
    moves. Turned over so white is on the bottom, it takes 4 (D R D' R'),
    and there's only one way. The row keeps the scramble as csTimer wrote it.
    These solves weren't on the smart cube, so there's no cross time or moves.
    """
    rows = build_dataset(export, csv_path=str(tmp_path / "solves.csv"))

    assert rows == [
        {"scramble": s, "time_ms": ms, "optimal_length": d, "num_optimal_solutions": n,
         "cross_ms": None, "cross_moves": None}
        for s, ms, d, n in EXPECTED
    ]


def test_turning_over_sideways_gives_the_same_numbers(export, dist, tmp_path):
    """Turning the cube over sideways (z2: U<->D, L<->R) also puts white on the
    bottom, just with a different face in front. The cross takes the same
    moves either way, so solving each scramble with z2, without going through
    the pipeline, must reproduce every row's numbers.
    """
    z2 = str.maketrans("UDLR", "DURL")

    for row in build_dataset(export, csv_path=str(tmp_path / "solves.csv")):
        d, sols = solve_all_optimal(dist, row["scramble"].translate(z2))
        assert (row["optimal_length"], row["num_optimal_solutions"]) == (d, len(sols))


def test_writes_the_rows_to_csv(export, tmp_path):
    """solves.csv is what the analysis will read: a header, then one line per row.
    A missing cross time or move count is a blank cell.
    """
    csv_path = tmp_path / "solves.csv"

    rows = build_dataset(export, csv_path=str(csv_path))

    with open(csv_path) as f:
        assert list(csv.DictReader(f)) == [
            {k: "" if v is None else str(v) for k, v in r.items()} for r in rows
        ]


def test_smart_cube_solve_gets_its_cross_time_and_moves(write_export, dist, monkeypatch, tmp_path):
    """The start of one of my real smart-cube solves. The first 7 turns,
    U U R U' R F F, are 5 moves (U2 R U' R F2), which is the optimal length,
    so I found an optimal cross, done at 1014 ms. The two turns after it are
    F2L and must not count.
    """
    monkeypatch.setattr(analysis.pipeline, "load_or_build_pdb", lambda: dist)
    path = write_export(
        {"session1": [[
            [0, 15256], "D' F2 L2 U F2 D L2 U2 B2 U' L2 U L' D2 B F R2 D2 U F'", "", 1790720668,
            ["U@0 U@192 R@308 U'@494 R@831 F@939 F@1014 D'@1540 R'@1659", "333"],
        ]]},
        {"1": {"name": "3x3", "opt": {}}},
    )

    [row] = build_dataset(path, csv_path=str(tmp_path / "solves.csv"))

    assert (row["optimal_length"], row["cross_moves"], row["cross_ms"]) == (5, 5, 1014)


def test_the_turn_that_finishes_the_cross_counts():
    """Scrambled with R U R' U', undoing it (U R U' R') brings the white cross
    back on the last turn, at 300 ms: 4 moves, the last one included.
    """
    assert cross_split("R U R' U'", [("U", 0), ("R", 100), ("U'", 200), ("R'", 300)]) == (300, 4)


def test_back_to_back_turns_of_one_face_make_one_move():
    """The cube reports a half turn as two quarter turns, so R R is one move
    (R2), and a turn undone right away (L L') is no move. After the scramble
    R2, the white cross is back on the second R.
    """
    assert cross_split("R2", [("L", 0), ("L'", 40), ("R", 100), ("R", 150)]) == (150, 1)


def test_cross_left_solved_by_the_scramble_is_done_at_zero():
    """D turns only the yellow face, so the white cross is already solved
    before my first turn: 0 ms, 0 moves.
    """
    assert cross_split("D", [("D'", 0)]) == (0, 0)


def test_turns_that_never_solve_the_cross_fail_loudly():
    """Turns that never solve the white cross don't fit the scramble (say the
    cube missed one), so any number would be a guess.
    """
    with pytest.raises(ValueError):
        cross_split("R", [("L", 0)])
