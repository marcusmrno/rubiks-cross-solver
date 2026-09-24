import pytest

from cube.moves import solved_edges, apply_move, apply_scramble, apply_cw, is_solved

INVERSES = {}
for f in "URFDLB":
    INVERSES[f] = f + "'"
    INVERSES[f + "'"] = f
    INVERSES[f + "2"] = f + "2"


def test_four_quarter_turns_is_identity():
    for f in "URFDLB":
        c = solved_edges()
        for _ in range(4):
            c = apply_cw(c, f)
        assert is_solved(c)


def test_move_then_inverse_is_identity():
    for mv, inv in INVERSES.items():
        c = apply_move(solved_edges(), mv)
        c = apply_move(c, inv)
        assert is_solved(c)


def test_opposite_faces_commute():
    assert apply_scramble(solved_edges(), "U D") == apply_scramble(solved_edges(), "D U")
    assert apply_scramble(solved_edges(), "R L") == apply_scramble(solved_edges(), "L R")


def test_sexy_move_has_order_six():
    c = apply_scramble(solved_edges(), ("R U R' U' " * 6).strip())
    assert is_solved(c)


def test_long_scramble_undone_by_reverse_inverse():
    scramble = "R U R' U' F' U F U2 R U' R' D R U R' U' D' L U L'"
    moves = scramble.split()
    rev_inv = " ".join(INVERSES[m] for m in reversed(moves))
    c = apply_scramble(solved_edges(), scramble)
    c = apply_scramble(c, rev_inv)
    assert is_solved(c)


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
    by_id = {c['id']: c['pos'] for c in apply_move(solved_edges(), move)}
    assert by_id[frozenset(piece)] == expected_pos


def test_f_move_reorients_uf_edge():
    uf = {c['id']: c for c in apply_move(solved_edges(), "F")}[frozenset({"U", "F"})]
    assert uf['stickers'] == {(1, 0, 0): 'U', (0, 0, 1): 'F'}
