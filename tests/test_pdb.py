from collections import Counter

import cube.pdb
from cube.pdb import save_pdb, load_pdb, load_or_build_pdb
from cube.moves import MOVES, solved_edges, apply_move
from cube.cross import cross_key


def test_full_distance_histogram(dist):
    """This is the published distribution of optimal cross lengths; it implies
    190,080 states total (= 12*11*10*9*2**4) and a worst case of 8 moves.
    """
    assert len(dist) == 190080
    assert Counter(dist.values()) == {
        0: 1,
        1: 15,
        2: 158,
        3: 1394,
        4: 9809,
        5: 46381,
        6: 97254,
        7: 34966,
        8: 102,
    }


def test_single_move_distances(dist):
    """Solved key is 0; U/U'/U2 stay at 0 (U never touches a cross piece);
    every other move reaches distance 1 in a single move.
    """
    solved_dist = dist[cross_key(solved_edges())]
    assert solved_dist == 0
    for mv in ["U", "U'", "U2"]:
        assert dist[cross_key(apply_move(solved_edges(), mv))] == 0
    for mv in MOVES:
        if not mv.startswith("U"):
            assert dist[cross_key(apply_move(solved_edges(), mv))] == 1, mv


def test_save_load_round_trip(tmp_path):
    """save_pdb then load_pdb returns an equal dict, using tmp_path only."""
    small = {
        ((10, 0), (1, 0), (11, 0), (3, 0)): 0,
        ((1, 0), (11, 0), (3, 0), (10, 0)): 1,
    }
    path = tmp_path / "pdb.pkl"
    save_pdb(small, path)
    assert load_pdb(path) == small


def test_load_or_build_builds_and_saves_when_missing(tmp_path, monkeypatch):
    """With no cache file present, load_or_build_pdb calls build_pdb, saves the
    result, and returns it -- without running a real BFS.
    """
    small = {((10, 0), (1, 0), (11, 0), (3, 0)): 0}
    monkeypatch.setattr(cube.pdb, "build_pdb", lambda: small)
    path = tmp_path / "pdb.pkl"

    result = load_or_build_pdb(path)

    assert result == small
    assert path.exists()
    assert load_pdb(path) == small


def test_load_or_build_uses_existing_cache_without_rebuilding(tmp_path, monkeypatch):
    """With a cache file already present, load_or_build_pdb returns its contents
    and never calls build_pdb. Path is passed as a str to prove str paths work.
    """
    sentinel = {((10, 0), (1, 0), (11, 0), (3, 0)): 0}
    path = tmp_path / "pdb.pkl"
    save_pdb(sentinel, path)

    def _should_not_run():
        raise AssertionError("should not rebuild")

    monkeypatch.setattr(cube.pdb, "build_pdb", _should_not_run)

    result = load_or_build_pdb(str(path))

    assert result == sentinel
