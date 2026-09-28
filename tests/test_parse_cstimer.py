import json

import pytest

from analysis.parse_cstimer import load_solves


def _export(tmp_path, sessions, session_data):
    """Write a csTimer-shaped export: one "sessionN" list per session, plus
    "properties"["sessionData"], which csTimer stores as a JSON *string*.
    """
    data = dict(sessions)
    data["properties"] = {"sessionData": json.dumps(session_data)}
    path = tmp_path / "export.txt"
    path.write_text(json.dumps(data))
    return str(path)


def test_plus2_adds_penalty_and_dnf_is_dropped(tmp_path):
    """csTimer stores a +2 as [2000, raw_time] and adds the two when it shows
    the time, so the parser must add them too. A DNF ([-1, raw_time]) has no
    valid time and is dropped.
    """
    path = _export(
        tmp_path,
        {"session1": [
            [[0, 12345], "R U R' U'", "", 1548020659],
            [[2000, 12345], "F2 R2 U'", "slow", 1548020702],
            [[-1, 9999], "L2 B2", "", 1548020732],
        ]},
        {"1": {"name": "3x3", "opt": {}}},
    )

    assert load_solves(path) == [
        {"scramble": "R U R' U'", "time_ms": 12345, "session": "session1"},
        {"scramble": "F2 R2 U'", "time_ms": 14345, "session": "session1"},
    ]


def test_only_wca_3x3_sessions_are_kept(tmp_path):
    """Sessions are picked by scramble type. A session with no scrType is 3x3
    (csTimer's default, like the real "3x3" session). The 2x2 scramble uses
    only valid 3x3 moves, so checking the moves alone would let it through.
    One-handed 3x3 is left out because its times aren't comparable.
    """
    path = _export(
        tmp_path,
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


def test_unexpected_time_shape_fails_loudly(tmp_path):
    """Multi-phase timing adds more numbers to [penalty, time]. That format
    isn't confirmed, so the parser should crash instead of guessing.
    """
    path = _export(
        tmp_path,
        {"session1": [[[0, 13009, 4000], "R U2 F'", "", 1548020659]]},
        {"1": {"name": "3x3", "opt": {}}},
    )

    with pytest.raises(ValueError):
        load_solves(path)
