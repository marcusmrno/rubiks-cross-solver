import pytest

from cube.moves import MOVES, solved_edges, apply_move, apply_scramble, apply_cw, is_solved

INVERSES = {}
for f in "URFDLB":
    INVERSES[f] = f + "'"
    INVERSES[f + "'"] = f
    INVERSES[f + "2"] = f + "2"


# --- is_solved: most other tests assert through it, so it must be able to say "no" ---

def test_is_solved_true_only_for_solved_cube():
    """A fresh cube is solved, and every one of the 18 moves unsolves it."""
    assert is_solved(solved_edges())
    for mv in MOVES:
        assert not is_solved(apply_move(solved_edges(), mv)), mv


def test_is_solved_detects_flipped_edge():
    """An edge in its home slot but flipped (labels swapped) is not solved."""
    cubies = solved_edges()
    (d1, a), (d2, b) = cubies[0].stickers.items()
    cubies[0] = cubies[0]._replace(stickers={d1: b, d2: a})
    assert not is_solved(cubies)


# --- structural behavior of a single turn ---

@pytest.mark.parametrize("face", "URFDLB")
def test_turn_moves_exactly_that_faces_four_edges(face):
    """Turning a face moves its 4 edges and leaves the other 8 untouched (not the whole cube)."""
    before = solved_edges()
    after = apply_move(before, face)
    moved = {a.id for a, b in zip(after, before) if a != b}
    assert moved == {c.id for c in before if face in c.id}


def test_turning_does_not_modify_input():
    """Moves return a new cube; the one passed in stays exactly as it was."""
    cube = solved_edges()
    snapshot = [c._replace(stickers=dict(c.stickers)) for c in cube]
    apply_move(cube, "R")
    assert cube == snapshot


def test_scramble_applies_moves_left_to_right():
    """'R U' means R first, then U. Order matters because R and U don't commute."""
    expected = apply_move(apply_move(solved_edges(), "R"), "U")
    assert apply_scramble(solved_edges(), "R U") == expected


# --- algebra: moves behave consistently with each other ---

def test_four_quarter_turns_is_identity():
    """Any face turned clockwise 4 times returns to where it started."""
    for f in "URFDLB":
        c = solved_edges()
        for _ in range(4):
            c = apply_cw(c, f)
        assert is_solved(c)


def test_move_then_inverse_is_identity():
    """Every move undone by its inverse (R/R', R2/R2) returns to solved; also checks ' and 2 parsing."""
    for mv, inv in INVERSES.items():
        c = apply_move(solved_edges(), mv)
        c = apply_move(c, inv)
        assert is_solved(c)


def test_opposite_faces_commute():
    """Opposite faces never share pieces, so their order doesn't matter."""
    assert apply_scramble(solved_edges(), "U D") == apply_scramble(solved_edges(), "D U")
    assert apply_scramble(solved_edges(), "R L") == apply_scramble(solved_edges(), "L R")


def test_sexy_move_has_order_six():
    """(R U R' U') repeated 6 times returns to solved — a known property of real cubes."""
    c = apply_scramble(solved_edges(), ("R U R' U' " * 6).strip())
    assert is_solved(c)


def test_long_scramble_undone_by_reverse_inverse():
    """A 20-move scramble is undone by its inverse moves in reverse order."""
    scramble = "R U R' U' F' U F U2 R U' R' D R U R' U' D' L U L'"
    moves = scramble.split()
    rev_inv = " ".join(INVERSES[m] for m in reversed(moves))
    c = apply_scramble(solved_edges(), scramble)
    c = apply_scramble(c, rev_inv)
    assert is_solved(c)


# --- ground truth: pins the model to a physical cube (algebra alone passes for a mirror image) ---

# Physical ground truth for each clockwise quarter turn (viewed from outside that face).
GROUND_TRUTH = [
    ("U", {"U", "F"}, (-1, 1, 0)),   # front goes left: UF -> UL
    ("D", {"D", "F"}, (1, -1, 0)),   # front goes right: DF -> DR
    ("R", {"F", "R"}, (1, 1, 0)),    # front goes up: FR -> UR
    ("L", {"U", "L"}, (-1, 0, 1)),   # top goes front: UL -> FL
    ("F", {"U", "F"}, (1, 0, 1)),    # top goes right: UF -> FR
    ("B", {"U", "B"}, (-1, 0, -1)),  # top goes left (seen from behind): UB -> BL
]


@pytest.mark.parametrize("move,piece,expected_pos", GROUND_TRUTH)
def test_each_face_turns_the_physical_direction(move, piece, expected_pos):
    """Each face turns clockwise, not counterclockwise, matching a real cube."""
    by_id = {c.id: c.pos for c in apply_move(solved_edges(), move)}
    assert by_id[frozenset(piece)] == expected_pos


def test_f_move_reorients_uf_edge():
    """Turning F carries UF to FR with its U sticker now facing right: orientation is tracked."""
    uf = {c.id: c for c in apply_move(solved_edges(), "F")}[frozenset({"U", "F"})]
    assert uf.stickers == {(1, 0, 0): 'U', (0, 0, 1): 'F'}
