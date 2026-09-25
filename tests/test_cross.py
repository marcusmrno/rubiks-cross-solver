from cube.moves import MOVES, solved_edges, apply_move, apply_scramble, is_solved
from cube.cross import cross_key


def test_solved_key_exact():
    """The solved key pins the slot numbering and DF/DR/DB/DL order."""
    assert cross_key(solved_edges()) == ((10, 0), (1, 0), (11, 0), (3, 0))


def test_u_moves_leave_key_unchanged():
    """U, U', and U2 never touch the cross pieces."""
    solved = solved_edges()
    for move in ["U", "U'", "U2"]:
        assert cross_key(apply_move(solved, move)) == cross_key(solved)


def test_all_non_u_moves_change_key():
    """Every move in MOVES not starting with 'U' changes the cross key."""
    solved = solved_edges()
    solved_key = cross_key(solved)
    for move in MOVES:
        if not move.startswith("U"):
            scrambled = apply_move(solved, move)
            assert cross_key(scrambled) != solved_key, f"Move {move} did not change the key"


def test_d_permutes_without_flipping():
    """A D turn permutes the cross pieces but keeps them all unflipped (flip=0)."""
    d_result = cross_key(apply_move(solved_edges(), "D"))
    assert d_result == ((1, 0), (11, 0), (3, 0), (10, 0))


def test_flip_ground_truth():
    """Single moves produce known flip states for each cross piece."""
    # After F: DF (index 0) is at slot 6, flipped
    assert cross_key(apply_move(solved_edges(), "F"))[0] == (6, 1)
    # After F2: DF is at slot 8, not flipped
    assert cross_key(apply_move(solved_edges(), "F2"))[0] == (8, 0)
    # After R: DR (index 1) is at slot 4, not flipped
    assert cross_key(apply_move(solved_edges(), "R"))[1] == (4, 0)
    # After B: DB (index 2) is at slot 5, flipped
    assert cross_key(apply_move(solved_edges(), "B"))[2] == (5, 1)
    # After L: DL (index 3) is at slot 7, not flipped
    assert cross_key(apply_move(solved_edges(), "L"))[3] == (7, 0)


def test_quarter_turn_rule():
    """U/D/R/L quarter turns leave every flip at 0; F/B quarter turns flip their piece.

    This is the standard edge-orientation convention: only F/B quarter turns flip edges.
    """
    solved = solved_edges()

    # U/D/R/L quarter turns don't flip
    for move in ["U", "D", "R", "L"]:
        key = cross_key(apply_move(solved, move))
        assert all(flip == 0 for _, flip in key), f"Move {move} flipped a piece"

    # F/B quarter turns flip exactly one piece
    for move in ["F", "B"]:
        key = cross_key(apply_move(solved, move))
        flips = [flip for _, flip in key]
        assert sum(flips) == 1, f"Move {move} should flip exactly one piece"


def test_ignores_non_cross_pieces():
    """The key is the same before and after a move that only affects non-cross pieces."""
    solved_key = cross_key(solved_edges())
    scrambled = apply_scramble(solved_edges(), "R U R' U'")
    # Non-cross edges have moved, so the cube is not solved
    assert not is_solved(scrambled)
    # But the cross key is unchanged
    assert cross_key(scrambled) == solved_key


def test_key_is_hashable():
    """The cross key works as a dict key and set member."""
    key = cross_key(solved_edges())
    d = {key: "solved"}
    assert d[key] == "solved"
    s = {key}
    assert key in s
