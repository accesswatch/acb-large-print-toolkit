"""Document chat route -- ask questions about uploaded documents with tool calling."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, session

from ..chat_handler import ChatSession, DocumentContext, ToolRegistry
from ..gating import ai_gate, GatingError
from ..upload import get_temp_dir, UploadError

chat_bp = Blueprint("chat", __name__)


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
    system_prompt = f"""You are a helpful document assistant. You have access to these tools:

{tools_json}

When the user asks a question:
1. Decide if you need to use any tools
2. If yes, call tools with proper parameters
3. Use the tool results to answer the question
4. Be concise and helpful

Always prioritize tool use over guessing. If a question needs information from the document, use the appropriate tool."""

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
            "http://localhost:11434/api/generate",
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
        )

    except Exception as e:
        return render_template("chat_form.html", error=str(e), token=token), 500


@chat_bp.route("/", methods=["POST"])
def chat_submit():
    """Process a user question and return answer."""
    token = request.form.get("token")
    question = request.form.get("question", "").strip()

    if not token or not question:
        return redirect(url_for("chat.chat_form", token=token))

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
        except GatingError as e:
            return render_template(
                "busy.html",
                operation="Document chat (AI interrogation)",
                retry_after=90,
            ), 503

        turn.answer = answer
        turn.tool_calls = tool_calls

        # Save updated session
        session[session_key] = chat_session.to_dict()
        session.modified = True

        return redirect(url_for("chat.chat_form", token=token))

    except UploadError as e:
        return render_template("chat_form.html", error=str(e), token=token), 400
    except Exception as e:
        return render_template("chat_form.html", error=f"Error: {e}", token=token), 500


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

        if format == "markdown":
            md_content = chat_session.export_markdown()
            return (
                md_content,
                200,
                {
                    "Content-Type": "text/markdown; charset=utf-8",
                    "Content-Disposition": f"attachment; filename={chat_session.filename}_chat.md",
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
                    "Content-Disposition": f"attachment; filename={chat_session.filename}_chat.docx",
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
                        "Content-Disposition": f"attachment; filename={chat_session.filename}_chat.pdf",
                    },
                )
            else:
                return "PDF generation failed", 500

        else:
            return "Unknown format", 400

    except Exception as e:
        return f"Export error: {e}", 500


@chat_bp.route("/clear", methods=["POST"])
def chat_clear():
    """Clear the conversation."""
    token = request.form.get("token")
    
    if token:
        session_key = f"chat_{token}"
        session.pop(session_key, None)
        session.modified = True

    return redirect(url_for("chat.chat_form", token=token))
