import pytest

from cube.pdb import build_pdb


@pytest.fixture(scope="session")
def dist():
    """Build the table once per test session; every test that takes `dist` shares it."""
    return build_pdb()
