"""Tests for the Snippet system."""

from datetime import datetime

import pytest

from pasta.core.snippets import Snippet, SnippetManager


class TestSnippet:
    """Test cases for Snippet data class."""

    def test_snippet_creation(self):
        """Test creating a snippet."""
        snippet = Snippet(
            id="test-123",
            name="Email Signature",
            content="Best regards,\nJohn Doe",
            category="signatures",
            hotkey="ctrl+shift+s",
            tags=["email", "work"],
        )

        assert snippet.id == "test-123"
        assert snippet.name == "Email Signature"
        assert snippet.content == "Best regards,\nJohn Doe"
        assert snippet.category == "signatures"
        assert snippet.hotkey == "ctrl+shift+s"
        assert snippet.tags == ["email", "work"]
        assert isinstance(snippet.created_at, datetime)
        assert isinstance(snippet.updated_at, datetime)
        assert snippet.use_count == 0

    def test_snippet_defaults(self):
        """Test snippet with default values."""
        snippet = Snippet(name="Test", content="Content")

        assert snippet.id is not None  # Should generate ID
        assert snippet.category == "general"
        assert snippet.hotkey == ""
        assert snippet.tags == []
        assert snippet.use_count == 0

    def test_snippet_to_dict(self):
        """Test converting snippet to dictionary."""
        snippet = Snippet(id="test-123", name="Test", content="Content", tags=["tag1", "tag2"])

        data = snippet.to_dict()

        assert data["id"] == "test-123"
        assert data["name"] == "Test"
        assert data["content"] == "Content"
        assert data["tags"] == ["tag1", "tag2"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_snippet_from_dict(self):
        """Test creating snippet from dictionary."""
        data = {
            "id": "test-123",
            "name": "Test",
            "content": "Content",
            "category": "custom",
            "hotkey": "ctrl+t",
            "tags": ["tag1"],
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "use_count": 5,
        }

        snippet = Snippet.from_dict(data)

        assert snippet.id == "test-123"
        assert snippet.name == "Test"
        assert snippet.content == "Content"
        assert snippet.category == "custom"
        assert snippet.hotkey == "ctrl+t"
        assert snippet.tags == ["tag1"]
        assert snippet.use_count == 5

    def test_snippet_validation(self):
        """Test snippet validation."""
        # Valid snippet
        snippet = Snippet(name="Test", content="Content")
        assert snippet.validate() is True

        # Empty name
        with pytest.raises(ValueError, match="Snippet name cannot be empty"):
            Snippet(name="", content="Content").validate()

        # Empty content
        with pytest.raises(ValueError, match="Snippet content cannot be empty"):
            Snippet(name="Test", content="").validate()

        # Invalid hotkey format
        with pytest.raises(ValueError, match="Invalid hotkey format"):
            Snippet(name="Test", content="Content", hotkey="invalid").validate()

    def test_snippet_update(self):
        """Test updating snippet."""
        import time

        snippet = Snippet(name="Test", content="Content")
        original_updated = snippet.updated_at

        # Small delay to ensure timestamp difference
        time.sleep(0.001)

        # Update content
        snippet.update(content="New Content", tags=["new"])

        assert snippet.content == "New Content"
        assert snippet.tags == ["new"]
        assert snippet.updated_at > original_updated

    def test_snippet_increment_use_count(self):
        """Test incrementing use count."""
        snippet = Snippet(name="Test", content="Content")
        assert snippet.use_count == 0

        snippet.increment_use_count()
        assert snippet.use_count == 1

        snippet.increment_use_count()
        assert snippet.use_count == 2


class TestSnippetManager:
    """Test cases for SnippetManager."""

    @pytest.fixture
    def temp_snippets_file(self, tmp_path):
        """Create a temporary snippets file."""
        return tmp_path / "snippets.json"

    @pytest.fixture
    def manager(self, temp_snippets_file):
        """Create a SnippetManager with temp file."""
        return SnippetManager(snippets_path=temp_snippets_file)

    def test_initialization(self, manager, temp_snippets_file):
        """Test SnippetManager initialization."""
        assert manager.snippets == {}
        assert manager.snippets_path == temp_snippets_file

    def test_add_snippet(self, manager):
        """Test adding a snippet."""
        snippet = manager.add_snippet(name="Test Snippet", content="Test Content", category="test")

        assert snippet.id in manager.snippets
        assert snippet.name == "Test Snippet"
        assert snippet.content == "Test Content"
        assert snippet.category == "test"

    def test_get_snippet(self, manager):
        """Test getting a snippet by ID."""
        snippet = manager.add_snippet(name="Test", content="Content")

        retrieved = manager.get_snippet(snippet.id)
        assert retrieved == snippet

        # Non-existent snippet
        assert manager.get_snippet("non-existent") is None

    def test_update_snippet(self, manager):
        """Test updating a snippet."""
        snippet = manager.add_snippet(name="Test", content="Content")

        updated = manager.update_snippet(snippet.id, name="Updated", content="New Content")

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.content == "New Content"
        assert updated.id == snippet.id

        # Update non-existent snippet
        assert manager.update_snippet("non-existent", name="Test") is None

    def test_delete_snippet(self, manager):
        """Test deleting a snippet."""
        snippet = manager.add_snippet(name="Test", content="Content")

        assert manager.delete_snippet(snippet.id) is True
        assert snippet.id not in manager.snippets

        # Delete non-existent snippet
        assert manager.delete_snippet("non-existent") is False

    def test_get_all_snippets(self, manager):
        """Test getting all snippets."""
        # Add multiple snippets
        snippet1 = manager.add_snippet(name="Test1", content="Content1")
        snippet2 = manager.add_snippet(name="Test2", content="Content2")
        snippet3 = manager.add_snippet(name="Test3", content="Content3")

        all_snippets = manager.get_all_snippets()
        assert len(all_snippets) == 3
        assert snippet1 in all_snippets
        assert snippet2 in all_snippets
        assert snippet3 in all_snippets

    def test_get_snippets_by_category(self, manager):
        """Test getting snippets by category."""
        # Add snippets in different categories
        manager.add_snippet(name="Email1", content="Content", category="email")
        manager.add_snippet(name="Email2", content="Content", category="email")
        manager.add_snippet(name="Code1", content="Content", category="code")

        email_snippets = manager.get_snippets_by_category("email")
        assert len(email_snippets) == 2
        assert all(s.category == "email" for s in email_snippets)

        code_snippets = manager.get_snippets_by_category("code")
        assert len(code_snippets) == 1
        assert code_snippets[0].category == "code"

    def test_search_snippets(self, manager):
        """Test searching snippets."""
        # Add test snippets
        manager.add_snippet(name="Python Function", content="def hello():", tags=["python", "code"])
        manager.add_snippet(name="Email Signature", content="Best regards", tags=["email"])
        manager.add_snippet(name="SQL Query", content="SELECT * FROM", tags=["sql", "code"])

        # Search by name
        results = manager.search_snippets("python")
        assert len(results) == 1
        assert results[0].name == "Python Function"

        # Search by content
        results = manager.search_snippets("SELECT")
        assert len(results) == 1
        assert results[0].name == "SQL Query"

        # Search by tag
        results = manager.search_snippets("code")
        assert len(results) == 2

        # Case insensitive search
        results = manager.search_snippets("EMAIL")
        assert len(results) == 1

    def test_get_snippets_by_hotkey(self, manager):
        """Test getting snippet by hotkey."""
        snippet = manager.add_snippet(name="Test", content="Content", hotkey="ctrl+shift+t")

        found = manager.get_snippet_by_hotkey("ctrl+shift+t")
        assert found == snippet

        # Non-existent hotkey
        assert manager.get_snippet_by_hotkey("ctrl+x") is None

    def test_save_and_load(self, manager, temp_snippets_file):
        """Test saving and loading snippets."""
        # Add snippets
        snippet1 = manager.add_snippet(name="Test1", content="Content1")
        snippet2 = manager.add_snippet(name="Test2", content="Content2", tags=["tag"])

        # Save
        manager.save()
        assert temp_snippets_file.exists()

        # Create new manager and load
        new_manager = SnippetManager(snippets_path=temp_snippets_file)
        new_manager.load()

        # Verify snippets loaded
        assert len(new_manager.snippets) == 2
        loaded1 = new_manager.get_snippet(snippet1.id)
        assert loaded1.name == "Test1"
        assert loaded1.content == "Content1"

        loaded2 = new_manager.get_snippet(snippet2.id)
        assert loaded2.tags == ["tag"]

    def test_import_export(self, manager, tmp_path):
        """Test importing and exporting snippets."""
        # Add snippets
        manager.add_snippet(name="Test1", content="Content1")
        manager.add_snippet(name="Test2", content="Content2")

        # Export
        export_file = tmp_path / "export.json"
        manager.export_snippets(export_file)

        # Clear and import
        manager.snippets.clear()
        imported_count = manager.import_snippets(export_file)

        assert imported_count == 2
        assert len(manager.snippets) == 2

    def test_import_with_duplicates(self, manager, tmp_path):
        """Test importing with duplicate handling."""
        # Add initial snippet
        snippet = manager.add_snippet(name="Test", content="Original")

        # Export
        export_file = tmp_path / "export.json"
        manager.export_snippets(export_file)

        # Modify snippet
        manager.update_snippet(snippet.id, content="Modified")

        # Import with merge
        imported = manager.import_snippets(export_file, merge=True)
        assert imported == 1
        # Original should be preserved
        assert manager.get_snippet(snippet.id).content == "Modified"

        # Import with overwrite
        imported = manager.import_snippets(export_file, merge=False)
        assert imported == 1
        # Should be overwritten
        assert manager.get_snippet(snippet.id).content == "Original"

    def test_get_recent_snippets(self, manager):
        """Test getting recently used snippets."""
        # Add snippets and use them
        snippet1 = manager.add_snippet(name="Test1", content="Content1")
        manager.add_snippet(name="Test2", content="Content2")
        snippet3 = manager.add_snippet(name="Test3", content="Content3")

        # Use snippets
        manager.use_snippet(snippet3.id)
        manager.use_snippet(snippet1.id)
        manager.use_snippet(snippet3.id)  # Use again

        recent = manager.get_recent_snippets(limit=2)
        assert len(recent) == 2
        assert recent[0].id == snippet3.id  # Most used
        assert recent[1].id == snippet1.id

    def test_use_snippet(self, manager):
        """Test using a snippet increments count."""
        snippet = manager.add_snippet(name="Test", content="Content")
        assert snippet.use_count == 0

        manager.use_snippet(snippet.id)
        assert manager.get_snippet(snippet.id).use_count == 1

        manager.use_snippet(snippet.id)
        assert manager.get_snippet(snippet.id).use_count == 2

    def test_get_categories(self, manager):
        """Test getting all categories."""
        manager.add_snippet(name="Test1", content="C1", category="email")
        manager.add_snippet(name="Test2", content="C2", category="code")
        manager.add_snippet(name="Test3", content="C3", category="email")
        manager.add_snippet(name="Test4", content="C4", category="signatures")

        categories = manager.get_categories()
        assert len(categories) == 3
        assert "email" in categories
        assert "code" in categories
        assert "signatures" in categories

    def test_validate_hotkey_uniqueness(self, manager):
        """Test hotkey uniqueness validation."""
        # Add snippet with hotkey
        manager.add_snippet(name="Test1", content="Content", hotkey="ctrl+shift+1")

        # Try to add another with same hotkey
        with pytest.raises(ValueError, match="Hotkey .* is already in use"):
            manager.add_snippet(name="Test2", content="Content", hotkey="ctrl+shift+1")

        # Updating to existing hotkey should also fail
        snippet2 = manager.add_snippet(name="Test2", content="Content")
        with pytest.raises(ValueError, match="Hotkey .* is already in use"):
            manager.update_snippet(snippet2.id, hotkey="ctrl+shift+1")

    def test_bulk_operations(self, manager):
        """Test bulk operations on snippets."""
        # Add multiple snippets
        ids = []
        for i in range(5):
            snippet = manager.add_snippet(name=f"Test{i}", content=f"Content{i}", category="bulk")
            ids.append(snippet.id)

        # Bulk delete
        deleted = manager.bulk_delete(ids[:3])
        assert deleted == 3
        assert len(manager.snippets) == 2

        # Bulk update category
        updated = manager.bulk_update_category(ids[3:], "updated")
        assert updated == 2
        for id in ids[3:]:
            assert manager.get_snippet(id).category == "updated"

    def test_snippet_templates(self, manager):
        """Test creating snippets from templates."""
        # Create template
        template = manager.create_snippet_template(
            name="Email Template",
            content="Dear {name},\n\n{body}\n\nBest regards,\n{sender}",
            category="templates",
        )

        # Create snippet from template
        snippet = manager.create_from_template(
            template.id,
            name="Welcome Email",
            variables={"name": "John", "body": "Welcome!", "sender": "Admin"},
        )

        assert snippet.name == "Welcome Email"
        assert "Dear John," in snippet.content
        assert "Welcome!" in snippet.content
        assert "Admin" in snippet.content
