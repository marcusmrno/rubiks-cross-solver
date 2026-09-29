import csv

import pytest

import analysis.pipeline
from analysis.pipeline import build_dataset
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
    """
    rows = build_dataset(export, csv_path=str(tmp_path / "solves.csv"))

    assert rows == [
        {"scramble": s, "time_ms": ms, "optimal_length": d, "num_optimal_solutions": n}
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
    """solves.csv is Task 8's input: a header, then one line per row."""
    csv_path = tmp_path / "solves.csv"

    rows = build_dataset(export, csv_path=str(csv_path))

    with open(csv_path) as f:
        assert list(csv.DictReader(f)) == [{k: str(v) for k, v in r.items()} for r in rows]
