import pytest

import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """
    Use a fresh temporary SQLite database for each test to keep tests isolated.
    """
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DATABASE", str(db_path))
    database.init_database()
    yield
