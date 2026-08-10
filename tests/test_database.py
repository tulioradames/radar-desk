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

        assert database.schema_version() == 1
