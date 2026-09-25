"""Reduce full edge state to just the 4 cross (D-face) edges: position slot + orientation."""

from cube.moves import EDGE_HOMES

SLOT_INDEX = {pos: i for i, (pos, d1, d2) in enumerate(EDGE_HOMES)}
CROSS_IDS = [frozenset(['D', 'F']), frozenset(['D', 'R']), frozenset(['D', 'B']), frozenset(['D', 'L'])]


def cross_key(cubies):
    """Return (slot, flip) for each cross piece (DF, DR, DB, DL).

    The reference direction for flip is: y-axis for top/bottom-layer slots (y != 0),
    z-axis for middle-layer slots (z != 0). flip=0 when the piece's D sticker points
    in the reference direction, flip=1 when flipped.
    """
    by_id = {c.id: c for c in cubies}
    result = []
    for cid in CROSS_IDS:
        c = by_id[cid]
        pos = c.pos
        slot = SLOT_INDEX[pos]
        if pos[1] != 0:
            primary_dir = (0, pos[1], 0)
        else:
            primary_dir = (0, 0, pos[2])
        oriented = 0 if c.stickers[primary_dir] == 'D' else 1
        result.append((slot, oriented))
    return tuple(result)
