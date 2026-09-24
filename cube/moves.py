"""Edge-only cube model. Corners are irrelevant to cross solving and are never tracked."""

from typing import NamedTuple


class Cubie(NamedTuple):
    id: frozenset   # the two faces this piece belongs between when solved, e.g. {'U', 'F'}; never changes
    pos: tuple      # where it is now, e.g. (0, 1, 1)
    stickers: dict  # direction each sticker points -> face it belongs on, e.g. {(0, 1, 0): 'U', (0, 0, 1): 'F'}


FACE_OF = {(1, 0, 0): 'R', (-1, 0, 0): 'L', (0, 1, 0): 'U', (0, -1, 0): 'D', (0, 0, 1): 'F', (0, 0, -1): 'B'}

MOVES = [f + suf for f in "URFDLB" for suf in ("", "'", "2")]


def rot(vec, face):
    """Rotate a position or sticker direction 90° clockwise, as seen looking at `face`."""
    x, y, z = vec
    if face == 'R': return (x, z, -y)
    if face == 'L': return (x, -z, y)
    if face == 'U': return (-z, y, x)
    if face == 'D': return (z, y, -x)
    if face == 'F': return (y, -x, z)
    if face == 'B': return (-y, x, z)
    raise ValueError(face)


def _layer_coord(face):
    """Return (axis, value) picking out the slab `face` turns: pieces where pos[axis] == value."""
    return {'R': (0, 1), 'L': (0, -1), 'U': (1, 1), 'D': (1, -1), 'F': (2, 1), 'B': (2, -1)}[face]


def _edge_homes():
    """List the 12 solved edges as (pos, d1, d2): where each sits and the two directions its stickers face."""
    homes = []
    for a in range(3):
        for b in range(a + 1, 3):
            for sa in (1, -1):
                for sb in (1, -1):
                    pos = [0, 0, 0]
                    pos[a] = sa
                    pos[b] = sb
                    d1 = [0, 0, 0]
                    d1[a] = sa
                    d2 = [0, 0, 0]
                    d2[b] = sb
                    homes.append((tuple(pos), tuple(d1), tuple(d2)))
    return homes


EDGE_HOMES = _edge_homes()


def solved_edges():
    """Return a fresh solved cube: 12 Cubies, in the same order as EDGE_HOMES."""
    cubies = []
    for pos, d1, d2 in EDGE_HOMES:
        cid = frozenset([FACE_OF[d1], FACE_OF[d2]])
        stickers = {d1: FACE_OF[d1], d2: FACE_OF[d2]}
        cubies.append(Cubie(id=cid, pos=pos, stickers=stickers))
    return cubies


def apply_cw(cubies, face):
    """Return a new cube with `face` turned one clockwise quarter turn.

    The input is never modified; pieces outside the turning slab are reused as-is.
    """
    axis, val = _layer_coord(face)
    new_cubies = []
    for c in cubies:
        if c.pos[axis] == val:
            new_pos = rot(c.pos, face)
            new_stickers = {rot(d, face): label for d, label in c.stickers.items()}
            new_cubies.append(Cubie(id=c.id, pos=new_pos, stickers=new_stickers))
        else:
            new_cubies.append(c)
    return new_cubies


def apply_move(cubies, move):
    """Apply one move like "R", "R'", or "R2" as 1, 3, or 2 clockwise quarter turns."""
    face = move[0]
    n = 2 if move.endswith('2') else (3 if move.endswith("'") else 1)
    for _ in range(n):
        cubies = apply_cw(cubies, face)
    return cubies


def apply_scramble(cubies, scramble):
    """Apply a space-separated move sequence, e.g. "R U R' U'", left to right."""
    for mv in scramble.split():
        cubies = apply_move(cubies, mv)
    return cubies


def is_solved(cubies):
    """True if every edge is home and facing the right way.

    Pairs cubies with EDGE_HOMES by list position, so it relies on the cube
    keeping solved_edges()' order (apply_cw preserves it).
    """
    return all(
        c.pos == p and c.stickers == {d1: FACE_OF[d1], d2: FACE_OF[d2]}
        for c, (p, d1, d2) in zip(cubies, EDGE_HOMES)
    )
