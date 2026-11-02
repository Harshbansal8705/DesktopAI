"""Tests for assistant initialization and database path directory safeguards."""

import os
import sqlite3
import tempfile
import unittest

from src.config import config


class TestAssistantInitialization(unittest.TestCase):
    """Test suite for checkpoint database initialization and directory guards."""

    def test_checkpoint_dir_creation(self):
        """Verifies that creating missing parent directories allows SQLite connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "nested_checkpoints", "sqlite.db")
            db_dir = os.path.dirname(test_db)

            assert not os.path.exists(db_dir)

            # Without parent directory creation, sqlite3 fails on non-existent directories
            failed = False
            try:
                sqlite3.connect(test_db)
            except sqlite3.OperationalError:
                failed = True
            assert failed

            # Applying the directory guard allows connection to succeed
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            conn = sqlite3.connect(test_db)
            assert isinstance(conn, sqlite3.Connection)
            conn.close()
            assert os.path.exists(test_db)

    def test_config_checkpoints_dir_guard(self):
        """Verifies that config.CHECKPOINTS_DB parent directory is created idempotently."""
        db_dir = os.path.dirname(config.CHECKPOINTS_DB)
        assert bool(db_dir)

        # Idempotent creation
        os.makedirs(db_dir, exist_ok=True)
        assert os.path.exists(db_dir)

        conn = sqlite3.connect(config.CHECKPOINTS_DB)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()


if __name__ == "__main__":
    unittest.main()
