"""Document chat route -- ask questions about uploaded documents with tool calling."""

from __future__ import annotations

import html
import os
from pathlib import Path

from flask import Blueprint, make_response, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

from ..app import limiter
from ..chat_handler import ChatSession, DocumentContext, ToolRegistry
from ..gating import ai_gate, GatingError
from ..upload import get_temp_dir, UploadError

chat_bp = Blueprint("chat", __name__)

_MAX_QUESTION_LENGTH = 2000
_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _ollama_available() -> bool:
    """Return True if Ollama is reachable and llama3 is loaded."""
    import requests as _req
    try:
        r = _req.get(f"{_OLLAMA_HOST}/api/tags", timeout=3)
        if not r.ok:
            return False
        models = [m.get("name", "") for m in r.json().get("models", [])]
        return any("llama3" in m for m in models)
    except Exception:
        return False


def _load_document_text(token: str) -> str:
    """Extract text from uploaded document."""
    try:
        temp_dir = get_temp_dir(token)
        saved_files = list(temp_dir.glob("*"))
        if not saved_files:
            raise UploadError("Upload not found.")
        
        saved_path = saved_files[0]
        ext = saved_path.suffix.lower()

        # Simple text extraction
        if ext == ".md":
            return saved_path.read_text(encoding="utf-8")
        elif ext in {".txt", ".rst"}:
            return saved_path.read_text(encoding="utf-8")
        else:
            # For Word, PDF, etc., use MarkItDown
            try:
                from markitdown import MarkItDown
                md = MarkItDown()
                result = md.convert(str(saved_path))
                return result.text_content or ""
            except Exception as e:
                return f"[Error extracting text: {e}]"

    except UploadError:
        raise
    except Exception as e:
        raise UploadError(f"Error loading document: {e}") from e


def _call_ollama_with_tools(
    question: str,
    document_text: str,
    tools_registry: ToolRegistry,
    conversation_context: str = "",
) -> tuple[str, list[dict]]:
    """Call Llama 3 with tool calling for Q&A.
    
    Returns:
        (answer, tool_calls_made)
    """
    import json
    import requests

    # Build tool definitions for Llama
    tools_json = json.dumps(tools_registry.get_all_tools())

    # System prompt with tool calling instructions
    system_prompt = f"""You are GLOW (Guided Layout & Output Workflow), an accessibility-focused document assistant. \
You have access to 24 tools organized into five categories:

DOCUMENT tools — extract tables, find sections, search text, list headings, get stats, summarize sections
COMPLIANCE AGENT tools — run_accessibility_audit, get_compliance_score, get_critical_findings, get_auto_fixable_findings
STRUCTURE AGENT tools — check_heading_hierarchy, find_faux_headings, check_list_structure, estimate_reading_order
CONTENT AGENT tools — check_emphasis_patterns, check_link_text, check_reading_level, check_alignment_hints
REMEDIATION AGENT tools — explain_rule, suggest_fix, prioritize_findings, estimate_fix_impact, check_image_alt_text

Full tool definitions:
{tools_json}

When the user asks a question:
1. Identify which agent category best applies
2. Call the most relevant tool(s) with correct parameters — use [TOOL: tool_name(param)] syntax
3. Ground your answer in the tool results; do not guess document content
4. Lead with the most important finding; be concise and actionable
5. Cite the ACB rule ID (e.g. ACB-NO-ITALIC) when relevant

Compliance questions → Compliance Agent tools first
Structure questions → Structure Agent tools first
Emphasis/link/reading-level questions → Content Agent tools first
"How do I fix X" or "explain rule" → Remediation Agent tools first
General document questions → Document tools"""

    # Build conversation
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    if conversation_context:
        messages.append({"role": "user", "content": f"Context from previous turns:\n{conversation_context}"})
    
    messages.append({"role": "user", "content": f"Document text (first 5000 chars):\n{document_text[:5000]}\n\nQuestion: {question}"})

    # Call Ollama
    try:
        response = requests.post(
            f"{_OLLAMA_HOST}/api/generate",
            json={
                "model": "llama3",
                "prompt": question,
                "system": system_prompt,
                "stream": False,
                "temperature": 0.3,
            },
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        answer = result.get("response", "")

        # Parse tool calls from response (basic parsing)
        tool_calls = []
        # Look for patterns like [TOOL: extract_table(table_name)]
        if "[TOOL:" in answer:
            # Extract tool calls
            import re
            matches = re.findall(r'\[TOOL: (\w+)\((.*?)\)\]', answer)
            for tool_name, params_str in matches:
                tool_calls.append({
                    "name": tool_name,
                    "params": params_str,
                })
                # Execute tool and get result
                result_text = tools_registry.call(tool_name, **{"param": params_str})
                answer = answer.replace(f"[TOOL: {tool_name}({params_str})]", f"[Tool result: {result_text[:200]}...]")

        return answer, tool_calls

    except Exception as e:
        return f"Error querying LLM: {e}", []


@chat_bp.route("/", methods=["GET"])
def chat_form():
    """Show the chat form."""
    token = request.args.get("token")
    if not token:
        return redirect(url_for("process.process_form"))

    try:
        # Load or create chat session
        session_key = f"chat_{token}"
        chat_data = session.get(session_key)
        
        if chat_data:
            chat_session = ChatSession.from_dict(chat_data)
        else:
            # Load document and create new session
            try:
                doc_text = _load_document_text(token)
                temp_dir = get_temp_dir(token)
                saved_files = list(temp_dir.glob("*"))
                filename = saved_files[0].name if saved_files else "document"
                
                chat_session = ChatSession(token, filename)
                session[session_key] = chat_session.to_dict()
            except UploadError as e:
                return render_template("chat_form.html", error=str(e), token=token)

        return render_template(
            "chat_form.html",
            token=token,
            filename=chat_session.filename,
            conversation=chat_session.turns,
            ollama_available=_ollama_available(),
        )

    except Exception as e:
        return render_template("chat_form.html", error=str(e), token=token), 500


@chat_bp.route("/", methods=["POST"])
@limiter.limit("10 per minute")
def chat_submit():
    """Process a user question and return answer."""
    token = request.form.get("token")
    question = request.form.get("question", "").strip()

    if not token or not question:
        return redirect(url_for("chat.chat_form", token=token))

    if len(question) > _MAX_QUESTION_LENGTH:
        return render_template(
            "chat_form.html",
            error=f"Question is too long. Please keep it under {_MAX_QUESTION_LENGTH} characters.",
            token=token,
        ), 400

    try:
        # Load chat session from session storage
        session_key = f"chat_{token}"
        chat_data = session.get(session_key)
        
        if not chat_data:
            return redirect(url_for("chat.chat_form", token=token))

        chat_session = ChatSession.from_dict(chat_data)

        # Load document
        doc_text = _load_document_text(token)
        context = DocumentContext(doc_text, chat_session.filename)
        tools = ToolRegistry(context)

        # Add turn and call AI with gating
        turn = chat_session.add_turn(question)

        try:
            with ai_gate():
                answer, tool_calls = _call_ollama_with_tools(
                    question,
                    doc_text,
                    tools,
                    conversation_context="\n".join(
                        f"Q: {t.question}\nA: {t.answer}" for t in chat_session.turns[:-1]
                    ),
                )
        except GatingError:
            resp = make_response(
                render_template(
                    "busy.html",
                    operation="Document chat (AI interrogation)",
                    retry_seconds=90,
                    back_url=url_for("chat.chat_form", token=token),
                ),
                503,
            )
            from ..gating import RETRY_AFTER_SECONDS
            resp.headers["Retry-After"] = str(RETRY_AFTER_SECONDS)
            return resp

        turn.answer = answer
        turn.tool_calls = tool_calls

        # Save updated session
        session[session_key] = chat_session.to_dict()
        session.modified = True

        return redirect(url_for("chat.chat_form", token=token))

    except UploadError as e:
        return render_template("chat_form.html", error=str(e), token=token), 400
    except Exception:
        return render_template("chat_form.html", error="An unexpected error occurred. Please try again.", token=token), 500


@chat_bp.route("/export/<format>", methods=["GET"])
def chat_export(format: str):
    """Export conversation."""
    token = request.args.get("token")
    
    if not token:
        return redirect(url_for("process.process_form"))

    try:
        session_key = f"chat_{token}"
        chat_data = session.get(session_key)
        
        if not chat_data:
            return redirect(url_for("chat.chat_form", token=token))

        chat_session = ChatSession.from_dict(chat_data)

        # Sanitize filename for use in Content-Disposition header
        safe_stem = secure_filename(chat_session.filename) or "document"

        if format == "markdown":
            md_content = chat_session.export_markdown()
            return (
                md_content,
                200,
                {
                    "Content-Type": "text/markdown; charset=utf-8",
                    "Content-Disposition": f'attachment; filename="{safe_stem}_chat.md"',
                },
            )

        elif format == "word":
            from tempfile import NamedTemporaryFile
            temp = NamedTemporaryFile(suffix=".docx", delete=False)
            temp_path = Path(temp.name)
            temp.close()

            chat_session.export_word(temp_path)

            with open(temp_path, "rb") as f:
                docx_data = f.read()

            temp_path.unlink()

            return (
                docx_data,
                200,
                {
                    "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "Content-Disposition": f'attachment; filename="{safe_stem}_chat.docx"',
                },
            )

        elif format == "pdf":
            from tempfile import NamedTemporaryFile
            temp = NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_path = Path(temp.name)
            temp.close()

            chat_session.export_pdf(temp_path)

            if temp_path.exists():
                with open(temp_path, "rb") as f:
                    pdf_data = f.read()
                temp_path.unlink()

                return (
                    pdf_data,
                    200,
                    {
                        "Content-Type": "application/pdf",
                        "Content-Disposition": f'attachment; filename="{safe_stem}_chat.pdf"',
                    },
                )
            else:
                return render_template(
                    "error.html",
                    title="Export Failed",
                    message="PDF generation failed. Please try Markdown or Word export instead.",
                ), 500

        else:
            return render_template(
                "error.html",
                title="Unknown Export Format",
                message="The requested export format is not supported.",
            ), 400

    except Exception:
        return render_template(
            "error.html",
            title="Export Error",
            message="An error occurred while exporting the conversation. Please try again.",
        ), 500


@chat_bp.route("/clear", methods=["POST"])
def chat_clear():
    """Clear the conversation."""
    token = request.form.get("token")
    
    if token:
        session_key = f"chat_{token}"
        session.pop(session_key, None)
        session.modified = True

    return redirect(url_for("chat.chat_form", token=token))
