"""Tests for document chat/interrogation feature."""

from __future__ import annotations

import json
import pytest

from acb_large_print_web.chat_handler import (
    DocumentContext,
    ToolRegistry,
    ChatSession,
    ConversationTurn,
)


class TestDocumentContext:
    """Test document context extraction."""

    def test_extract_headings(self):
        """Headings are properly extracted."""
        text = """# Title
        
## Section 1
Some text here.

### Subsection 1.1
More text."""
        context = DocumentContext(text, "test.md")
        assert len(context.headings) == 3
        assert context.headings[0]["text"] == "Title"
        assert context.headings[0]["level"] == 1

    def test_compute_stats(self):
        """Document stats are computed correctly."""
        text = "This is a test document. " * 50  # ~300 words
        context = DocumentContext(text, "test.md")
        assert context.stats["words"] > 200
        assert context.stats["filename"] == "test.md"
        assert context.stats["reading_time_minutes"] >= 1

    def test_extract_tables(self):
        """Markdown tables are extracted."""
        text = """| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |"""
        context = DocumentContext(text, "test.md")
        assert len(context.tables) == 1


class TestToolRegistry:
    """Test tool calling registry."""

    @pytest.fixture
    def context(self):
        """Sample document context."""
        text = """# Main Title

## Section A
Content for section A goes here.

## Section B
This is section B content.

| Product | Price |
| --- | --- |
| Item 1 | $10 |
| Item 2 | $20 |
"""
        return DocumentContext(text, "sample.md")

    @pytest.fixture
    def tools(self, context):
        """Tool registry instance."""
        return ToolRegistry(context)

    def test_list_headings(self, tools):
        """Tool can list all headings."""
        result = tools.list_headings()
        assert "Main Title" in result
        assert "Section A" in result
        assert "Section B" in result

    def test_find_section(self, tools):
        """Tool can find a section by name."""
        result = tools.find_section("Section A")
        assert "Section A" in result
        assert "Content for section A" in result

    def test_search_text(self, tools):
        """Tool can search for keywords."""
        result = tools.search_text("Price")
        assert "Price" in result

    def test_search_not_found(self, tools):
        """Tool returns message when search fails."""
        result = tools.search_text("nonexistent_keyword_xyz")
        assert "not found" in result.lower() or "no match" in result.lower()

    def test_get_document_stats(self, tools):
        """Tool returns document stats."""
        result = tools.get_document_stats()
        assert "sample.md" in result
        assert "Words:" in result
        assert "Headings:" in result

    def test_extract_table(self, tools):
        """Tool can extract a table."""
        result = tools.extract_table("0")
        assert "Product" in result
        assert "Price" in result


class TestConversationTurn:
    """Test conversation turn management."""

    def test_create_turn(self):
        """Can create a new turn."""
        turn = ConversationTurn(1, "What is the main topic?")
        assert turn.turn_number == 1
        assert turn.question == "What is the main topic?"
        assert turn.answer is None

    def test_turn_to_dict(self):
        """Turn can be serialized."""
        turn = ConversationTurn(1, "Question?")
        turn.answer = "Answer!"
        turn.tool_calls = [{"name": "search_text", "params": "keyword"}]
        
        data = turn.to_dict()
        assert data["turn_number"] == 1
        assert data["question"] == "Question?"
        assert data["answer"] == "Answer!"
        assert len(data["tool_calls"]) == 1

    def test_turn_from_dict(self):
        """Turn can be deserialized."""
        original = {
            "turn_number": 1,
            "question": "Question?",
            "answer": "Answer!",
            "tool_calls": [{"name": "search", "params": "x"}],
            "tool_results": {},
        }
        turn = ConversationTurn.from_dict(original)
        assert turn.turn_number == 1
        assert turn.question == "Question?"


class TestChatSession:
    """Test chat session management."""

    def test_create_session(self):
        """Can create a chat session."""
        session = ChatSession("token123", "document.md")
        assert session.token == "token123"
        assert session.filename == "document.md"
        assert len(session.turns) == 0

    def test_add_turn(self):
        """Can add turns to session."""
        session = ChatSession("token123", "doc.md")
        turn1 = session.add_turn("First question?")
        turn2 = session.add_turn("Second question?")
        
        assert len(session.turns) == 2
        assert turn1.turn_number == 1
        assert turn2.turn_number == 2

    def test_session_to_dict(self):
        """Session can be serialized."""
        session = ChatSession("token123", "doc.md")
        turn = session.add_turn("Question?")
        turn.answer = "Answer!"
        
        data = session.to_dict()
        assert data["token"] == "token123"
        assert data["filename"] == "doc.md"
        assert len(data["turns"]) == 1

    def test_session_from_dict(self):
        """Session can be deserialized."""
        original = {
            "token": "token123",
            "filename": "doc.md",
            "created_at": "2026-04-17T12:00:00",
            "turns": [
                {
                    "turn_number": 1,
                    "question": "Q?",
                    "answer": "A!",
                    "tool_calls": [],
                    "tool_results": {},
                }
            ],
        }
        session = ChatSession.from_dict(original)
        assert session.token == "token123"
        assert len(session.turns) == 1

    def test_export_markdown(self):
        """Session exports to markdown."""
        session = ChatSession("token123", "doc.md")
        turn = session.add_turn("What is the topic?")
        turn.answer = "The topic is accessibility."
        
        markdown = session.export_markdown()
        assert "# Chat Session" in markdown
        assert "doc.md" in markdown
        assert "Turn 1" in markdown
        assert "What is the topic?" in markdown
        assert "accessibility" in markdown




class TestChatRoutes:
    """Integration tests for chat routes (requires Flask context).
    
    Note: Route tests are covered by smoke tests in test_app.py.
    Unit tests above verify the core chat_handler module independently.
    """

    pass

