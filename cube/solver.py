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
