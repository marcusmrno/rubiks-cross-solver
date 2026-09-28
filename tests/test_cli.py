import runpy
import sys

import cube.pdb

EXPECTED = (
    "Optimal cross length: 3\n"
    "Number of optimal solutions: 2\n"
    "  U2 R2 F2\n"
    "  U2 F2 R2\n"
)


def _run_cli(args, dist, monkeypatch, capsys):
    """Run cube.cli exactly as `python -m cube.cli ARGS` would, but hand it the
    session's table instead of letting it load or build the real cache.
    """
    monkeypatch.setattr(cube.pdb, "load_or_build_pdb", lambda: dist)

    def _should_not_run():
        raise AssertionError("the CLI must use the cached table, not rebuild it")

    monkeypatch.setattr(cube.pdb, "build_pdb", _should_not_run)
    monkeypatch.setattr(sys, "argv", ["cube.cli", *args])
    runpy.run_module("cube.cli", run_name="__main__")
    return capsys.readouterr().out


def test_cli_prints_length_count_and_each_solution(dist, monkeypatch, capsys):
    """`python -m cube.cli "<scramble>"` prints the optimal length, the number
    of solutions, then one indented line per solution.
    """
    assert _run_cli(["R2 F2 U' F2 U' R2 F2"], dist, monkeypatch, capsys) == EXPECTED


def test_cli_accepts_scramble_as_separate_args(dist, monkeypatch, capsys):
    """Unquoted moves arrive as separate argv entries; the CLI joins them back
    into one scramble, so the output is the same as the quoted form.
    """
    args = ["R2", "F2", "U'", "F2", "U'", "R2", "F2"]
    assert _run_cli(args, dist, monkeypatch, capsys) == EXPECTED
