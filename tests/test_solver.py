from cube.moves import MOVES, solved_edges, apply_move, apply_scramble
from cube.cross import cross_key
from cube.solver import solve_all_optimal

SCRAMBLE = "D2 R' D' F2 B2 U' R2 U' F2 D B2 U2 R' D R' B L2 F' U F2"

NON_CANONICAL = {('D', 'U'), ('R', 'L'), ('B', 'F')}  # opposite-face orders the solver never emits


def _enumerate_without_dedup(dist, scramble):
    """The solver's distance-pruned search with the opposite-face order rule removed."""
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
            ns = apply_move(state, mv)
            nk = cross_key(ns)
            if dist[nk] == remaining - 1:
                path.append(mv)
                dfs(ns, nk, remaining - 1, path, f)
                path.pop()

    dfs(start, start_key, d, [], None)
    return d, solutions


def _canonicalize(seq):
    """Swap adjacent D U / R L / B F pairs into U D / L R / F B until none are left."""
    seq = list(seq)
    changed = True
    while changed:
        changed = False
        for i in range(len(seq) - 1):
            if (seq[i][0], seq[i + 1][0]) in NON_CANONICAL:
                seq[i], seq[i + 1] = seq[i + 1], seq[i]
                changed = True
    return tuple(seq)


def test_intact_cross_zero_moves(dist):
    """R lifts the DR edge into the FR slot, U doesn't touch the middle layer,
    and R' puts DR back home, so the cross is intact and the empty sequence is
    the one and only optimal solution.
    """
    d, sols = solve_all_optimal(dist, "R U R' U'")
    assert d == 0
    assert sols == [[]]


def test_single_move_is_undone_by_its_inverse(dist):
    """A one-move scramble (other than U) is solved by exactly its inverse.
    The solution starts on the face the scramble ended on, so this also catches
    a solver that refuses to turn that face first.
    """
    inverse = {"": "'", "'": "", "2": "2"}
    for mv in MOVES:
        if mv.startswith("U"):
            continue
        assert solve_all_optimal(dist, mv) == (1, [[mv[0] + inverse[mv[1:]]]]), mv


def test_known_scramble_length_and_count(dist):
    """Pinned values for SCRAMBLE: optimal length 7 (straight from the table)
    and 56 deduped solutions, which the oracle test below reproduces a second way.
    """
    d, sols = solve_all_optimal(dist, SCRAMBLE)
    assert d == 7
    assert len(sols) == 56


def test_adjacent_axis_orders_are_both_kept(dist):
    """After U2, R2 brings DR home from UR and F2 brings DF home from UF, and
    neither turn touches the other's piece, so both orders solve the cross.
    R2 and F2 don't commute (both turn the FR edge), so the two orders leave the
    rest of the cube different: they are different solutions and both are kept.
    """
    d, sols = solve_all_optimal(dist, "R2 F2 U' F2 U' R2 F2")
    assert d == 3
    assert len(sols) == 2
    assert {tuple(s) for s in sols} == {('U2', 'R2', 'F2'), ('U2', 'F2', 'R2')}


def test_every_solution_is_real_optimal_and_distinct(dist):
    """Every returned solution actually solves the scrambled cross, has length
    exactly the optimal distance, and no two are duplicates.
    """
    _, sols = solve_all_optimal(dist, SCRAMBLE)
    solved_key = cross_key(solved_edges())
    for sol in sols:
        state = apply_scramble(solved_edges(), SCRAMBLE)
        for mv in sol:
            state = apply_move(state, mv)
        assert cross_key(state) == solved_key
        assert len(sol) == 7
    assert len({tuple(s) for s in sols}) == len(sols)


def test_canonical_order_for_opposite_faces(dist):
    """Consecutive moves never repeat a face and never appear as D-then-U,
    R-then-L, or B-then-F, while U-then-D, L-then-R, and F-then-B each show up:
    the dedup keeps one order on every axis instead of dropping both.
    """
    _, sols = solve_all_optimal(dist, SCRAMBLE)
    pairs = {(a[0], b[0]) for sol in sols for a, b in zip(sol, sol[1:])}
    assert all(fa != fb for fa, fb in pairs)
    assert not pairs & NON_CANONICAL
    assert {('U', 'D'), ('L', 'R'), ('F', 'B')} <= pairs


def test_against_enumeration_without_dedup(dist):
    """The same distance-pruned search with the opposite-face order rule removed
    finds 104 optimal sequences for SCRAMBLE. Putting every commuting
    opposite-face pair into U-D / L-R / F-B order collapses them to exactly the
    solver's 56. This checks the dedup rule against a second enumeration; both
    searches share `dist`, which the histogram test in test_pdb.py checks.
    """
    d, sols = solve_all_optimal(dist, SCRAMBLE)
    raw_d, raw = _enumerate_without_dedup(dist, SCRAMBLE)
    assert raw_d == d
    assert len(raw) == 104
    assert {_canonicalize(s) for s in raw} == {tuple(s) for s in sols}
