import json

import pytest

from cube.pdb import build_pdb


@pytest.fixture(scope="session")
def dist():
    """Build the table once per test session; every test that takes `dist` shares it."""
    return build_pdb()


@pytest.fixture
def write_export(tmp_path):
    """Return a function that writes a csTimer-shaped export and returns its
    path: one "sessionN" list per session, plus "properties"["sessionData"],
    which csTimer stores as a JSON *string*.
    """
    def write(sessions, session_data):
        data = dict(sessions)
        data["properties"] = {"sessionData": json.dumps(session_data)}
        path = tmp_path / "export.txt"
        path.write_text(json.dumps(data))
        return str(path)

    return write
