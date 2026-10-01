import csv
import sys

import numpy as np
import pytest
from scipy import stats

import analysis.analyze
from analysis.analyze import _ols, analyze
from analysis.pipeline import FIELDS


def _write_csv(tmp_path, rows):
    """Write rows the way build_dataset does: missing values as blank cells."""
    path = tmp_path / "solves.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, restval=None)
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


def _row(length, count, time_ms, cross_moves=None, cross_ms=None, pause_ms=None):
    return {"scramble": "R", "time_ms": time_ms, "optimal_length": length,
            "num_optimal_solutions": count, "cross_ms": cross_ms,
            "cross_moves": cross_moves, "pause_ms": pause_ms}


def test_ols_matches_scipy_on_one_predictor():
    """With one predictor, the regression is a plain line fit, which scipy's
    linregress computes its own way: same slope, intercept and p-value. The
    slope is weak on purpose: with a tiny p-value, approx would call any two
    tiny numbers equal.
    """
    rng = np.random.default_rng(1)
    x = rng.uniform(0, 10, 40)
    y = 0.5 * x + rng.normal(0, 5, 40)

    coef, p = _ols(y, np.column_stack([np.ones(40), x]))

    fit = stats.linregress(x, y)
    assert coef == pytest.approx([fit.intercept, fit.slope])
    assert 0.1 < fit.pvalue < 0.9
    assert p[1] == pytest.approx(fit.pvalue)


def test_ols_matches_numpy_on_two_predictors():
    """With two predictors (here x and x squared) the degrees of freedom are
    n - 3, not n - 2. numpy's quadratic fit computes the coefficients and
    their standard errors its own way; the p-values must follow from those.
    The x coefficient comes out negative, which a missing abs() would get
    wrong.
    """
    rng = np.random.default_rng(2)
    x = rng.uniform(0, 10, 15)
    y = 1 - 0.05 * x ** 2 + rng.normal(0, 2, 15)

    coef, p = _ols(y, np.column_stack([np.ones(15), x, x ** 2]))

    np_coef, cov = np.polyfit(x, y, 2, cov=True)  # highest power first
    np_coef, se = np_coef[::-1], np.sqrt(np.diag(cov))[::-1]
    assert np_coef[1] < 0
    assert coef == pytest.approx(np_coef)
    assert p == pytest.approx(2 * stats.t.sf(np.abs(np_coef / se), 15 - 3))


def test_each_effect_is_measured_with_the_other_held_fixed(tmp_path):
    """Longer crosses tend to have more optimal solutions, so each effect can
    pass for the other. Here total time depends only on length (+400 ms per
    move), yet raw count and time are strongly correlated; the regression
    must give the count nothing. Cross time depends only on the count
    (-150 ms each time it doubles); the regression must give length nothing.
    """
    rng = np.random.default_rng(0)
    rows = [_row(length, 2 ** (length - 5 + k), 10000 + 400 * length + rng.normal(0, 100),
                 cross_ms=2000 - 150 * (length - 5 + k) + rng.normal(0, 100))
            for length in (5, 6, 7) for k in range(4) for _ in range(5)]
    counts = [r["num_optimal_solutions"] for r in rows]
    times = [r["time_ms"] for r in rows]
    assert stats.spearmanr(counts, times).statistic > 0.4  # the trap

    results = analyze(_write_csv(tmp_path, rows), png_path=tmp_path / "plot.png")

    time, cross = results["time_ms"], results["cross_ms"]
    assert time["per_move"][0] == pytest.approx(400, abs=60)
    assert abs(time["per_doubling"][0]) < 30 and time["per_doubling"][1] > 0.05
    assert cross["per_doubling"][0] == pytest.approx(-150, abs=30)
    assert abs(cross["per_move"][0]) < 60 and cross["per_move"][1] > 0.05


def test_found_optimal_is_cross_moves_equal_to_optimal_length(tmp_path):
    """At length 5, crosses of 5, 5, 5 and 7 moves: three of four optimal. At
    length 6, 6, 8 and 9 moves: one of three. Means are rates.
    """
    rows = [_row(5, 1, 12000, cross_moves=m) for m in (5, 5, 5, 7)]
    rows += [_row(6, n, 13000, cross_moves=m) for n, m in ((2, 6), (4, 8), (8, 9))]

    table = analyze(_write_csv(tmp_path, rows), png_path=tmp_path / "plot.png")["found_optimal"]["by_length"]

    assert table["count"].to_dict() == {5: 4, 6: 3}
    assert table["mean"].to_dict() == pytest.approx({5: 0.75, 6: 1 / 3})


def test_smart_cube_outcomes_skipped_without_smart_cube_solves(tmp_path):
    """The old keyboard export has no turns, so only total time is analyzed,
    and the plot has one panel instead of four.
    """
    rows = [_row(length, n, 11000 + 300 * length + 50 * k)
            for length in (4, 5, 6) for n in (1, 2, 4) for k in range(2)]
    png = tmp_path / "plot.png"

    results = analyze(_write_csv(tmp_path, rows), png_path=png)

    assert list(results) == ["time_ms"]
    assert results["time_ms"]["n"] == 18
    assert png.exists()


def test_main_builds_the_dataset_then_prints_the_report(tmp_path, monkeypatch, capsys):
    """`python -m analysis.analyze EXPORT` builds solves.csv from the export,
    then prints each outcome's table and effects and writes by_length.png,
    all in the working directory.
    """
    monkeypatch.chdir(tmp_path)
    rows = [_row(length, n, 11000 + 300 * length + 50 * k, cross_moves=length + k, cross_ms=1000 + k,
                 pause_ms=400 + 10 * n)
            for length in (4, 5, 6) for n in (1, 2, 4) for k in range(2)]
    built = []
    monkeypatch.setattr(analysis.analyze, "build_dataset",
                        lambda path: built.append(path) or _write_csv(tmp_path, rows))
    monkeypatch.setattr(sys, "argv", ["analysis.analyze", "export.txt"])

    analysis.analyze.main()

    out = capsys.readouterr().out
    assert built == ["export.txt"]
    assert "Solve time (ms), 18 solves\n  length 4:    6 solves, mean 12225.00\n" in out
    assert "Found an optimal cross, 18 solves\n  length 4:    6 solves, mean 0.50\n" in out
    assert "Pause after the cross (ms)" in out
    assert (tmp_path / "by_length.png").exists()
