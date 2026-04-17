"""Agentic Q&A handler with tool calling for document interrogation.

Users ask questions about uploaded documents. Llama 3 decides which tools to use
(extract table, search, summarize, etc.) based on the question. Conversation
history is stored in session and can be exported as Markdown or Word.

Tool calling flow:
  1. User asks question
  2. Llama decides which tools to invoke (or answer directly)
  3. Tools execute (extract text, search, etc.)
  4. Llama uses tool results to form final answer
  5. Answer + tool calls are added to conversation history
  6. History can be exported as Markdown, Word, or PDF
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class DocumentContext:
    """Holds extracted document content and metadata for Q&A."""

    def __init__(self, text: str, filename: str, doc_type: str = "text") -> None:
        """Initialize document context.

        Args:
            text: Full extracted text from document.
            filename: Original filename.
            doc_type: "text" (Word/PDF/Markdown), "image" (scanned), or "mixed".
        """
        self.text = text
        self.filename = filename
        self.doc_type = doc_type
        self.headings = self._extract_headings()
        self.tables = self._extract_tables()
        self.stats = self._compute_stats()

    def _extract_headings(self) -> list[dict[str, Any]]:
        """Extract heading hierarchy and positions from text."""
        headings = []
        lines = self.text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# "):
                headings.append({"level": 1, "text": line[2:].strip(), "line": i})
            elif line.startswith("## "):
                headings.append({"level": 2, "text": line[3:].strip(), "line": i})
            elif line.startswith("### "):
                headings.append({"level": 3, "text": line[4:].strip(), "line": i})
            elif line.startswith("#### "):
                headings.append({"level": 4, "text": line[5:].strip(), "line": i})
        return headings

    def _extract_tables(self) -> list[dict[str, Any]]:
        """Extract simple table-like structures (pipe-delimited markdown tables)."""
        tables = []
        lines = self.text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if "|" in line and i + 1 < len(lines) and "|" in lines[i + 1]:
                # Likely a markdown table
                table_lines = [line]
                i += 1
                table_lines.append(lines[i])  # header separator
                i += 1
                while i < len(lines) and "|" in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                tables.append({"lines": table_lines, "start": len(tables)})
            else:
                i += 1
        return tables

    def _compute_stats(self) -> dict[str, Any]:
        """Compute document statistics."""
        words = len(self.text.split())
        lines = len(self.text.split("\n"))
        chars = len(self.text)
        reading_time_minutes = max(1, words // 200)  # ~200 wpm
        return {
            "words": words,
            "lines": lines,
            "characters": chars,
            "reading_time_minutes": reading_time_minutes,
            "filename": self.filename,
        }


class ToolRegistry:
    """Registry of callable tools for the agent."""

    def __init__(self, context: DocumentContext) -> None:
        self.context = context

    def extract_table(self, table_name: str) -> str:
        """Extract a specific table by name or index."""
        try:
            idx = int(table_name)
            if 0 <= idx < len(self.context.tables):
                return "\n".join(self.context.tables[idx]["lines"])
        except (ValueError, IndexError):
            pass
        return f"Table '{table_name}' not found. Available tables: {len(self.context.tables)}"

    def find_section(self, section_name: str) -> str:
        """Find and return a section by heading name."""
        for heading in self.context.headings:
            if section_name.lower() in heading["text"].lower():
                # Find text until next heading
                lines = self.context.text.split("\n")
                start = heading["line"]
                end = len(lines)
                for h in self.context.headings:
                    if h["line"] > start:
                        end = h["line"]
                        break
                return "\n".join(lines[start:end]).strip()
        return f"Section '{section_name}' not found."

    def search_text(self, keyword: str) -> str:
        """Search for keyword in document and return context."""
        if not keyword:
            return "No keyword provided."
        matches = []
        lines = self.context.text.split("\n")
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                matches.append(f"Line {i + 1}: {line}")
        if not matches:
            return f"No matches found for '{keyword}'."
        return "\n".join(matches[:10])  # Return first 10 matches

    def get_document_stats(self) -> str:
        """Return document statistics."""
        stats = self.context.stats
        return (
            f"Document: {stats['filename']}\n"
            f"Words: {stats['words']}\n"
            f"Lines: {stats['lines']}\n"
            f"Characters: {stats['characters']}\n"
            f"Reading time: ~{stats['reading_time_minutes']} minutes\n"
            f"Headings: {len(self.context.headings)}\n"
            f"Tables: {len(self.context.tables)}"
        )

    def summarize_section(self, section_name: str) -> str:
        """Summarize a section (via find_section + message to Llama)."""
        section_text = self.find_section(section_name)
        if "not found" in section_text:
            return section_text
        # Summaries are done by Llama, this just returns the section
        return f"Section '{section_name}':\n\n{section_text[:500]}..."

    def list_headings(self) -> str:
        """List all headings in the document."""
        if not self.context.headings:
            return "No headings found."
        headings_list = []
        for h in self.context.headings:
            indent = "  " * (h["level"] - 1)
            headings_list.append(f"{indent}• {h['text']}")
        return "\n".join(headings_list)

    def get_images(self) -> str:
        """Return list of images (stub for scanned PDFs via Llava)."""
        return (
            "Image extraction requires Llava vision model. "
            "Images are automatically analyzed during scanned PDF processing."
        )

    def get_all_tools(self) -> dict[str, dict[str, Any]]:
        """Return tool definitions for Llama tool calling."""
        return {
            "extract_table": {
                "description": "Extract a specific table by name or index number",
                "parameters": {"table_name": "str (name or 0-indexed number)"},
            },
            "find_section": {
                "description": "Find and return a section by heading name or keyword",
                "parameters": {"section_name": "str (heading name or keyword)"},
            },
            "search_text": {
                "description": "Search for keyword and return matching lines",
                "parameters": {"keyword": "str"},
            },
            "get_document_stats": {
                "description": "Get document statistics (word count, line count, headings, etc.)",
                "parameters": {},
            },
            "summarize_section": {
                "description": "Get a section summary (uses find_section + Llama reasoning)",
                "parameters": {"section_name": "str"},
            },
            "list_headings": {
                "description": "List all headings in the document with hierarchy",
                "parameters": {},
            },
            "get_images": {
                "description": "Get list of images in the document (scanned PDFs only)",
                "parameters": {},
            },
        }

    def call(self, tool_name: str, **kwargs: Any) -> str:
        """Call a tool by name and return result."""
        if tool_name == "extract_table":
            return self.extract_table(kwargs.get("table_name", ""))
        elif tool_name == "find_section":
            return self.find_section(kwargs.get("section_name", ""))
        elif tool_name == "search_text":
            return self.search_text(kwargs.get("keyword", ""))
        elif tool_name == "get_document_stats":
            return self.get_document_stats()
        elif tool_name == "summarize_section":
            return self.summarize_section(kwargs.get("section_name", ""))
        elif tool_name == "list_headings":
            return self.list_headings()
        elif tool_name == "get_images":
            return self.get_images()
        else:
            return f"Unknown tool: {tool_name}"


class ConversationTurn:
    """A single Q&A turn with optional tool calls."""

    def __init__(self, turn_number: int, question: str) -> None:
        self.turn_number = turn_number
        self.question = question
        self.answer: str | None = None
        self.tool_calls: list[dict[str, Any]] = []
        self.tool_results: dict[str, str] = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for session storage."""
        return {
            "turn_number": self.turn_number,
            "question": self.question,
            "answer": self.answer,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ConversationTurn:
        """Create from dictionary (session load)."""
        turn = ConversationTurn(data["turn_number"], data["question"])
        turn.answer = data.get("answer")
        turn.tool_calls = data.get("tool_calls", [])
        turn.tool_results = data.get("tool_results", {})
        return turn


class ChatSession:
    """Manages conversation history for a document."""

    def __init__(self, token: str, filename: str) -> None:
        self.token = token
        self.filename = filename
        self.turns: list[ConversationTurn] = []
        self.created_at = datetime.now(UTC)

    def add_turn(self, question: str) -> ConversationTurn:
        """Add a new Q&A turn."""
        turn_number = len(self.turns) + 1
        turn = ConversationTurn(turn_number, question)
        self.turns.append(turn)
        return turn

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for session storage."""
        return {
            "token": self.token,
            "filename": self.filename,
            "created_at": self.created_at.isoformat(),
            "turns": [turn.to_dict() for turn in self.turns],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ChatSession:
        """Create from dictionary (session load)."""
        session = ChatSession(data["token"], data["filename"])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.turns = [ConversationTurn.from_dict(t) for t in data.get("turns", [])]
        return session

    def export_markdown(self) -> str:
        """Export conversation to Markdown."""
        lines = [
            f"# Chat Session: {self.filename}",
            f"*Created: {self.created_at.isoformat()}*\n",
        ]
        for turn in self.turns:
            lines.append(f"## Turn {turn.turn_number}: {turn.question}\n")
            if turn.tool_calls:
                lines.append("**Tools used:**")
                for call in turn.tool_calls:
                    lines.append(f"- {call.get('name', 'unknown')}")
                lines.append("")
            if turn.answer:
                lines.append(turn.answer)
            lines.append("")
        return "\n".join(lines)

    def export_word(self, output_path: Path) -> None:
        """Export conversation to Word document."""
        from docx import Document
        from docx.shared import Pt, RGBColor

        doc = Document()
        doc.add_heading(f"Chat Session: {self.filename}", 0)
        doc.add_paragraph(f"Created: {self.created_at.isoformat()}").runs[0].italic = True

        for turn in self.turns:
            doc.add_heading(f"Turn {turn.turn_number}", level=2)
            doc.add_paragraph(turn.question).runs[0].bold = True

            if turn.tool_calls:
                p = doc.add_paragraph("Tools used:")
                for call in turn.tool_calls:
                    doc.add_paragraph(call.get("name", "unknown"), style="List Bullet")

            if turn.answer:
                doc.add_paragraph(turn.answer)

        doc.save(str(output_path))

    def export_pdf(self, output_path: Path) -> None:
        """Export conversation to PDF via markdown + Pandoc + WeasyPrint."""
        import subprocess
        from weasyprint import HTML

        md_content = self.export_markdown()
        md_path = output_path.with_suffix(".md")
        html_path = output_path.with_suffix(".html")

        # Write markdown
        md_path.write_text(md_content, encoding="utf-8")

        # Convert markdown to HTML via Pandoc
        try:
            subprocess.run(
                ["pandoc", str(md_path), "-o", str(html_path)],
                check=True,
                capture_output=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            log.error("Pandoc conversion failed: %s", e)
            return

        # Convert HTML to PDF via WeasyPrint
        try:
            HTML(str(html_path)).write_pdf(str(output_path))
            md_path.unlink()
            html_path.unlink()
            log.info("PDF export successful: %s", output_path)
        except Exception as e:
            log.error("WeasyPrint PDF generation failed: %s", e)
