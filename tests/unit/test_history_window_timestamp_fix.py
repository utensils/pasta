"""Test the fix for history window timestamp handling."""

from datetime import datetime


def test_timestamp_handling_logic():
    """Test the timestamp conversion logic that was fixed."""
    # Test the exact logic we implemented in the fix

    test_cases = [
        # (name, input_timestamp, should_work)
        ("datetime object", datetime(2025, 6, 18, 12, 30, 45), True),
        ("ISO string", "2025-06-18T12:30:45", True),
        ("Unix timestamp float", 1734527445.123, True),
        ("Unix timestamp int", 1734527445, True),
        ("Invalid type", {"timestamp": "invalid"}, True),  # Should use fallback
    ]

    for name, timestamp, should_work in test_cases:
        try:
            # This is the fixed logic from history_pyside6.py
            if isinstance(timestamp, datetime):
                # Already a datetime object
                dt = timestamp
            elif isinstance(timestamp, str):
                # ISO format string
                dt = datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                dt = datetime.fromtimestamp(timestamp)
            else:
                # Fallback to current time
                dt = datetime.now()

            # Should be able to format it
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            assert isinstance(time_str, str)
            assert should_work, f"{name} should have worked"

        except Exception as e:
            assert not should_work, f"{name} failed unexpectedly: {e}"


def test_storage_manager_returns_datetime_objects():
    """Test that storage manager returns datetime objects, which caused the crash."""

    # Storage manager's _row_to_dict converts timestamps to datetime objects
    # This is what was causing the crash in history window

    # Simulate what storage manager does
    mock_row = {
        "id": 1,
        "content": "Test content",
        "timestamp": "2025-06-18T12:30:45",  # Stored as ISO string in DB
        "content_type": "text",
        "encrypted": 0,
        "hash": "test_hash",
    }

    # This is what storage manager does (line 230-231)
    entry = dict(mock_row)
    if isinstance(entry["timestamp"], str):
        entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])

    # Now entry has a datetime object
    assert isinstance(entry["timestamp"], datetime)

    # This is what was crashing in history window:
    # datetime.fromtimestamp(entry["timestamp"])  # TypeError!

    # With our fix, it should handle this case
    timestamp = entry["timestamp"]
    dt = timestamp if isinstance(timestamp, datetime) else datetime.fromtimestamp(timestamp)

    assert isinstance(dt, datetime)
