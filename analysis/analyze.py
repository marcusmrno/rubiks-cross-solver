"""How much does the cross a scramble gives me affect the solve?

Reads solves.csv (see analysis/pipeline.py) and, for each outcome, reports
its mean at each optimal cross length, plus one regression:

    outcome ~ optimal_length + log2(num_optimal_solutions)

Both effects are measured with the other held fixed. That matters because
longer crosses tend to have more optimal solutions, so on its own the count
would pick up the length's effect. Read the count's coefficient as "at the
same length, twice as many optimal solutions changes the outcome by this
much".

Total time is in every export. The other three outcomes come from my smart
cube and are skipped when the export has none of them. found_optimal is 1
when my cross took as many moves as the shortest one, else 0, so its mean
is a rate and its coefficients are changes in that rate.

Run it with python -m analysis.analyze <cstimer export>.
"""

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from analysis.pipeline import build_dataset

OUTCOMES = {
    "time_ms": "Solve time (ms)",
    "cross_ms": "Cross time (ms)",
    "found_optimal": "Found an optimal cross",
    "pause_ms": "Pause after the cross (ms)",
}


def analyze(csv_path="solves.csv", png_path="by_length.png"):
    """For each outcome with data: {"n", "by_length", "per_move",
    "per_doubling"}. by_length is a table of solves and mean per optimal
    length; per_move and per_doubling are (effect, p-value) from the
    regression. Also plots the means by length to png_path.
    """
    df = pd.read_csv(csv_path)
    df["found_optimal"] = (df["cross_moves"] == df["optimal_length"]).astype(float)
    df.loc[df["cross_moves"].isna(), "found_optimal"] = np.nan

    # ponytail: no skill-drift adjustment. Scrambles are random, so drift
    # adds noise but can't fake an effect; add solve order as a regressor
    # if months of improvement make the p-values too weak.
    results = {}
    for col in OUTCOMES:
        d = df.dropna(subset=[col])
        if d.empty:
            continue
        X = np.column_stack([np.ones(len(d)), d["optimal_length"],
                             np.log2(d["num_optimal_solutions"])])
        coef, p = _ols(d[col].to_numpy(dtype=float), X)
        results[col] = {
            "n": len(d),
            "by_length": d.groupby("optimal_length")[col].agg(["count", "mean"]),
            "per_move": (coef[1], p[1]),
            "per_doubling": (coef[2], p[2]),
        }

    _plot(results, png_path)
    return results


def _ols(y, X):
    """Least squares fit of y on the columns of X (the first one all 1s for
    the intercept). Returns the coefficients and their two-sided p-values.
    """
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    dof = len(y) - X.shape[1]
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * (resid @ resid) / dof)
    return coef, 2 * stats.t.sf(np.abs(coef / se), dof)


def _plot(results, png_path):
    """One panel per outcome: its mean at each optimal length."""
    fig, axes = plt.subplots(1, len(results), figsize=(4 * len(results), 3.5), squeeze=False)
    for ax, (col, r) in zip(axes[0], results.items()):
        t = r["by_length"]
        ax.plot(t.index, t["mean"], marker="o")
        ax.set_title(OUTCOMES[col])
        ax.set_xlabel("Optimal cross length")
    fig.tight_layout()
    fig.savefig(png_path)
    plt.close(fig)


def main():
    build_dataset(sys.argv[1])
    for col, r in analyze().items():
        print(f"{OUTCOMES[col]}, {r['n']} solves")
        for length, (n, mean) in r["by_length"].iterrows():
            print(f"  length {length}: {int(n):4d} solves, mean {mean:.2f}")
        effect, p = r["per_move"]
        print(f"  per extra optimal move: {effect:+.2f} (p = {p:.2g})")
        effect, p = r["per_doubling"]
        print(f"  per doubling of optimal solutions, same length: {effect:+.2f} (p = {p:.2g})")
    print("Plot written to by_length.png")


if __name__ == "__main__":
    main()
