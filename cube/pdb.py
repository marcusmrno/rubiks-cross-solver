"""Pattern database: exact optimal cross-distance for every reachable cross state."""

import pickle
from collections import deque
from pathlib import Path

from cube.moves import solved_edges, apply_move, MOVES
from cube.cross import cross_key

CACHE_PATH = Path(__file__).resolve().parent.parent / "pdb_cache.pkl"


def build_pdb():
    """BFS from solved over cross keys; returns {cross_key: optimal move count}."""
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
    # No invalidation: delete pdb_cache.pkl if cross_key's format ever changes.
    path = Path(path)
    if path.exists():
        return load_pdb(path)
    dist = build_pdb()
    save_pdb(dist, path)
    return dist
