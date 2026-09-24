# Rubik's Cube Cross Solver + Solve-Time Correlation

A cross solver that enumerates every optimal cross solution for a scramble,
built on a full pattern database over the reduced cross-edge state space.
Part 2 correlates the number of optimal solutions available for a scramble
against real solve times pulled from a csTimer export.

## Usage

    python -m cube.cli "R U R' U' F' U F U2 R U' R' D R U R' U' D' L U L'"
