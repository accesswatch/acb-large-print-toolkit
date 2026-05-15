"""
GLOW MCP Server - FastAPI entrypoint

This server exposes GLOW's accessibility audit, fix, convert, and reporting features via a Model Context Protocol (MCP) API for integration with Accessibility Agents and other tools.

Endpoints:
- /health: Health check
- /audit: Audit a document (Markdown, HTML, DOCX)
- /fix: Auto-fix accessibility issues
- /convert: Convert between formats (Markdown, HTML, DOCX)
- /report: Generate accessibility reports

See README.md and openapi.yaml for full documentation.
"""


from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
from pathlib import Path
try:
    from .glow_mcp_utils import run_audit, run_report
except ImportError:  # Support direct module execution in tests.
    from glow_mcp_utils import run_audit, run_report

app = FastAPI(title="GLOW MCP Server", description="Accessibility audit/fix/convert/report API for agent integration.", version="7.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/audit")
async def audit(file: UploadFile = File(...), format: str = Form(...)):
    """Audit a document for accessibility issues."""
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)
    try:
        audit_result = run_audit(tmp_path, format)
        report_json = run_report(audit_result, report_type="json")
        return JSONResponse(content=report_json)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/fix")
async def fix(file: UploadFile = File(...), format: str = Form(...)):
    """Auto-fix accessibility issues in a document."""
    try:
        from .glow_mcp_utils import run_fix
    except ImportError:
        from glow_mcp_utils import run_fix
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)
    try:
        fixed_path, total_fixes, fix_records, post_fix_audit, warnings = run_fix(tmp_path, format)
        return JSONResponse({
            "fixed_file": str(fixed_path),
            "total_fixes": total_fixes,
            "fix_records": [r.__dict__ for r in fix_records],
            "post_fix_audit": post_fix_audit.__dict__,
            "warnings": warnings
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/convert")
async def convert(file: UploadFile = File(...), from_format: str = Form(...), to_format: str = Form(...)):
    """Convert a document between supported formats."""
    try:
        from .glow_mcp_utils import run_convert
    except ImportError:
        from glow_mcp_utils import run_convert
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)
    try:
        output_path, converted_text = run_convert(tmp_path, from_format, to_format)
        return JSONResponse({
            "output_file": str(output_path),
            "converted_text": converted_text
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/report")
async def report(file: UploadFile = File(...), format: str = Form(...), report_type: str = Form("json")):
    """Generate a detailed accessibility report."""
    try:
        from .glow_mcp_utils import run_audit, run_report
    except ImportError:
        from glow_mcp_utils import run_audit, run_report
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)
    try:
        audit_result = run_audit(tmp_path, format)
        report = run_report(audit_result, report_type=report_type)
        return JSONResponse({"report": report})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        tmp_path.unlink(missing_ok=True)
