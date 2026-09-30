import pytest

from analysis.parse_cstimer import load_solves


def test_plus2_adds_penalty_and_dnf_is_dropped(write_export):
    """csTimer stores a +2 as [2000, raw_time] and adds the two when it shows
    the time, so the parser must add them too. A DNF ([-1, raw_time]) has no
    valid time and is dropped.
    """
    path = write_export(
        {"session1": [
            [[0, 12345], "R U R' U'", "", 1548020659],
            [[2000, 12345], "F2 R2 U'", "slow", 1548020702],
            [[-1, 9999], "L2 B2", "", 1548020732],
        ]},
        {"1": {"name": "3x3", "opt": {}}},
    )

    assert load_solves(path) == [
        {"scramble": "R U R' U'", "time_ms": 12345, "session": "session1", "turns": None},
        {"scramble": "F2 R2 U'", "time_ms": 14345, "session": "session1", "turns": None},
    ]


def test_smart_cube_turns_are_kept_with_their_times(write_export):
    """A smart-cube solve has a fifth field: [turns, "333"], where turns is
    one string of every turn and its time in ms since the first turn. It's
    split into (move, ms) pairs. A solve without the smart cube has no turns.
    """
    path = write_export(
        {"session1": [
            [[0, 1500], "R U R' U'", "", 1790720582, ["U@0 R@350 U'@700 R'@1500", "333"]],
            [[0, 12345], "F2 R2 U'", "", 1548020702],
        ]},
        {"1": {"name": "3x3", "opt": {}}},
    )

    assert [s["turns"] for s in load_solves(path)] == [
        [("U", 0), ("R", 350), ("U'", 700), ("R'", 1500)],
        None,
    ]


def test_only_wca_3x3_sessions_are_kept(write_export):
    """Sessions are picked by scramble type. A session with no scrType is 3x3
    (csTimer's default, like the real "3x3" session). The 2x2 scramble uses
    only valid 3x3 moves, so checking the moves alone would let it through.
    One-handed 3x3 is left out because its times aren't comparable.
    """
    path = write_export(
        {
            "session1": [[[0, 13009], "R U2 F'", "", 1548020659]],
            "session2": [[[0, 4188], "R U' F2 R'", "", 1548490391]],
            "session3": [[[0, 38178], "D2 B2 U'", "", 1545709371]],
            "session4": [[[0, 12500], "L' D B2", "", 1775772857]],
        },
        {
            "1": {"name": "3x3", "opt": {}},
            "2": {"name": "2x2", "opt": {"scrType": "222so"}},
            "3": {"name": "OH", "opt": {"scrType": "333oh"}},
            "4": {"name": "4", "opt": {"scrType": "333"}},
        },
    )

    assert [s["session"] for s in load_solves(path)] == ["session1", "session4"]


def test_unexpected_time_shape_fails_loudly(write_export):
    """Multi-phase timing adds more numbers to [penalty, time]. That format
    isn't confirmed, so the parser should crash instead of guessing.
    """
    path = write_export(
        {"session1": [[[0, 13009, 4000], "R U2 F'", "", 1548020659]]},
        {"1": {"name": "3x3", "opt": {}}},
    )

    with pytest.raises(ValueError):
        load_solves(path)
