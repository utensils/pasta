"""Persistent storage for clipboard history."""

import contextlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet

from pasta.utils.security import SecurityManager


class StorageManager:
    """Manages persistent storage of clipboard history.

    This class handles SQLite database operations for storing
    and retrieving clipboard history with encryption support.

    Attributes:
        db_path: Path to the SQLite database
        encryption_key: Key for encrypting sensitive data
    """

    def __init__(self, db_path: str, encryption_key: Optional[bytes] = None) -> None:
        """Initialize the StorageManager.

        Args:
            db_path: Path to SQLite database file
            encryption_key: Optional encryption key for sensitive data
        """
        # Suppress unused argument warning - for future use
        _ = encryption_key  # noqa: F841
        self.db_path = db_path
        self._lock = threading.Lock()

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self.cipher = Fernet(self._get_or_create_key())

        # Use SecurityManager for sensitive data detection
        self._security_manager = SecurityManager()

        # Initialize database
        self._init_database()

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key.

        Returns:
            Encryption key bytes
        """
        key_file = Path(self.db_path).parent / ".pasta_key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key: bytes = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Create main table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clipboard_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    content_type TEXT NOT NULL,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    hash TEXT NOT NULL
                )
            """
            )

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON clipboard_history(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON clipboard_history(hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON clipboard_history(content_type)")

            # Create schema version table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """
            )

            # Set initial version
            cursor = conn.execute("SELECT version FROM schema_version")
            if cursor.fetchone() is None:
                conn.execute("INSERT INTO schema_version (version) VALUES (1)")

            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def is_sensitive(self, content: str) -> bool:
        """Check if content contains sensitive data.

        Args:
            content: Content to check

        Returns:
            True if sensitive data detected
        """
        return self._security_manager.is_sensitive(content)

    def save_entry(self, entry: dict[str, Any]) -> Optional[int]:
        """Save clipboard entry to database.

        Args:
            entry: Clipboard entry to save

        Returns:
            ID of saved entry or None on error
        """
        try:
            with self._lock:
                content = entry["content"]
                encrypted = self.is_sensitive(content)

                if encrypted:
                    # Encrypt sensitive content
                    content = self.cipher.encrypt(content.encode()).decode()

                with self._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        INSERT INTO clipboard_history
                        (content, timestamp, content_type, encrypted, hash)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            content,
                            entry["timestamp"],
                            entry["content_type"],
                            int(encrypted),
                            entry["hash"],
                        ),
                    )
                    conn.commit()
                    return cursor.lastrowid
        except sqlite3.Error:
            return None

    def get_entry(self, entry_id: int) -> Optional[dict[str, Any]]:
        """Get a specific entry by ID.

        Args:
            entry_id: ID of entry to retrieve

        Returns:
            Entry dict or None if not found
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM clipboard_history WHERE id = ?", (entry_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

    def get_entries(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Get multiple entries.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of entry dicts
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                    SELECT * FROM clipboard_history
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                    """,
                (limit, offset),
            )

            return [self._row_to_dict(row) for row in cursor]

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert database row to dictionary.

        Args:
            row: Database row

        Returns:
            Entry dictionary
        """
        entry = dict(row)

        # Decrypt if necessary
        if entry["encrypted"]:
            with contextlib.suppress(Exception):
                # Decryption failed, return as-is
                entry["content"] = self.cipher.decrypt(entry["content"].encode()).decode()

        # Convert timestamp string to datetime
        if isinstance(entry["timestamp"], str):
            entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])

        return entry

    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if deleted, False otherwise
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM clipboard_history WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def search_entries(self, query: str) -> list[dict[str, Any]]:
        """Search entries by content.

        Args:
            query: Search query

        Returns:
            List of matching entries
        """
        with self._lock, self._get_connection() as conn:
            # Don't search encrypted content
            cursor = conn.execute(
                """
                    SELECT * FROM clipboard_history
                    WHERE encrypted = 0 AND content LIKE ?
                    ORDER BY timestamp DESC
                    """,
                (f"%{query}%",),
            )

            return [self._row_to_dict(row) for row in cursor]

    def cleanup_old_entries(self, days: int = 30) -> None:
        """Delete entries older than specified days.

        Args:
            days: Number of days to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self._lock, self._get_connection() as conn:
            conn.execute(
                "DELETE FROM clipboard_history WHERE timestamp < ?",
                (cutoff_date,),
            )
            conn.commit()

    def get_history(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Get clipboard history entries.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of history entries
        """
        return self.get_entries(limit=limit, offset=offset)

    def clear_history(self) -> None:
        """Clear all clipboard history."""
        with self._lock, self._get_connection() as conn:
            conn.execute("DELETE FROM clipboard_history")
            conn.commit()

    def get_statistics(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Statistics dictionary
        """
        with self._lock, self._get_connection() as conn:
            # Total entries
            total = conn.execute("SELECT COUNT(*) FROM clipboard_history").fetchone()[0]

            # Entries by type
            type_stats = {}
            cursor = conn.execute(
                """
                    SELECT content_type, COUNT(*) as count
                    FROM clipboard_history
                    GROUP BY content_type
                    """
            )
            for row in cursor:
                type_stats[row["content_type"]] = row["count"]

            # Database size
            db_size = Path(self.db_path).stat().st_size

            return {
                "total_entries": total,
                "entries_by_type": type_stats,
                "database_size": db_size,
            }

    def export_to_json(self) -> str:
        """Export all entries to JSON.

        Returns:
            JSON string of entries
        """
        entries = self.get_entries(limit=10000)  # Get all entries

        # Convert datetime objects to strings
        for entry in entries:
            entry["timestamp"] = entry["timestamp"].isoformat()

        return json.dumps(entries, indent=2)

    def import_from_json(self, json_data: str) -> int:
        """Import entries from JSON.

        Args:
            json_data: JSON string of entries

        Returns:
            Number of entries imported
        """
        entries = json.loads(json_data)
        count = 0

        for entry in entries:
            # Convert timestamp string to datetime
            if isinstance(entry["timestamp"], str):
                entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])

            if self.save_entry(entry):
                count += 1

        return count

    def rotate_encryption_key(self) -> None:
        """Rotate encryption key and re-encrypt all sensitive data.

        This method generates a new encryption key and re-encrypts
        all sensitive data in the database with the new key.
        """
        # Generate new key
        new_key = Fernet.generate_key()
        new_cipher = Fernet(new_key)

        # Re-encrypt all sensitive entries
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute("SELECT id, content FROM clipboard_history WHERE encrypted = 1")

            for row in cursor.fetchall():
                # Decrypt with old key
                decrypted = self.cipher.decrypt(row["content"].encode()).decode()

                # Encrypt with new key
                encrypted = new_cipher.encrypt(decrypted.encode()).decode()

                # Update in database
                conn.execute("UPDATE clipboard_history SET content = ? WHERE id = ?", (encrypted, row["id"]))

            conn.commit()

        # Update cipher and save new key
        self.cipher = new_cipher
        key_file = Path(self.db_path).parent / ".pasta_key"
        with open(key_file, "wb") as f:
            f.write(new_key)
        os.chmod(key_file, 0o600)
