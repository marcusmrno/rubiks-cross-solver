"""Parse a csTimer export into (scramble, time_ms, session) records.

Export shape (checked against a real export and csTimer's source):
- "session1", "session2", ...: lists of solves, each
  [[penalty, time_ms], scramble, comment, unix_timestamp].
  penalty is 0, 2000 (+2) or -1 (DNF). time_ms is always the raw time;
  csTimer adds the penalty when it shows the time.
- "properties"["sessionData"]: a JSON string mapping session number to
  {"name": ..., "opt": {"scrType": ...}}. No scrType means "333".
"""

import json

PENALTY_DNF = -1
WCA_3X3 = "333"


def load_solves(path):
    """Every non-DNF solve from the WCA 3x3 sessions, in file order.

    Sessions are picked by scramble type, not by their moves: 2x2 and Skewb
    scrambles use only R, U, F, L, B turns, so they'd parse as 3x3 scrambles
    and get wrong cross answers. One-handed 3x3 ("333oh") is left out too;
    its times aren't comparable to two-handed ones.
    """
    with open(path) as f:
        data = json.load(f)
    session_data = json.loads(data["properties"]["sessionData"])

    solves = []
    for num, meta in session_data.items():
        if meta["opt"].get("scrType", WCA_3X3) != WCA_3X3:
            continue
        key = f"session{num}"
        for (penalty, time_ms), scramble, *_ in data.get(key, []):
            if penalty == PENALTY_DNF:
                continue
            solves.append({"scramble": scramble, "time_ms": penalty + time_ms, "session": key})
    return solves
