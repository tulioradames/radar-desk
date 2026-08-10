import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from radar_desk.data.database import Database, SCHEMA_VERSION


def test_database_initializes_and_is_healthy() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "test.sqlite3"
        database = Database(path)

        database.initialize()

        assert path.exists()
        assert database.health_check() is True
        assert database.schema_version() == SCHEMA_VERSION


def test_database_initialization_is_idempotent() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")

        database.initialize()
        database.initialize()

        assert database.schema_version() == SCHEMA_VERSION


def test_version_two_creates_ticket_tables() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()

        with database.connect() as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

        assert "tickets" in tables
        assert "protocol_sequences" in tables


def test_existing_version_one_database_is_migrated() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "legacy.sqlite3"
        connection = sqlite3.connect(path)
        try:
            connection.execute(
                """
                CREATE TABLE schema_info (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute("INSERT INTO schema_info (id, version) VALUES (1, 1)")
            connection.commit()
        finally:
            connection.close()

        database = Database(path)
        database.initialize()

        assert database.schema_version() == SCHEMA_VERSION
        with database.connect() as connection:
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE name = 'tickets'"
            ).fetchone()
        assert table is not None
