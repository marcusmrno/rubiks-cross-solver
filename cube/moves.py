"""Edge-only cube model. Corners are irrelevant to cross solving and are never tracked."""

COLOR_OF = {(1, 0, 0): 'R', (-1, 0, 0): 'L', (0, 1, 0): 'U', (0, -1, 0): 'D', (0, 0, 1): 'F', (0, 0, -1): 'B'}

MOVES = [f + suf for f in "URFDLB" for suf in ("", "'", "2")]


def rot(vec, face):
    x, y, z = vec
    if face == 'R': return (x, z, -y)
    if face == 'L': return (x, -z, y)
    if face == 'U': return (-z, y, x)
    if face == 'D': return (z, y, -x)
    if face == 'F': return (y, -x, z)
    if face == 'B': return (-y, x, z)
    raise ValueError(face)


def _layer_coord(face):
    return {'R': (0, 1), 'L': (0, -1), 'U': (1, 1), 'D': (1, -1), 'F': (2, 1), 'B': (2, -1)}[face]


def _edge_homes():
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
    cubies = []
    for pos, d1, d2 in EDGE_HOMES:
        cid = frozenset([COLOR_OF[d1], COLOR_OF[d2]])
        stickers = {d1: COLOR_OF[d1], d2: COLOR_OF[d2]}
        cubies.append({'id': cid, 'pos': pos, 'stickers': stickers})
    return cubies


def apply_cw(cubies, face):
    axis, val = _layer_coord(face)
    new_cubies = []
    for c in cubies:
        if c['pos'][axis] == val:
            new_pos = rot(c['pos'], face)
            new_stickers = {rot(d, face): col for d, col in c['stickers'].items()}
            new_cubies.append({'id': c['id'], 'pos': new_pos, 'stickers': new_stickers})
        else:
            new_cubies.append(c)
    return new_cubies


def apply_move(cubies, move):
    face = move[0]
    n = 2 if move.endswith('2') else (3 if move.endswith("'") else 1)
    for _ in range(n):
        cubies = apply_cw(cubies, face)
    return cubies


def apply_scramble(cubies, scramble):
    for mv in scramble.split():
        cubies = apply_move(cubies, mv)
    return cubies


def is_solved(cubies):
    return all(
        c['pos'] == p and c['stickers'] == {d1: COLOR_OF[d1], d2: COLOR_OF[d2]}
        for c, (p, d1, d2) in zip(cubies, EDGE_HOMES)
    )
