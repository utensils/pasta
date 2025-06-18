"""Tests for the StorageManager module."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from pasta.core.storage import StorageManager


class TestStorageManager:
    """Test cases for StorageManager."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database path."""
        return tmp_path / "test_pasta.db"

    @pytest.fixture
    def manager(self, temp_db):
        """Create a StorageManager instance for testing."""
        return StorageManager(db_path=str(temp_db))

    def test_initialization(self, manager, temp_db):
        """Test StorageManager initializes correctly."""
        assert manager.db_path == str(temp_db)
        assert hasattr(manager, "cipher")
        assert hasattr(manager, "sensitive_patterns")
        assert Path(temp_db).exists()  # Database should be created

    def test_database_creation(self, temp_db):
        """Test database and tables are created on initialization."""
        StorageManager(db_path=str(temp_db))  # Creates DB on init

        # Check database exists
        assert Path(temp_db).exists()

        # Check tables exist
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        # Check clipboard_history table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clipboard_history'")
        assert cursor.fetchone() is not None

        # Check columns
        cursor.execute("PRAGMA table_info(clipboard_history)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {"id", "content", "timestamp", "content_type", "encrypted", "hash"}
        assert expected_columns.issubset(columns)

        conn.close()

    def test_encryption_key_generation(self, manager):
        """Test encryption key is generated properly."""
        assert manager.cipher is not None
        assert isinstance(manager.cipher, Fernet)

    def test_encryption_key_persistence(self, temp_db):
        """Test encryption key is persisted and loaded correctly."""
        # Create first manager
        manager1 = StorageManager(db_path=str(temp_db))
        key1 = manager1._get_or_create_key()

        # Create second manager - should use same key
        manager2 = StorageManager(db_path=str(temp_db))
        key2 = manager2._get_or_create_key()

        assert key1 == key2

    def test_save_entry_unencrypted(self, manager):
        """Test saving unencrypted clipboard entry."""
        entry = {
            "content": "Simple text",
            "timestamp": datetime.now(),
            "content_type": "text",
            "hash": "abc123",
        }

        entry_id = manager.save_entry(entry)

        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_save_entry_encrypted(self, manager):
        """Test saving encrypted sensitive clipboard entry."""
        entry = {
            "content": "password: secret123",
            "timestamp": datetime.now(),
            "content_type": "text",
            "hash": "def456",
        }

        entry_id = manager.save_entry(entry)

        assert isinstance(entry_id, int)

        # Verify it was encrypted in database
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content, encrypted FROM clipboard_history WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[1] == 1  # encrypted flag
        assert row[0] != "password: secret123"  # content is encrypted

    def test_retrieve_entry(self, manager):
        """Test retrieving saved entry."""
        original = {
            "content": "Test content",
            "timestamp": datetime.now(),
            "content_type": "text",
            "hash": "test123",
        }

        entry_id = manager.save_entry(original)
        retrieved = manager.get_entry(entry_id)

        assert retrieved is not None
        assert retrieved["content"] == original["content"]
        assert retrieved["content_type"] == original["content_type"]
        assert retrieved["hash"] == original["hash"]

    def test_retrieve_encrypted_entry(self, manager):
        """Test retrieving and decrypting sensitive entry."""
        original = {
            "content": "api_key: sk-1234567890",
            "timestamp": datetime.now(),
            "content_type": "text",
            "hash": "api123",
        }

        entry_id = manager.save_entry(original)
        retrieved = manager.get_entry(entry_id)

        assert retrieved is not None
        assert retrieved["content"] == original["content"]  # Should be decrypted

    def test_get_entries_with_limit(self, manager):
        """Test retrieving multiple entries with limit."""
        # Save multiple entries
        for i in range(10):
            entry = {
                "content": f"Entry {i}",
                "timestamp": datetime.now(),
                "content_type": "text",
                "hash": f"hash{i}",
            }
            manager.save_entry(entry)

        # Get limited entries
        entries = manager.get_entries(limit=5)

        assert len(entries) == 5
        # Should be in reverse chronological order
        assert entries[0]["content"] == "Entry 9"

    def test_get_entries_with_offset(self, manager):
        """Test retrieving entries with offset."""
        # Save multiple entries
        for i in range(10):
            entry = {
                "content": f"Entry {i}",
                "timestamp": datetime.now(),
                "content_type": "text",
                "hash": f"hash{i}",
            }
            manager.save_entry(entry)

        # Get entries with offset
        entries = manager.get_entries(limit=5, offset=5)

        assert len(entries) == 5
        assert entries[0]["content"] == "Entry 4"

    def test_delete_entry(self, manager):
        """Test deleting an entry."""
        entry = {
            "content": "To be deleted",
            "timestamp": datetime.now(),
            "content_type": "text",
            "hash": "delete123",
        }

        entry_id = manager.save_entry(entry)

        # Delete entry
        result = manager.delete_entry(entry_id)
        assert result is True

        # Verify it's gone
        retrieved = manager.get_entry(entry_id)
        assert retrieved is None

    def test_delete_nonexistent_entry(self, manager):
        """Test deleting entry that doesn't exist."""
        result = manager.delete_entry(9999)
        assert result is False

    def test_sensitive_data_detection(self, manager):
        """Test detection of various sensitive data patterns."""
        # Test cases
        sensitive_cases = [
            "password: mysecret",
            "api_key: sk-1234567890",
            "token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "secret: abcd1234",
            "123-45-6789",  # SSN
            "4532 1234 5678 9010",  # Credit card
            "john@example.com",  # Email
        ]

        for content in sensitive_cases:
            assert manager.is_sensitive(content) is True

        # Non-sensitive cases
        non_sensitive_cases = [
            "Hello world",
            "This is regular text",
            "https://example.com",
            "2024-01-01",
        ]

        for content in non_sensitive_cases:
            assert manager.is_sensitive(content) is False

    def test_search_entries(self, manager):
        """Test searching entries by content."""
        # Save entries
        entries = [
            {"content": "Python code example", "timestamp": datetime.now(), "content_type": "text", "hash": "py1"},
            {"content": "JavaScript function", "timestamp": datetime.now(), "content_type": "text", "hash": "js1"},
            {"content": "Python tutorial", "timestamp": datetime.now(), "content_type": "text", "hash": "py2"},
        ]

        for entry in entries:
            manager.save_entry(entry)

        # Search for Python
        results = manager.search_entries("Python")
        assert len(results) == 2
        assert all("Python" in r["content"] for r in results)

    def test_search_encrypted_entries(self, manager):
        """Test searching works with encrypted entries."""
        # Save sensitive entry
        entry = {
            "content": "password: python123",
            "timestamp": datetime.now(),
            "content_type": "text",
            "hash": "pwd1",
        }
        manager.save_entry(entry)

        # Should not find encrypted content
        results = manager.search_entries("python123")
        assert len(results) == 0

    def test_data_retention_cleanup(self, manager):
        """Test automatic cleanup of old entries."""
        # Save old and new entries
        old_date = datetime.now() - timedelta(days=31)
        new_date = datetime.now()

        # Mock timestamp for old entry
        with patch("pasta.core.storage.datetime") as mock_dt:
            mock_dt.now.return_value = old_date
            manager.save_entry(
                {
                    "content": "Old entry",
                    "timestamp": old_date,
                    "content_type": "text",
                    "hash": "old1",
                }
            )

        # Save new entry normally
        manager.save_entry(
            {
                "content": "New entry",
                "timestamp": new_date,
                "content_type": "text",
                "hash": "new1",
            }
        )

        # Run cleanup (30 days retention)
        manager.cleanup_old_entries(days=30)

        # Only new entry should remain
        entries = manager.get_entries()
        assert len(entries) == 1
        assert entries[0]["content"] == "New entry"

    def test_get_statistics(self, manager):
        """Test getting storage statistics."""
        # Save various entries
        for i in range(5):
            manager.save_entry(
                {
                    "content": f"Entry {i}",
                    "timestamp": datetime.now(),
                    "content_type": "text" if i < 3 else "url",
                    "hash": f"hash{i}",
                }
            )

        stats = manager.get_statistics()

        assert stats["total_entries"] == 5
        assert stats["entries_by_type"]["text"] == 3
        assert stats["entries_by_type"]["url"] == 2
        assert "database_size" in stats

    def test_export_entries(self, manager):
        """Test exporting entries to JSON."""
        # Save entries
        for i in range(3):
            manager.save_entry(
                {
                    "content": f"Entry {i}",
                    "timestamp": datetime.now(),
                    "content_type": "text",
                    "hash": f"hash{i}",
                }
            )

        # Export to JSON
        export_data = manager.export_to_json()

        assert isinstance(export_data, str)
        parsed = json.loads(export_data)
        assert len(parsed) == 3

    def test_import_entries(self, manager):
        """Test importing entries from JSON."""
        # Create import data
        import_data = [
            {
                "content": "Imported 1",
                "timestamp": datetime.now().isoformat(),
                "content_type": "text",
                "hash": "imp1",
            },
            {
                "content": "Imported 2",
                "timestamp": datetime.now().isoformat(),
                "content_type": "url",
                "hash": "imp2",
            },
        ]

        json_data = json.dumps(import_data)
        count = manager.import_from_json(json_data)

        assert count == 2

        # Verify imported
        entries = manager.get_entries()
        assert len(entries) == 2

    def test_database_error_handling(self, manager):
        """Test handling of database errors."""
        # Corrupt the database connection
        with patch.object(manager, "_get_connection", side_effect=sqlite3.Error("Database error")):
            # Should handle error gracefully
            entry_id = manager.save_entry(
                {
                    "content": "Test",
                    "timestamp": datetime.now(),
                    "content_type": "text",
                    "hash": "test",
                }
            )
            assert entry_id is None

    def test_concurrent_access(self, manager):
        """Test thread-safe concurrent access."""
        import threading

        results = []

        def save_entry(index):
            entry_id = manager.save_entry(
                {
                    "content": f"Concurrent {index}",
                    "timestamp": datetime.now(),
                    "content_type": "text",
                    "hash": f"concurrent{index}",
                }
            )
            results.append(entry_id)

        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=save_entry, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All saves should succeed
        assert len(results) == 5
        assert all(r is not None for r in results)

    def test_database_migration(self, temp_db):
        """Test database schema migration."""
        # Create manager - should handle any migrations
        StorageManager(db_path=str(temp_db))  # Creates DB with migrations

        # Check version table exists
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_performance_indexing(self, temp_db):
        """Test that appropriate indexes are created."""
        StorageManager(db_path=str(temp_db))  # Creates DB with indexes

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        # Should have indexes on commonly queried columns
        expected_indexes = {"idx_timestamp", "idx_hash", "idx_content_type"}
        assert expected_indexes.issubset(indexes)

        conn.close()
